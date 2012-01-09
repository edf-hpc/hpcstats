#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.Node import Node
from HPCStats.Model.Cluster import Cluster
from ClusterShell.NodeSet import NodeSet
import ConfigParser

class ArchitectureImporterArchfile(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        archfile_section = self._cluster_name + "/archfile"

        self._archfile = config.get(archfile_section,"file")
        
    def get_cluster_nodes(self):
        # [ivanoe]
        # nodes=nodes1,nodes2,nodes3

        cluster = Cluster(self._cluster_name)
        nodes = []

        config = ConfigParser.ConfigParser()
        config.read(self._archfile)
        nodeset_names = config.get(self._cluster_name,"nodes").split(',')

        for nodeset_name in nodeset_names:
            nodeset_section = self._cluster_name + "/" + nodeset_name
            nodenames = config.get(nodeset_section, "names")
            cpu = config.getint(nodeset_section, "cpu")
            model = config.get(nodeset_section, "model")
            flops = config.getint(nodeset_section, "flops")
            
            # expand nodeset using clustershell
            nodeset = NodeSet(nodenames)
            for nodename in nodeset:
                # create and append node
                nodes.append( Node(name = nodename,
                                   cluster = self._cluster_name,
                                   cpu = cpu, 
                                   model = model,
                                   flops = flops ) )

        return (cluster, nodes)
