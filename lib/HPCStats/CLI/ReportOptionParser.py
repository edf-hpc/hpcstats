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

import optparse

class ReportOptionParser(optparse.OptionParser):
    
    def __init__(self, usage, **kwargs):
        optparse.OptionParser.__init__(self, usage)

        self.disable_interspersed_args()

        self.add_option("-i", "--interval", dest="interval", default="day",
                      help="interval used for consolidation of output (default: %default)")
        self.add_option("-c", "--cluster", dest="cluster",
                      help="cluster to work on")
        self.add_option("-t", "--template", dest="template", default="csv",
                      help="template to use for formatted output (default: %default)")
        self.add_option("-d", "--debug",
                      action="store_true", dest="debug")
