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
logger = logging.getLogger(__name__)
import logging.handlers
import locale

from HPCStats.Exceptions import HPCStatsArgumentException, HPCStatsConfigurationException, HPCStatsDBIntegrityError, HPCStatsSourceError, HPCStatsRuntimeError
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Log.Logger import HPCStatsLogger
from HPCStats.Errors.Mgr import HPCStatsErrorMgr
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
        except HPCStatsArgumentException as err:
            logger.error("Argument Error: %s", err)
            self.exit()

        # locale to format numbers
        # TODO: load locale output of the environment
        try:
            locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        except locale.Error as err:
            logger.error("Error while setting locale: %s", err)
            self.exit()

        # Change the default logger class. This way, the logger instanciated
        # for Importer.log attribute will be a HPCStatsLogger object and all
        # sub-Importer classes are able to use its specific warn() method.
        logging.setLoggerClass(HPCStatsLogger)

        # enable debug mode
        logging_level = logging.INFO
        if args.debug:
            logging_level = logging.DEBUG

        app_logger = logging.getLogger('HPCStats')
        app_logger.setLevel(logging_level)

        if args.batch == True:

            # In batch mode, set 2 handlers:
            #   - console handler with warning level for cronjobs emails
            #   - syslog handler with info/debug level (depending on --debug
            #     parameter) for sysadmins

            hdr_str = logging.StreamHandler()
            hdr_str.setLevel(logging.WARNING)
            fmt_str = logging.Formatter("%(levelname)s: %(module)s - %(message)s")
            hdr_str.setFormatter(fmt_str)
            app_logger.addHandler(hdr_str)

            hdr_sys = logging.handlers.SysLogHandler('/dev/log')
            hdr_sys.setLevel(logging_level)
            fmt_sys = logging.Formatter("%(levelname)s: %(module)s: %(message)s")
            hdr_sys.setFormatter(fmt_sys)
            app_logger.addHandler(hdr_sys)

        else:

            # In normal mode, only one console handler with info/debug level
            # (depending on --debug parameter)

            hdr_str = logging.StreamHandler()
            hdr_str.setLevel(logging_level)
            fmt_str = logging.Formatter("%(levelname)s: %(module)s - %(message)s")
            hdr_str.setFormatter(fmt_str)
            app_logger.addHandler(hdr_str)

        action = args.action
        cluster_name = args.cluster.pop()
        conf = HPCStatsConf(args.conf, cluster_name)

        try:
            conf.read()
        except HPCStatsConfigurationException as err:
            logger.error("Configuration Error: %s", err)
            self.exit()

        # set error manager for HPCStatsLogger
        app_logger.set_error_mgr(HPCStatsErrorMgr(conf))

        if action == "check":
            self.app = HPCStatsChecker(conf, cluster_name)
        elif action == "import":
            params = { 'since_event': args.since_event,
                       'since_jobid': args.since_jobid }
            self.app = HPCStatsImporter(conf, cluster_name, params)
        elif action == "modify":
            params = { 'business': args.business,
                       'project': args.project,
                       'set_description': args.set_description,
                       'set_domain': args.set_domain,
                       'new_domain': args.new_domain,
                       'domain_name': args.domain_name }
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
        except HPCStatsConfigurationException as err:
            logger.error("Configuration Error: %s", err)
            self.exit()
        except HPCStatsDBIntegrityError as err:
            logger.error("DB Integrity Error: %s", err)
            self.exit()
        except HPCStatsSourceError as err:
            logger.error("Source Error: %s", err)
            self.exit()
        except HPCStatsRuntimeError as err:
            logger.error("Runtime Error: %s", err)
            self.exit()


    def exit(self):
        """Clean-up the application and exit the program with error return
           node.
        """

        if self.app is not None:
            self.app.cleanup()
        sys.exit(1)
