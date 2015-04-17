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

class HPCStatsConfig(ConfigParser.ConfigParser, object):

    def __init__(self, options):
        ConfigParser.ConfigParser.__init__(self)

        if options.config:
            files = [options.config]
        else:
            files = ['/etc/hpcstats/hpcstats.conf',
                     os.path.expanduser('~/.hpcstats.conf')]

        self.read(files)

        # check that given cluster is present in config file
        try:
            cluster_list_str = self.get("clusters","clusters")
        except ConfigParser.NoSectionError:
            logging.critical("Section clusters has to be present in configuration file")
            sys.exit(1)
        except ConfigParser.NoOptionError:
            logging.critical("Option clusters has to be present in configuration file")
            sys.exit(1)
        clusters = cluster_list_str.split(",")
        if options.clustername not in clusters:
            logging.critical("Cluster %s has to be present in configuration file",
                              options.clustername )
            sys.exit(1)
