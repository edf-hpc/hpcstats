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

"""This module contains the HPCStatsArgumentParser class."""

import argparse
from HPCStats.Exceptions import HPCStatsArgumentException

class HPCStatsArgumentParser(argparse.ArgumentParser):

    """This class inherits the Python standard ArgumentParser class, it
       implements the CLI argument parser for the HPCStats program.
    """

    def __init__(self, *args, **kwargs):

        super(HPCStatsArgumentParser, self).__init__(*args, **kwargs)

    def add_args(self):

        """Add all arguments with their constraints to the parser."""

        self.add_argument("-c", "--conf",
                          dest="conf",
                          default="/etc/hpcstats/hpcstats.conf",
                          help="HPCStats configuration file")

        self.add_argument("-d", "--debug",
                          help='Enable debug output',
                          action="store_true")

        self.add_argument("--batch-mode",
                          dest="batch",
                          help='Set application output in batch mode',
                          action="store_true")

        subparsers = self.add_subparsers(help='sub-command help',
                                         dest='action')

        parser_imp = subparsers.add_parser('import', help='import help')

        parser_imp.add_argument("--cluster",
                                dest='cluster',
                                nargs=1,
                                required=True,
                                help="Cluster to import data from. " \
                                     "Could be one cluster name or " \
                                     "special value all for all " \
                                     "clusters at once" )

        parser_imp.add_argument("--since-event",
                                dest='since_event',
                                nargs=1,
                                default='1970-01-01',
                                help="Import event from this date for new " \
                                     "clusters (default: %(default)s)" )

        parser_imp.add_argument("--since-jobid",
                                dest='since_jobid',
                                nargs=1,
                                type=int,
                                default='-1',
                                help="Import jobs starting from this job id "\
                                     "for new clusters (default: %(default)s)" )

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
                                     "(default: %(default)s)")

        parser_rep.add_argument("--template",
                                dest="template",
                                default="csv",
                                help="template to use for formatted " \
                                     "output (default: %(default)s)")

        parser_chk = subparsers.add_parser('check', help='check help')

        parser_chk.add_argument("--cluster",
                                dest='cluster',
                                nargs=1,
                                required=True,
                                help="Cluster data sources to check" )

        parser_mod = subparsers.add_parser('modify', help='modify help')

        # modify sub-parser possible combinations:
        #
        #   - modify description of business B1:
        #   $ hpcstats modify --business-code=B1 --set-descrition='business code B1 description'
        #
        #   - modify description of project P1:
        #   $ hpcstats modify --project-code=P1 --set-descrition='project P1 description'
        #
        #   - create new domain D1:
        #   $ hpcstats modify --new-domain=D1 --domain-name='Domain name D1'
        #
        #   - set domain D1 for project P1:
        #   $ hpcstats modify --project-code=P1 --set-domain=D1


        parser_mod.add_argument("--business-code",
                                dest='business',
                                nargs=1,
                                help="The business code to modify" )

        parser_mod.add_argument("--project-code",
                                dest='project',
                                nargs=1,
                                help="The project code to modify" )

        parser_mod.add_argument("--set-description",
                                dest='description',
                                nargs=1,
                                help="Project or Business description" )

        parser_mod.add_argument("--set-domain",
                                dest='set_domain',
                                nargs=1,
                                help="Domain key to set for Project" )

        parser_mod.add_argument("--new-domain",
                                dest='new_domain',
                                nargs=1,
                                help="Create domain key" )

        parser_mod.add_argument("--domain-name",
                                dest='domain_name',
                                nargs=1,
                                help="The name of the domain to create" )

    def parse_args(self, *args, **kwargs):

        """Call parent class parse_args() method and do more specifics
           arguments coherency checks.
        """

        args = super(HPCStatsArgumentParser, self).parse_args(*args, **kwargs)

        if args.action == 'import':

            # If the --since-* arguments are specified on command line, the
            # argparse module returns the values inside a list. Since nargs=1
            # the value is pop'ed here to get the value directly, and use it
            # whatever the default or user value is used.
            if type(args.since_event) is list:
                args.since_event = args.since_event.pop()

            if type(args.since_jobid) is list:
                args.since_jobid = args.since_jobid.pop()

        elif args.action == 'modify':

            # Check that either --business-code, --project-code or --new-domain
            # is set
            if args.business is None and args.project is None and \
               args.new_domain is None:
                raise HPCStatsArgumentException( \
                        "either --business-code, --project-code or " \
                        "--new-domain parameters must be set with modify " \
                        "action")

            # Check that --business-code, --project-code and --new-domain are
            # exclusive
            if (args.business is not None and args.project is not None) or \
               (args.business is not None and args.new_domain is not None) or \
               (args.project is not None and args.new_domain is not None):
                raise HPCStatsArgumentException( \
                        "parameters --business-code, --project-code and " \
                        "--new-domain are mutually exclusive")

            # Check that --set-description is set with --business-code
            if args.business is not None and args.description is None:
                raise HPCStatsArgumentException( \
                        "--set-description parameter is required to modify a " \
                        "business code")
            # Check that either --set-description or --set-domain are set with
            # --project-code
            if args.project is not None and args.description is None and \
               args.set_domain is None:
                raise HPCStatsArgumentException( \
                        "--set-description or --set-domain parameters are " \
                        "required to modify a project")

            # Check that not both --set-description and --set-domain are set
            # with --project-code
            if args.project is not None and args.description is not None and \
               args.set_domain is not None:
                raise HPCStatsArgumentException( \
                        "--set-description and --set-domain parameters are " \
                        "mutually exclusive to modify a project")

            # Check that --domain-name is set with --new-domain
            if args.new_domain is not None and args.domain_name is None:
                raise HPCStatsArgumentException( \
                        "--domain-name parameter is required to create a " \
                        "new domain")
        return args
