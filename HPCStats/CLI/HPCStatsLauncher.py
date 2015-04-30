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

import sys
import logging
import locale

from HPCStats.CLI.HPCStatsImporter import HPCStatsImporter
from HPCStats.CLI.HPCStatsReporter import HPCStatsReporter
from HPCStats.CLI.HPCStatsArgumentParser import HPCStatsArgumentParser

class HPCStatsLauncher(object)

    """HPCStats application factory. It basically parses the arguments, set
       various global and general parameters, creates the configuration object
       and finally creates the appropriate application object.
    """

    def __init__(self, args):

        parser = HPCStatsArgumentParser('hpcstats')
        parser.add_args()
        args = parser.parse_args()

        # locale to format numbers
        # TODO: load locale output of the environment
        locale.setlocale(locale.LC_ALL, 'fr_FR')

        # enable debug mode
        logging_level = logging.INFO
        if args.debug:
            logging_level = logging.DEBUG

        logging.basicConfig(format='%(levelname)s: %(filename)s: %(message)s',
                            level=logging_level,
                            stream=sys.stdout)

        action = args.action
        conf = HPCStatsConf(args.conf, args.cluster)
        cluster_name = args.cluster

        if action == "importer":
            return HPCStatsImporter(conf, cluster_name)
        elif action == "reporter":
            template = args.template
            interval = args.interval
            return HPCStatsReporter(conf, cluster_name,
                                    template, interval)
        else:
            raise NotImplemented
