#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2015 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of HPCStats.
#
# HPCStats is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with HPCStats. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

from HPCStats.Importer.Architectures.ArchitectureImporter import ArchitectureImporter
from HPCStats.Model.Node import Node
from HPCStats.Model.Cluster import Cluster
from ClusterShell.NodeSet import NodeSet
import ConfigParser
import re
import os
import logging

class ArchitectureImporterArchfile(ArchitectureImporter):

    def __init__(self, app, db, config, cluster):

        super(ArchitectureImporterArchfile, self).__init__(app, db, config, cluster)

        archfile_section = self.cluster + "/archfile"

        self._archfile = config.get(archfile_section, "file")
        if not os.path.isfile(self._archfile):
            logging.error("archfile %s does not exist", self._archfile)
            raise RuntimeError

    def update_architecture(self):

        cluster = Cluster(self.cluster)
        nodes = self.get_cluster_nodes()
        if cluster.exists_in_db(self.db):
            logging.debug("updating cluster %s", cluster)
            cluster.update(self.db)
        else:
            logging.debug("creating cluster %s", cluster)
            cluster.save(self.db)

        # insert or update nodes
        for node in nodes:
            if node.exists_in_db(self.db):
                logging.debug("updating node %s", node)
                node.update(self.db)
            else:
                logging.debug("creating node %s", node)
                node.save(self.db)

        
    def get_cluster_nodes(self):
        # [ivanoe]
        # nodes=nodes1,nodes2,nodes3

        nodes = []

        config = ConfigParser.ConfigParser()
        config.read(self._archfile)

        partitions_list = config.get(self.cluster,"partitions").split(',')

        for partition_name in partitions_list:
            partition_section_name = self.cluster + "/" + partition_name
            nodesets_list = config.get(partition_section_name, "nodesets").split(',')

            for nodeset_name in nodesets_list:
                nodeset_section_name = self.cluster + "/" + partition_name + "/" + nodeset_name
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
                                   self.cluster,
                                   partition_name,
                                   nodeset_name,
                                   nodenames,
                                   frequency_str )

                flops = sockets * cores_per_socket * float_instructions * frequency

                memory_str = config.get(nodeset_section_name, "memory")
                units = { "MB": 1024**2,  # 1048576
                          "GB": 1024**3,  # 1073741824 
                          "TB": 1024**4 } # 1099511627776
                memory = None
                for unit,multiplier in units.items():
                    match_result = re.match("^(\d+)" + unit + "$", memory_str)
                    if match_result and not memory:
                        memory = int(match_result.group(1)) * multiplier
                if not memory:
                    logging.error("memory for nodeset %s/%s/%s (%s) '%s' does" \
                                  "not have a proper format : \d+(GB|MB)",
                                   self.cluster,
                                   partition_name,
                                   nodeset_name,
                                   nodenames,
                                   memory_str )
                    memory = 0
                model = config.get(nodeset_section_name, "model")
            
                # expand nodeset using clustershell
                nodeset = NodeSet(nodenames)
                for nodename in nodeset:
                    # create and append node
                    nodes.append( Node(name = nodename,
                                       cluster = self.cluster,
                                       partition = partition_name,
                                       cpu = cpu,
                                       memory = memory,
                                       model = model,
                                       flops = flops ) )

        return nodes

    def get_partitions(self):
        """Returns a dict with nodesets as keys and the list of possible
           partitions for this nodeset as items. Ex:
           { "cn[0001-1382]": ["small","para","compute"],
             "bm[01-29]"    : ["bigmem"],
             "cg[01-24]"    : ["visu"]                    }
        """
        partitions = {}

        config = ConfigParser.ConfigParser()
        config.read(self._archfile)
        partitions_list = config.get(self.cluster,"partitions").split(',')
        for partition_name in partitions_list:
            partition_section_name = self.cluster + "/" + partition_name
            nodesets_list = config.get(partition_section_name, "nodesets").split(',')
            slurm_partitions_list = config.get(partition_section_name, "slurm_partitions").split(',')
            ns_nodeset = NodeSet()
            for nodeset_name in nodesets_list:
                nodeset_section_name = self.cluster + "/" + partition_name + "/" + nodeset_name
                str_nodenames = config.get(nodeset_section_name, "names")
                ns_nodeset.add(str_nodenames)
            partitions[str(ns_nodeset)] = slurm_partitions_list

        return partitions
