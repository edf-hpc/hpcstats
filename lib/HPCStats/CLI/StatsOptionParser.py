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

import optparse

class StatsOptionParser(optparse.OptionParser):
    
    def __init__(self, usage, **kwargs):
        optparse.OptionParser.__init__(self, usage)

        self.disable_interspersed_args()

        self.add_option("-n", "--name", action="store", type="string", dest="clustername")
        self.add_option("-c", "--config", action="store", type="string", dest="config")
        self.add_option("-j", "--jobs", action="store_true", dest="jobs")
        self.add_option("-u", "--users", action="store_true", dest="users")
        self.add_option("-a", "--arch", action="store_true", dest="arch")
        self.add_option("-m", "--mounted", action="store_true", dest="mounted")
        self.add_option("-f", "--usage", action="store_true", dest="usage")
        self.add_option("-e", "--events", action="store_true", dest="events")
        self.add_option("-p", "--project", action="store_true", dest="context")
        self.add_option("-d", "--debug", action="store_true", dest="debug", default=False)

    def validate(self, options):
        # verify cluster arg
        if not options.clustername:
            self.error("Cluster name has to given as a parameter")
            sys.exit(1)
