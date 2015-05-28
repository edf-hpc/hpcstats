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

from HPCStats.Model.Cluster import Cluster
from HPCStats.Importer.Events.EventImporterSlurm import EventImporterSlurm
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockPg2 import mock_psycopg2
import HPCStats.Tests.Mocks.MySQLdb as MockMySQLdb # for MY_REQS
from HPCStats.Tests.Mocks.MySQLdb import mock_mysqldb
from HPCStats.Tests.Mocks.Conf import MockConf
from HPCStats.Tests.Mocks.App import MockApp

CONFIG = {
           'hpcstatsdb': {
             'hostname': 'test_hostname',
             'port':     'test_port',
             'dbname':   'test_name',
             'user':     'test_user',
             'password': 'test_password',
           },
           'testcluster/slurm': {
             'host': 'dbhost',
             'port': 3128,
             'name': 'dbname',
             'user': 'dbuser',
             'password': 'dbpassword',
           }
         }

class TestsEventImporterSlurm(HPCStatsTestCase):

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def setUp(self):
        self.filename = 'fake'
        self.cluster = Cluster('testcluster')
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG.copy()
        self.app = MockApp()
        self.db = HPCStatsDB(self.conf)
        self.db.bind()
        self.importer = EventImporterSlurm(self.app,
                                           self.db,
                                           self.conf,
                                           self.cluster)

    def test_init(self):
        """EventImporterSlurm.__init__() initializes w/o error
        """
        pass

    @mock.patch('HPCStats.Importer.Events.EventImporterSlurm.MySQLdb',
                mock_mysqldb())
    def test_init(self):
        """EventImporterSlurm.load() works with simple data."""
        MockMySQLdb.MY_REQS = {}
        self.importer.load()

loadtestcase(TestsEventImporterSlurm)
