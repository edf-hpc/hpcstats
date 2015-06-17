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

import argparse
from HPCStats.Exceptions import HPCStatsArgumentException

class HPCStatsArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):

        super(HPCStatsArgumentParser,self).__init__(*args, **kwargs)

    def add_args(self):

        #self.add_argument("actions",
        #                  nargs=1,
        #                  choices=['import', 'report'],
        #                  help="name of the action to perform")
        self.add_argument("-c", "--conf",
                          dest="conf",
                          default="/etc/hpcstats/hpcstats.conf",
                          help="HPCStats configuration file")

        self.add_argument("-d", "--debug",
                          help='Enable debug output',
                          action="store_true")

        subparsers = self.add_subparsers(help='sub-command help',
                                         dest='action')

        parser_imp = subparsers.add_parser('import', help='import help')

        parser_imp.add_argument("--projects",
                                dest="projects",
                                help="import projects related data " \
                                     "(projects and domains)",
                                action="store_true")

        parser_imp.add_argument("--cluster",
                                dest='cluster',
                                nargs=1,
                                required=True,
                                help="Cluster to import data from. " \
                                     "Could be one cluster name or " \
                                     "special value all for all " \
                                     "clusters at once" )

        parser_rep = subparsers.add_parser('report', help='report help')

        parser_rep.add_argument("--cluster",
                                dest='cluster',
                                nargs=1,
                                required=True,
                                help="Cluster to report data about" )

        parser_rep.add_argument("--interval",
                                dest="interval",
                                default="day",
                                help="Interval used for " \
                                     "consolidation of output " \
                                     "(default: %default)")

        parser_rep.add_argument("--template",
                                dest="template",
                                default="csv",
                                help="template to use for formatted " \
                                     "output (default: %default)")

        parser_chk = subparsers.add_parser('check', help='check help')

        parser_chk.add_argument("--cluster",
                                dest='cluster',
                                nargs=1,
                                required=True,
                                help="Cluster data sources to check" )
