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

import ConfigParser
import os
import logging
import sys

from HPCStats.Exceptions import HPCStatsConfigurationException

class HPCStatsConf(ConfigParser.ConfigParser):

    def __init__(self, filename, cluster):

        super(HPCStatsReporter, self).__init__()

        self.cluster = cluster
        self.filename = filename
        self.read(filename)

    def get_clusters_list(self):
        """Returns the list of clusters in configuration file. If any problem
           is encountered, HPCStatsConfigurationException is raised.
        """
        try:
            cluster_list_str = self.get("clusters","clusters")
        except ConfigParser.NoSectionError:
            raise HPCStatsConfigurationException(
                    "section clusters is not present in configuration file")
        except ConfigParser.NoOptionError:
            raise HPCStatsConfigurationException(
                    "option clusters is not present in configuration file")
        return cluster_list_str.split(",")

    def check_cluster(self):
        """Check for presence of cluster in configuration file. If any problem
           is encountered, HPCStatsConfigurationException is raised.
        """

        clusters = self.get_clusters_list()
        if self.cluster not in clusters:
            raise HPCStatsConfigurationException(
                    "cluster %s is not present in configuration file" \
                      % self.cluster)
