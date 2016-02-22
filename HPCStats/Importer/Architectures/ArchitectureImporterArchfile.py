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

"""This module contains the ArchitectureImporterArchfile class."""

import ConfigParser
import re
import os
from ClusterShell.NodeSet import NodeSet
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Importer.Architectures.ArchitectureImporter import ArchitectureImporter
from HPCStats.Model.Node import Node
from HPCStats.Model.Cluster import Cluster

class ArchitectureImporterArchfile(ArchitectureImporter):

    """This class imports architecture related data (Cluster and Nodes)
       from an ini flat file.
    """

    def __init__(self, app, db, config, cluster_name):

        super(ArchitectureImporterArchfile, self) \
          .__init__(app, db, config, cluster_name)

        archfile_section = self.cluster_name + "/archfile"

        self.archfile = config.get(archfile_section, "file")
        self.arch = None # ConfigParser object

    def check(self):
        """Checks if archfile actually exists or raises HPCStatsSourceError if
           not.
        """

        if not os.path.isfile(self.archfile):
            raise HPCStatsSourceError( \
                    "Architecture file %s does not exist" \
                      % (self.archfile))

    def update(self):
        """Create or update Cluster and Nodes in the database."""

        if not self.cluster.find(self.db):
            self.log.debug("creating cluster %s", self.cluster)
            self.cluster.save(self.db)

        # insert or update nodes
        for node in self.nodes:
            if node.find(self.db):
                self.log.debug("updating node %s", node)
                node.update(self.db)
            else:
                self.log.debug("creating node %s", node)
                node.save(self.db)

    def config_get(self, section, option, isint=False):
        """Static method to get option/section in architecture file and raise
           HPCStatsSourceError when a problem occurs.
        """

        try:
            if isint:
                return self.arch.getint(section, option)
            else:
                return self.arch.get(section, option)
        except ConfigParser.NoSectionError:
            raise HPCStatsSourceError( \
                    "missing section %s in architecture file" \
                      % (section))
        except ConfigParser.NoOptionError:
            raise HPCStatsSourceError( \
                    "missing option %s in section %s of " \
                    "architecture file" \
                      % (option, section))

    @staticmethod
    def convert_freq(freq_str):
        """Convert frequency string in parameter into float. Returns None if
           string format is not valid.
        """
        units = { "MHz": 1000**2,
                  "Mhz": 1000**2,
                  "mhz": 1000**2,
                  "GHz": 1000**3,
                  "Ghz": 1000**3,
                  "ghz": 1000**3 }
        for unit, multiplier in units.iteritems():
            match_result = re.match("^((\d+\.)?\d+)\s?" + unit + "$", freq_str)
            if match_result:
                return float(match_result.group(1)) * multiplier
        return None

    @staticmethod
    def convert_mem(mem_str):
        """Convert memory string in parameter into int. Returns None if
           string format is not valid.
        """
        units = { "MB": 1024**2,  # 1048576
                  "GB": 1024**3,  # 1073741824 
                  "TB": 1024**4 } # 1099511627776

        for unit, multiplier in units.iteritems():
            match_result = re.match("^(\d+)\s?" + unit + "$", mem_str)
            if match_result:
                return int(match_result.group(1)) * multiplier
        return None

    def read_arch(self):
        """Check if archfile actually exists then reads it and set arch
           attribute. Raises HPCStatsSourceError on error.
        """
        self.check()
        self.arch = ConfigParser.ConfigParser()
        self.arch.read(self.archfile)

    def load(self):
        """Load Cluster, Nodes and partitions from Architecture files. Raises
           HPCStatsRuntimeError or HPCStatsSourceError if error is encountered
           while loading data from sources. It sets attributes cluster, nodes
           and partitions with loaded data.
        """

        self.cluster = Cluster(self.cluster_name)
        self.nodes = []
        self.partitions = {}

        self.read_arch()
        config_get = self.config_get
        partitions = config_get(self.cluster.name, "partitions").split(',')

        for partition in partitions:

            part_sect = self.cluster.name + "/" + partition

            nodegroups = config_get(part_sect, "nodegroups").split(',')
            job_partitions = config_get(part_sect, "job_partitions") \
                               .split(',')

            nodeset_part = NodeSet() # nodeset for the partitions attribute

            for nodegroup in nodegroups:

                nodegroup_sect = self.cluster.name + "/" + partition \
                                 + "/" + nodegroup
                nodenames = config_get(nodegroup_sect, "names")
                nodeset_part.add(nodenames)

                sockets = config_get(nodegroup_sect, "sockets", isint=True)
                cores_per_socket = config_get(nodegroup_sect,
                                              "corespersocket",
                                              isint=True)
                cpu = sockets * cores_per_socket

                float_instructions = config_get(nodegroup_sect,
                                                "floatinstructions",
                                                isint=True)

                freq_str = config_get(nodegroup_sect, "frequency")
                freq = ArchitectureImporterArchfile.convert_freq(freq_str)
                if freq is None:
                    raise HPCStatsSourceError( \
                            "format of frequency for nodeset %s/%s/%s (%s) " \
                            "'%s' is not valid" \
                              % ( self.cluster.name,
                                  partition,
                                  nodegroup,
                                  nodenames,
                                  freq_str ))

                flops = sockets * cores_per_socket * float_instructions * freq

                mem_str = config_get(nodegroup_sect, "memory")
                mem = ArchitectureImporterArchfile.convert_mem(mem_str)
                if mem is None:
                    raise HPCStatsSourceError( \
                            "format of memory for nodeset %s/%s/%s (%s) " \
                            "'%s' is not valid" \
                              % ( self.cluster.name,
                                  partition,
                                  nodegroup,
                                  nodenames,
                                  mem_str ))

                model = config_get(nodegroup_sect, "model")
            
                nodeset_group = NodeSet(nodenames)
                for nodename in nodeset_group:
                    # create and append node
                    new_node = Node(name=nodename,
                                    cluster=self.cluster,
                                    model=model,
                                    partition=partition,
                                    cpu=cpu,
                                    memory=mem,
                                    flops=flops)
                    self.nodes.append(new_node)

            self.partitions[str(nodeset_part)] = job_partitions
