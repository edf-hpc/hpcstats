# -*- coding: utf-8 -*-
# This file is part of HPCStats
#
# Copyright (C) 2011-2012 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
#
#Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#This program is free software; you can redistribute in and/or
#modify it under the terms of the GNU General Public License,
#version 2, as published by the Free Software Foundation.
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#On Calibre systems, the complete text of the GNU General
#Public License can be found in `/usr/share/common-licenses/GPL'.

###############################################################

import ConfigParser
import os

class HPCStatsConfig(ConfigParser.ConfigParser, object):

    def __init__(self, options):
        ConfigParser.ConfigParser.__init__(self)

        if options.config:
            files = [options.config]
        else:
            files = ['/etc/hpcstats/hpcstats.conf',
                     os.path.expanduser('~/.hpcstats.conf')]

        self.read(files)

