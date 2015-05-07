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
import copy
from StringIO import StringIO

from HPCStats.Exceptions import *
from HPCStats.Importer.Architectures.ArchitectureImporterArchfile import ArchitectureImporterArchfile
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Model.Cluster import Cluster
from HPCStats.Model.Node import Node
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Mocks.Utils import mock_open
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for REQS
from HPCStats.Tests.Mocks.MockPg2 import mock_psycopg2
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase

CONFIG = {
  'hpcstatsdb': {
    'hostname': 'test_hostname',
    'port':     'test_port',
    'dbname':   'test_name',
    'user':     'test_user',
    'password': 'test_password',
  },
  'test_cluster/archfile': {
    'file': 'fake_arch_file',
  },
}

BASIC_ARCH = {
"test_cluster": {
    "partitions": "group_compute",
  },
  "test_cluster/group_compute": {
    "nodesets": "cn",
    "slurm_partitions": "compute",
  },
  "test_cluster/group_compute/cn": {
    "names": "cn[0001-1000]",
    "sockets": 2,
    "corespersocket": 6,
    "frequency": "2.93GHz",
    "floatinstructions":4,
    "memory": "24GB",
    "model": "test_model",
  },
}

module = "HPCStats.Importer.Architectures.ArchitectureImporterArchfile"

class TestsArchitectureImporterArchfileLoad(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'test_cluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG.copy()
        self.app = None
        self.db = None
        self.importer = ArchitectureImporterArchfile(self.app,
                                                     self.db,
                                                     self.conf,
                                                     self.cluster)
        self.importer.arch = MockConfigParser()

    def test_init(self):
        """ArchitectureImporterArchfile.__init__() runs w/o problem
        """
        pass

    @mock.patch("%s.ArchitectureImporterArchfile.read_arch" % (module))
    def test_load_1(self, m_read_arch):
        """ArchitectureImporterArchfile.load() works with simple data
        """

        self.importer.arch.conf = copy.deepcopy(BASIC_ARCH)
        self.importer.load()

        self.assertEquals(len(self.importer.nodes), 1000)
        self.assertEquals(self.importer.cluster.name, 'test_cluster')
        self.assertEquals(self.importer.nodes[0].memory, 24 * 1024 ** 3)
        self.assertEquals(self.importer.nodes[0].cpu, 12)
        self.assertEquals(self.importer.nodes[0].name, 'cn0001')
        self.assertEquals(self.importer.nodes[0].partition, 'group_compute')
        self.assertEquals(self.importer.partitions['cn[0001-1000]'], ['compute'])

    @mock.patch("%s.ArchitectureImporterArchfile.read_arch" % (module))
    def test_load_missing_section(self, m_read_arch):
        """ArchitectureImporterArchfile.load() raise exception in one section
           is missing
        """

        for section in BASIC_ARCH.keys():
            self.importer.arch.conf = copy.deepcopy(BASIC_ARCH)
            del self.importer.arch.conf[section]
            self.assertRaisesRegexp(
                   HPCStatsSourceError,
                   "missing section %s in architecture file" % (section),
                   self.importer.load)

    @mock.patch("%s.ArchitectureImporterArchfile.read_arch" % (module))
    def test_load_missing_option(self, m_read_arch):
        """ArchitectureImporterArchfile.load() raise exception in one option
           is missing
        """

        for section in BASIC_ARCH.keys():
            for option in BASIC_ARCH[section].keys():
                self.importer.arch.conf = copy.deepcopy(BASIC_ARCH)
                del self.importer.arch.conf[section][option]
                self.assertRaisesRegexp(
                       HPCStatsSourceError,
                       "missing option %s in section %s of architecture file" \
                         % (option, section),
                       self.importer.load)

    def test_convert_freq(self):
        """ArchitectureImporterArchfile.convert_freq() should properly convert
           frequency string into float
        """
        freqs = { '24MHz' : 24 * 1000 ** 2,
                  '24MHz': 24 * 1000 ** 2,
                  '24mhz': 24 * 1000 ** 2,
                  '24 Mhz': 24 * 1000 ** 2,
                  '2.5GHz': 2.5 * 1000 ** 3,
                  '3GHz' : 3 * 1000 ** 3,
                  '1 GHz' : 1 * 1000 ** 3,
                  '2 Ghz' : 2 * 1000 ** 3,
                  '3' : None,
                  '5.5.5Ghz' : None,
                  'fail' : None }
        for freq_s, freq_f in freqs.iteritems():
            self.assertEqual(ArchitectureImporterArchfile.convert_freq(freq_s),
                             freq_f)

class TestsArchitectureImporterArchfileUpdate(HPCStatsTestCase):

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'test_cluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG.copy()
        self.app = None
        self.db = HPCStatsDB(self.conf)
        self.db.bind()
        self.importer = ArchitectureImporterArchfile(self.app,
                                                     self.db,
                                                     self.conf,
                                                     self.cluster)

    def test_update(self):
        """ProjectImporterCSV.update() creates cluster and node if not existing
        """
        MockPg2.REQS = {
          "save_cluster_cluster1": {
            "req": "INSERT INTO Cluster \( cluster_name \) " \
                   "VALUES \( %s \) "\
                   "RETURNING cluster_id",
            "res": [ [ 1 ] ],
          },
          "save_node_node1": {
            "req": "INSERT INTO Node \( node_name, " \
                                       "cluster_id, "\
                                       "node_partition, "\
                                       "node_nbCpu, "\
                                       "node_memory, "\
                                       "node_flops \) "\
                   "VALUES \( %s, %s, %s, %s, %s, %s \) "\
                   "RETURNING node_id",
            "res": [ [ 1 ] ],
          },
        }
        cluster1 = Cluster('cluster1')
        node1 = Node('node1', cluster1, 'test_partition', 12, 6 * 1024 ** 3, 1)
        self.importer.cluster = cluster1
        self.importer.nodes = [ node1 ]

        self.importer.update()

    def test_update_2(self):
        """ProjectImporterCSV.update() detect existing cluster and node
        """
        MockPg2.REQS = {
          "find_cluster_cluster1": {
            "req": "SELECT cluster_id " \
                   "FROM Cluster " \
                   "WHERE cluster_name = %s",
            "res": [ [ 1 ] ],
          },
          "find_node_node1": {
            "req": "SELECT node_id " \
                   "FROM Node " \
                   "WHERE node_name = %s " \
                   "AND cluster_id = %s",
            "res": [ [ 1 ] ],
          },
        }
        cluster1 = Cluster('cluster1')
        node1 = Node('node1', cluster1, 'test_partition', 12, 6 * 1024 ** 3, 1)
        self.importer.cluster = cluster1
        self.importer.nodes = [ node1 ]

        self.importer.update()

loadtestcase(TestsArchitectureImporterArchfileLoad)
loadtestcase(TestsArchitectureImporterArchfileUpdate)
