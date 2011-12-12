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

class OptionParser(optparse.OptionParser):
    
    def __init__(self, usage, **kwargs):
        optparse.OptionParser.__init__(self, usage)

        self.disable_interspersed_args()

        self.add_option("-n", "--name", action="store", type="string", dest="clustername")
        self.add_option("-j", "--jobs", action="store_true", dest="jobs")
        self.add_option("-u", "--users", action="store_true", dest="users")


