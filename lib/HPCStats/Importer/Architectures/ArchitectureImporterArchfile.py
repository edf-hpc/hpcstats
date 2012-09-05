#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Architectures.ArchitectureImporter import ArchitectureImporter
from HPCStats.Model.Node import Node
from HPCStats.Model.Cluster import Cluster
from ClusterShell.NodeSet import NodeSet
import ConfigParser
import re
import logging

class ArchitectureImporterArchfile(ArchitectureImporter):

    def __init__(self, db, config, cluster_name):

        ArchitectureImporter.__init__(self)

        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        archfile_section = self._cluster_name + "/archfile"

        self._archfile = config.get(archfile_section, "file")

    def update_architecture(self):

        cluster = Cluster(self._cluster_name)
        nodes = self.get_cluster_nodes()
        if cluster.exists_in_db(self._db):
            logging.debug("updating cluster %s", cluster)
            cluster.update(self._db)
        else:
            logging.debug("creating cluster %s", cluster)
            cluster.save(self._db)

        # insert or update nodes
        for node in nodes:
            if node.exists_in_db(self._db):
                logging.debug("updating node %s", node)
                node.update(self._db)
            else:
                logging.debug("creating node %s", node)
                node.save(self._db)

        
    def get_cluster_nodes(self):
        # [ivanoe]
        # nodes=nodes1,nodes2,nodes3

        nodes = []

        config = ConfigParser.ConfigParser()
        config.read(self._archfile)

        partitions_list = config.get(self._cluster_name,"partitions").split(',')

        for partition_name in partitions_list:
            partition_section_name = self._cluster_name + "/" + partition_name
            nodesets_list = config.get(partition_section_name, "nodesets").split(',')

            for nodeset_name in nodesets_list:
                nodeset_section_name = self._cluster_name + "/" + partition_name + "/" + nodeset_name
                nodenames = config.get(nodeset_section_name, "names")

                sockets = config.getint(nodeset_section_name, "sockets")
                cores_per_socket = config.getint(nodeset_section_name, "corespersocket")
                cpu = sockets * cores_per_socket

                float_instructions = config.getint(nodeset_section_name, "floatinstructions")

                frequency_str = config.get(nodeset_section_name, "frequency")
                frequency = None
                units = { "MHz": 1000**2,
                          "GHz": 1000**3 }
                for unit,multiplier in units.items():
                    match_result = re.match("^((\d+.)?\d+)" + unit + "$", frequency_str)
                    if match_result and not frequency:
                        frequency = float(match_result.group(1)) * multiplier
                if not frequency:
                    logging.error("frequency for nodeset %s/%s/%s (%s) '%s' does" \
                                  "not have a proper format : (\d+.)?\d(GHz|MHz)",
                                   self._cluster_name,
                                   partition_name,
                                   nodeset_name,
                                   nodenames,
                                   frequency_str )

                flops = sockets * cores_per_socket * float_instructions * frequency

                memory_str = config.get(nodeset_section_name, "memory")
                units = { "MB": 1024**2,  # 1048576
                          "GB": 1024**3 } # 1073741824 
                memory = None
                for unit,multiplier in units.items():
                    match_result = re.match("^(\d+)" + unit + "$", memory_str)
                    if match_result and not memory:
                        memory = int(match_result.group(1)) * multiplier
                if not memory:
                    logging.error("memory for nodeset %s/%s/%s (%s) '%s' does" \
                                  "not have a proper format : \d+(GB|MB)",
                                   self._cluster_name,
                                   partition_name,
                                   nodeset_name,
                                   nodenames,
                                   memory_str )

                model = config.get(nodeset_section_name, "model")
            
                # expand nodeset using clustershell
                nodeset = NodeSet(nodenames)
                for nodename in nodeset:
                    # create and append node
                    nodes.append( Node(name = nodename,
                                       cluster = self._cluster_name,
                                       partition = partition_name,
                                       cpu = cpu,
                                       memory = memory,
                                       model = model,
                                       flops = flops ) )

        return nodes
