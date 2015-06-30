#!/usr/bin/env python
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

from HPCStats.Exceptions import HPCStatsArgumentException
from HPCStats.CLI.HPCStatsArgumentParser import HPCStatsArgumentParser
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase

class TestsHPCStatsArgumentParser(HPCStatsTestCase):

    def setUp(self):
        self.parser = HPCStatsArgumentParser('hpcstats')
        self.parser.add_args()

    def test_init(self):
        """HPCStatsArgumentParser.__init__() + add_args() run w/o problem
        """
        pass

    def test_report(self):
        """HPCStatsArgumentParser.parse_args() w/ report action
        """
        argv = ['report', '--cluster', 'test']
        args = self.parser.parse_args(argv)
        self.assertEquals(args.action, 'report')

    def test_import(self):
        """HPCStatsArgumentParser.parse_args() w/ import action
        """
        argv = ['import', '--cluster', 'test']
        args = self.parser.parse_args(argv)
        self.assertEquals(args.action, 'import')

    def test_modify(self):
        """HPCStatsArgumentParser.parse_args() w/ modify action
        """
        # All of these are acceptable combinations of params
        argvs = [ [ 'modify', '--business-code', 'B1', '--set-description', 'desc1' ],
                  [ 'modify', '--project-code', 'P1', '--set-description', 'desc1' ],
                  [ 'modify', '--project-code', 'P1', '--set-domain', 'D1' ],
                  [ 'modify', '--new-domain', 'D1', '--domain-name', 'domain D1' ] ]
        for argv in argvs:
            args = self.parser.parse_args(argv)
            self.assertEquals(args.action, 'modify')

    def test_modify_missing_param(self):
        """HPCStatsArgumentParser.parse_args() raise exception when
           the main param are missing
        """
        argv = [ 'modify' ]
        self.assertRaisesRegexp(
          HPCStatsArgumentException,
          "either --business-code, --project-code or --new-domain parameters must be set with modify action",
          self.parser.parse_args,
          argv)

    def test_modify_params_mutually_exclusive(self):
        """HPCStatsArgumentParser.parse_args() raise exception in case of
           conflict w/ mutually exclusive main params
        """
        argvs = [ [ 'modify', '--business-code', 'B1', '--project-code', 'P1'],
                  [ 'modify', '--business-code', 'B1', '--new-domain', 'D1' ],
                  [ 'modify', '--project-code', 'P1', '--new-domain', 'D1' ] ]
        for argv in argvs:
            self.assertRaisesRegexp(
              HPCStatsArgumentException,
              "parameters --business-code, --project-code and --new-domain are mutually exclusive",
              self.parser.parse_args,
              argv)

    def test_modify_business_missing_desc(self):
        """HPCStatsArgumentParser.parse_args() raise exception when
           modify business code w/o description
        """
        argv = [ 'modify', '--business-code', 'B1' ]
        self.assertRaisesRegexp(
          HPCStatsArgumentException,
          "--set-description parameter is required to modify a business code",
          self.parser.parse_args,
          argv)

    def test_modify_project_missing_param(self):
        """HPCStatsArgumentParser.parse_args() raise exception when
           modify project w/o param
        """
        argv = [ 'modify', '--project-code', 'P1' ]
        self.assertRaisesRegexp(
          HPCStatsArgumentException,
          "--set-description or --set-domain parameters are required to modify a project",
          self.parser.parse_args,
          argv)

    def test_modify_project_conflict_params(self):
        """HPCStatsArgumentParser.parse_args() raise exception when
           modify project w/ conflicting params
        """
        argv = [ 'modify', '--project-code', 'P1', '--set-description', 'desc P1', '--set-domain', 'D1' ]
        self.assertRaisesRegexp(
          HPCStatsArgumentException,
          "--set-description and --set-domain parameters are mutually exclusive to modify a project",
          self.parser.parse_args,
          argv)

    def test_modify_domain_missing_name(self):
        """HPCStatsArgumentParser.parse_args() raise exception when
           modify domain w/o name
        """
        argv = [ 'modify', '--new-domain', 'D1' ]
        self.assertRaisesRegexp(
          HPCStatsArgumentException,
          "--domain-name parameter is required to create a new domain",
          self.parser.parse_args,
          argv)

if __name__ == '__main__':

    loadtestcase(TestsHPCStatsArgumentParser)
