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

from datetime import datetime
import time
import mock

from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Model.Cluster import Cluster
from HPCStats.Model.Node import Node
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
        self.db = HPCStatsDB(self.conf)
        self.db.bind()
        self.app = MockApp(self.db, self.conf, self.cluster.name)
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
    def test_load_simple(self):
        """EventImporterSlurm.load() works with simple data."""

        e1_start = datetime(2015, 3, 2, 15, 59, 59)
        e1_end = datetime(2015, 3, 2, 16, 0, 0)
        e1_start_ts = time.mktime(e1_start.timetuple())
        e1_end_ts = time.mktime(e1_end.timetuple())

        node_name = 'node1'
        MockMySQLdb.MY_REQS = {
          'get_events': {
            'req': "SELECT time_start, time_end, node_name, cpu_count, " \
                          "state, reason " \
                   "FROM .*_event_table " \
                   "WHERE node_name <> '' " \
                   "AND time_start >= UNIX_TIMESTAMP(.*) " \
                   "ORDER BY time_start",
            'res': [
              [ e1_start_ts, e1_end_ts,
                node_name, 16, 35, 'reason1' ],
            ]
          }
        }

        self.app.arch.nodes = [ Node(node_name, self.cluster, 'partition1', 16, 8, 0), ]
        self.importer.load()
        self.assertEquals(1, len(self.importer.events))
        event = self.importer.events[0]
        self.assertEquals(event.start_datetime, e1_start)
        self.assertEquals(event.end_datetime, e1_end)
        self.assertEquals(event.nb_cpu, 16)
        self.assertEquals(event.event_type, 'ALLOCATED+RES')
        self.assertEquals(event.reason, 'reason1')

    @mock.patch('HPCStats.Importer.Events.EventImporterSlurm.MySQLdb',
                mock_mysqldb())
    def test_load_unfound_node(self):
        """EventImporterSlurm.load() raises Exception if one event is linked to
           a node not loaded by ArchitectureImporter."""

        e1_start = datetime(2015, 3, 2, 15, 59, 59)
        e1_end = datetime(2015, 3, 2, 16, 0, 0)
        e1_start_ts = time.mktime(e1_start.timetuple())
        e1_end_ts = time.mktime(e1_end.timetuple())

        node_name = 'node1'
        MockMySQLdb.MY_REQS = {
          'get_events': {
            'req': "SELECT time_start, time_end, node_name, cpu_count, " \
                          "state, reason " \
                   "FROM .*_event_table " \
                   "WHERE node_name <> '' " \
                   "AND time_start >= UNIX_TIMESTAMP(.*) " \
                   "ORDER BY time_start",
            'res': [
              [ e1_start_ts, e1_end_ts,
                node_name, 16, 35, 'reason1' ],
            ]
          }
        }

        self.app.arch.nodes = []
        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "event node %s not found in loaded nodes" % (node_name),
               self.importer.load)

loadtestcase(TestsEventImporterSlurm)
