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
from HPCStats.Model.Event import Event
from HPCStats.Importer.Events.EventImporterSlurm import EventImporterSlurm
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockPg2 import mock_psycopg2, init_reqs
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

MockMySQLdb.MY_REQS['get_events'] = {
  'req': "SELECT time_start, time_end, node_name, (cpu_count|tres), " \
                "state, reason " \
         "FROM .*_event_table " \
         "WHERE node_name <> '' " \
         "AND time_start >= \%s\ " \
         "ORDER BY time_start",
  'res': [],
}

MockMySQLdb.MY_REQS['event_table_cols'] = {
  'req': "SHOW COLUMNS FROM .*_event_table LIKE 'cpu_count'",
  'res': [],
}


module = 'HPCStats.Importer.Events.EventImporterSlurm'

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
        self.app = MockApp(self.db, self.conf, self.cluster)
        self.importer = EventImporterSlurm(self.app,
                                           self.db,
                                           self.conf,
                                           self.cluster)
        init_reqs()

    def test_init(self):
        """EventImporterSlurm.__init__() initializes w/o error
        """
        pass

    def init_load_data(self):
        """Utility method to initialize data to make load() simply."""

        self.e1_start = datetime(2015, 3, 2, 15, 59, 59)
        self.e1_end = datetime(2015, 3, 2, 16, 0, 0)
        self.node_name = 'node1'
        e1_start_ts = time.mktime(self.e1_start.timetuple())
        e1_end_ts = time.mktime(self.e1_end.timetuple())

        MockMySQLdb.MY_REQS['get_events']['res'] = \
          [
            [ e1_start_ts, e1_end_ts, self.node_name, '1=16', 35, 'reason1' ],
          ]
        MockMySQLdb.MY_REQS['event_table_cols']['res'] = [ ]

        self.app.arch.nodes = [ Node(self.node_name, self.cluster, 'model1', 'partition1', 16, 8, 0), ]

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_is_old_schema(self):
        """EventImporterSlurm._is_old_schema() should return True is SlurmDBD
           <15.08 is detected, False otherwise."""

        self.importer.connect_db()
        MockMySQLdb.MY_REQS['event_table_cols']['res'] = \
          [ [ 'cpu_count', ] , ]
        self.assertEquals(self.importer._is_old_schema(), True)

        MockMySQLdb.MY_REQS['event_table_cols']['res'] = []
        self.assertEquals(self.importer._is_old_schema(), False)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_simple(self):
        """EventImporterSlurm.load() works with simple data."""

        self.init_load_data()
        self.importer.load()
        self.assertEquals(1, len(self.importer.events))
        event = self.importer.events[0]
        self.assertEquals(event.start_datetime, self.e1_start)
        self.assertEquals(event.end_datetime, self.e1_end)
        self.assertEquals(event.nb_cpu, 16)
        self.assertEquals(event.event_type, 'ALLOCATED+RES')
        self.assertEquals(event.reason, 'reason1')

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_old_schema(self):
        """EventImporterSlurm.load() works with simple data from old SlurmDBD
           <15.08 schema."""

        self.init_load_data()
        MockMySQLdb.MY_REQS['event_table_cols']['res'] = \
          [ [ 'cpu_count', ] , ]
        MockMySQLdb.MY_REQS['get_events']['res'][0][3] = 16
        self.importer.load()
        event = self.importer.events[0]
        self.assertEquals(event.nb_cpu, 16)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    @mock.patch("%s.EventImporterSlurm.get_new_events" % (module))
    def test_load_search_datetime(self, mock_new_events):
        """EventImporterSlurm.load() must search new events starting from
           correct datetime."""

        # Both datetimes are defined, search must be done with start datetime
        # of oldest unfinished event.
        d1 = datetime(2015, 3, 2, 15, 59, 59)
        d2 = datetime(2015, 3, 2, 16, 0, 0)
        d1_ts = time.mktime(d1.timetuple())
        d2_ts = time.mktime(d2.timetuple())

        MockPg2.PG_REQS['get_end_last_event'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ [ d1_ts ] ]
        )
        MockPg2.PG_REQS['get_start_oldest_unfinised_event'].set_assoc(
          params= ( self.cluster.cluster_id ),
          result=[ [ d2_ts ] ]
        )

        self.importer.load()
        mock_new_events.assert_called_with(d2_ts)

        # None unfinished event, search must be done with end datetime of last
        # event.
        MockPg2.PG_REQS['get_end_last_event'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ [ d1_ts ] ]
        )
        MockPg2.PG_REQS['get_start_oldest_unfinised_event'].set_assoc(
          params= ( self.cluster.cluster_id ),
          result=[ ]
        )

        self.importer.load()
        mock_new_events.assert_called_with(d1_ts)

        default_datetime = datetime(1970, 1, 1, 1, 0)

        # No event in DB: search starting from epoch.
        MockPg2.PG_REQS['get_end_last_event'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ ]
        )
        MockPg2.PG_REQS['get_start_oldest_unfinised_event'].set_assoc(
          params= ( self.cluster.cluster_id ),
          result=[ ]
        )

        self.importer.load()
        mock_new_events.assert_called_with(default_datetime)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_unfound_node(self):
        """EventImporterSlurm.load() raises Exception if one event is linked to
           a node not loaded by ArchitectureImporter."""

        self.init_load_data()
        self.app.arch.nodes = []
        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "event node %s not found in loaded nodes" % (self.node_name),
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_invalid_tres(self):
        """EventImporterSlurm.load() raises exception if invalid tres for an
           event is found"""

        self.init_load_data()
        MockMySQLdb.MY_REQS['get_events']['res'][0][3] = '0=0'
        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "unable to extract cpu_count from event tres",
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_merge_successive_events(self):
        """EventImporterSlurm.merge_successive_events() should merge successive
           events in the list if they are on the same node w/ same type.
        """

        e1_start = datetime(2015, 3, 2, 16,  0, 0)
        e1_end   = datetime(2015, 3, 2, 16, 10, 0)
        e2_start = datetime(2015, 3, 2, 16, 10, 0)
        e2_end   = datetime(2015, 3, 2, 16, 20, 0)
        e3_start = datetime(2015, 3, 2, 16, 20, 0)
        e3_end   = datetime(2015, 3, 2, 16, 30, 0)

        node1 = [ Node('node1', self.cluster, 'model1', 'partition1', 16, 8, 0), ]
        node2 = [ Node('node2', self.cluster, 'model1', 'partition1', 16, 8, 0), ]

        # 3 successive events on one node with same type, they must be merged
        # into one event.
        events = [
          Event(self.cluster, node1, 4, e1_start, e1_end, 'type1', 'reason1'),
          Event(self.cluster, node1, 4, e2_start, e2_end, 'type1', 'reason1'),
          Event(self.cluster, node1, 4, e3_start, e3_end, 'type1', 'reason1'),
        ]
        merged = self.importer.merge_successive_events(events)
        self.assertEquals(1, len(merged))
        self.assertEquals(merged[0].start_datetime, e1_start)
        self.assertEquals(merged[0].end_datetime, e3_end)
        self.assertEquals(merged[0].event_type, 'type1')
        self.assertEquals(merged[0].reason, 'reason1')

        # 3 successive events on one node node1 with same type, with one event
        # on another node node2 in the middle: all events on node1 must be
        # merged while the other event on node2 must stay as is.
        events = [
          Event(self.cluster, node1, 4, e1_start, e1_end, 'type1', 'reason1'),
          Event(self.cluster, node2, 4, e2_start, e2_end, 'type1', 'reason1'),
          Event(self.cluster, node1, 4, e2_start, e2_end, 'type1', 'reason1'),
          Event(self.cluster, node1, 4, e3_start, e3_end, 'type1', 'reason1'),
        ]
        merged = self.importer.merge_successive_events(events)
        self.assertEquals(2, len(merged))
        self.assertEquals(merged[0].start_datetime, e1_start)
        self.assertEquals(merged[0].end_datetime, e3_end)
        self.assertEquals(merged[1].end_datetime, e2_end)
        self.assertEquals(merged[0].node, node1)
        self.assertEquals(merged[1].node, node2)

        # 3 successive events on node1 but with different types, they must not
        # be merged.
        events = [
          Event(self.cluster, node1, 4, e1_start, e1_end, 'type1', 'reason1'),
          Event(self.cluster, node1, 4, e2_start, e2_end, 'type2', 'reason1'),
          Event(self.cluster, node1, 4, e3_start, e3_end, 'type1', 'reason1'),
        ]
        merged = self.importer.merge_successive_events(events)
        self.assertEquals(3, len(merged))

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_txt_slurm_event_type(self):
        """EventImporterSlurm.txt_slurm_event_type() should give the
           appropriate human readable string represation of an event type
           according to its hex bitmap value.
        """

        tests = [ ( 0x0001, 'DOWN' ),
                  ( 0x0004, 'ERROR' ),
                  ( 0x0012, 'IDLE+NET' ),
                  ( 0x8535, 'MIXED+NET+RES+RESUME+COMPLETING+MAINT' ) ]
        for value, expected in tests:
            txt = EventImporterSlurm.txt_slurm_event_type(value)
            self.assertEquals(txt, expected)

if __name__ == '__main__':

    loadtestcase(TestsEventImporterSlurm)
