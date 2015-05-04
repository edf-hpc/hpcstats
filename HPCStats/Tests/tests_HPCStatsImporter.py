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

from HPCStats.CLI.HPCStatsImporter import HPCStatsImporter
from HPCStats.Tests.Mocks.Conf import MockConf
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase

CONFIG = { 'clusters':
             {
               'clusters': 'testcluster,testcluster2',
             },
           'testcluster/slurm':
             { 'host': 'dbhost',
               'port': 3128,
               'name': 'dbname',
               'user': 'dbuser',
               'password': 'dbpassword' }
         }

class TestsHPCStatsImporter(HPCStatsTestCase):

    def setUp(self):
        self.conf = MockConf(CONFIG, 'testcluster')
        self.importer = HPCStatsImporter(self.conf, 'testcluster')

    def test_init(self):
        """HPCStatsImporter.__init__() + add_args() run w/o problem
        """
        pass

loadtestcase(TestsHPCStatsImporter)
