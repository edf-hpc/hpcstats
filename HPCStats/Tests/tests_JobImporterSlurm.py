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
from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MySQLdb import mock_mysqldb
from HPCStats.Tests.Mocks.Conf import MockConf
from HPCStats.Tests.Mocks.App import MockApp

CONFIG = { 'testcluster/slurm':
             { 'host': 'dbhost',
               'port': 3128,
               'name': 'dbname',
               'user': 'dbuser',
               'password': 'dbpassword' }
         }

class TestsJobImporterSlurm(HPCStatsTestCase):

    @mock.patch('HPCStats.Importer.Jobs.JobImporterSlurm.MySQLdb',
                mock_mysqldb())
    def setUp(self):
        self.db = 'testdb'
        self.conf = MockConf(CONFIG, 'testcluster')
        self.cluster = Cluster('testcluster')
        self.app = MockApp()
        self.importer = JobImporterSlurm(self.app,
                                         self.db,
                                         self.conf,
                                         self.cluster)

    def test_init(self):
        """JobImporterSlurm.__init__() initializes object with attributes
        """
        self.assertEquals(self.importer._dbhost,
                          self.conf.conf[self.cluster.name + '/slurm']['host'])

loadtestcase(TestsJobImporterSlurm)
