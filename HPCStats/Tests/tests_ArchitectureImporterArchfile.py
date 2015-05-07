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
           }
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

        arch = {
          "test_cluster": {
            "partitions": "group_compute",
          },
          "test_cluster/group_compute": {
            "nodesets": "cn", \
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
        self.importer.arch.conf = arch
        self.importer.load()

        self.assertEquals(len(self.importer.nodes), 1000)
        self.assertEquals(self.importer.cluster.name, 'test_cluster')
        self.assertEquals(self.importer.nodes[0].memory, 24 * 1024 ** 3)
        self.assertEquals(self.importer.nodes[0].cpu, 12)
        self.assertEquals(self.importer.nodes[0].name, 'cn0001')
        self.assertEquals(self.importer.nodes[0].partition, 'group_compute')
        self.assertEquals(self.importer.partitions['cn[0001-1000]'], ['compute'])

loadtestcase(TestsArchitectureImporterArchfileLoad)