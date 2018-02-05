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
import sys

from HPCStats.Exceptions import HPCStatsConfigurationException

class HPCStatsConf(ConfigParser.ConfigParser, object):

    def __init__(self, filename, cluster):

        super(HPCStatsConf, self).__init__()

        self.cluster = cluster
        self.filename = filename

    def read(self):
        """Check if configuration file exists and then read it. Raises
           HPCStatsConfigurationException if configuration file does not exist.
        """

        if not os.path.exists(self.filename):
            raise HPCStatsConfigurationException(
                    "file %s does not exist" % (self.filename))

        super(HPCStatsConf, self).read(self.filename)

    def get(self, section, option, option_type=str):
        """Try to get option value in section of configuration. Raise
           HPCStatsConfigurationException if not found.
        """
        try:
            if option_type is bool:
                return super(HPCStatsConf, self).getboolean(section, option)
            if option_type is int:
                return super(HPCStatsConf, self).getint(section, option)
            else:
                return super(HPCStatsConf, self).get(section, option)
        except ConfigParser.NoSectionError:
            raise HPCStatsConfigurationException( \
                    "section %s not found" % (section))
        except ConfigParser.NoOptionError:
            raise HPCStatsConfigurationException( \
                    "option %s not found in section %s" % (option, section))

    def get_default(self, section, option, default, option_type=str):
        """Try to get option value in section of configuration. Return default
           if not found.
        """
        try:
            return self.get(section, option, option_type)
        except HPCStatsConfigurationException:
            return default

    def get_list(self, section, option):
        """Returns a comma separated multi-values parameter formatted into a
           list. If the parameter is not set, it returns an empty list."""
        items = self.get_default(section, option, '')
        return [ item.strip()
                 for item in items.split(',')
                 if item.strip() != '' ]

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
