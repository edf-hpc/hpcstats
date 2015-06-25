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

"""This module contains the HPCStatsLauncher class."""

import sys
import logging
import locale

from HPCStats.Exceptions import HPCStatsArgumentException, HPCStatsConfigurationException, HPCStatsDBIntegrityError, HPCStatsSourceError, HPCStatsRuntimeError
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.CLI.HPCStatsChecker import HPCStatsChecker
from HPCStats.CLI.HPCStatsImporter import HPCStatsImporter
from HPCStats.CLI.HPCStatsReporter import HPCStatsReporter
from HPCStats.CLI.HPCStatsArgumentParser import HPCStatsArgumentParser

class HPCStatsLauncher(object):

    """HPCStats application factory. It basically parses the arguments, set
       various global and general parameters, creates the configuration object
       and finally creates the appropriate application object.
    """

    def __init__(self, args):

        self.app = None

        try:
            parser = HPCStatsArgumentParser('hpcstats')
            parser.add_args()
            args = parser.parse_args()
        except HPCStatsArgumentException, err:
            logging.error("Argument Error: ", err)
            self.exit()

        # locale to format numbers
        # TODO: load locale output of the environment
        try:
            locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        except locale.Error, err:
            logging.error("Error while setting locale: %s", err)
            self.exit()

        # enable debug mode
        logging_level = logging.INFO
        if args.debug:
            logging_level = logging.DEBUG

        logging.basicConfig(format='%(levelname)s: %(filename)s: %(message)s',
                            level=logging_level,
                            stream=sys.stdout)

        action = args.action
        cluster_name = args.cluster.pop()
        conf = HPCStatsConf(args.conf, cluster_name)

        try:
            conf.read()
        except HPCStatsConfigurationException, err:
            logging.error("Configuration Error: %s", err)
            self.exit()

        if action == "check":
            self.app = HPCStatsChecker(conf, cluster_name)
        elif action == "import":
            self.app = HPCStatsImporter(conf, cluster_name)
        elif action == "modify":
            params = { 'business': args.business,
                       'project': args.project,
                       'set_description': args.set_description,
                       'set_domain': args.set_domain,
                       'new_domain': args.new_domain,
                       'domain_domain': args.domain_name }
            self.app = HPCStatsModifier(conf, cluster_name, params)
        elif action == "report":
            template = args.template
            interval = args.interval
            self.app = HPCStatsReporter(conf, cluster_name,
                                        template, interval)

    def run(self):
        """Run the application and catch all exceptions."""

        try:
            self.app.run()
        except HPCStatsConfigurationException, err:
            logging.error("Configuration Error: %s", err)
            self.exit()
        except HPCStatsDBIntegrityError, err:
            logging.error("DB Integrity Error: %s", err)
            self.exit()
        except HPCStatsSourceError, err:
            logging.error("Source Error: %s", err)
            self.exit()
        except HPCStatsRuntimeError, err:
            logging.error("Runtime Error: %s", err)
            self.exit()


    def exit(self):
        """Clean-up the application and exit the program with error return
           node.
        """

        if self.app is not None:
            self.app.cleanup()
        sys.exit(1)
