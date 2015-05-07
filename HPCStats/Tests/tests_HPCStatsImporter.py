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

import mock
from HPCStats.Exceptions import *
from HPCStats.CLI.HPCStatsImporter import HPCStatsImporter
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase

CONFIG = { 'clusters': {
             'clusters': 'testcluster,testcluster2',
           },
           'hpcstatsdb': {
             'hostname': 'test_hostname',
             'port':     'test_port',
             'dbname':   'test_name',
             'user':     'test_user',
             'password': 'test_password',
           },
           'globals': {
             'projects': 'csv',
           },
           'projects': {
             'file': 'fake_project_file',
           },
           'testcluster/slurm': {
             'host': 'dbhost',
             'port': 3128,
             'name': 'dbname',
             'user': 'dbuser',
             'password': 'dbpassword'
           },
         }

class TestsHPCStatsImporter(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'testcluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG.copy()
        self.importer = HPCStatsImporter(self.conf, self.cluster)

    def test_init(self):
        """HPCStatsImporter.__init__() run w/o problem
        """
        pass

    def test_run(self):
        """HPCStatsImporter.run() NOT SUPPOSED TO WORK YET.
        """
        pass
        #self.importer.run()

    def test_run_exception_no_hpcstatsdb(self):
        """HPCStatsImporter.run() raise exception when hpcstatsdb section is
           missing.
        """
        del self.conf.conf['hpcstatsdb']

        self.assertRaisesRegexp(
               HPCStatsConfigurationException,
               "section hpcstatsdb not found",
               self.importer.run)

loadtestcase(TestsHPCStatsImporter)
