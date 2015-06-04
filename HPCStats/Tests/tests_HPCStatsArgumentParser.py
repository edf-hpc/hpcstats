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

loadtestcase(TestsHPCStatsArgumentParser)
