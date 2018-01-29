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
from HPCStats.Model.Cluster import Cluster
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockPg2 import mock_psycopg2, init_reqs

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
           'testcluster': {
             'architecture': 'archfile',
             'users': 'ldap',
             'fsusage': 'ssh',
             'events': 'slurm',
             'jobs': 'slurm',
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
        self.importer = HPCStatsImporter(self.conf, self.cluster, {})
        init_reqs()

    def test_init(self):
        """HPCStatsImporter.__init__() run w/o problem
        """
        pass

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    @mock.patch("HPCStats.Importer.Jobs.JobImporterFactory.JobImporterSlurm")
    @mock.patch("HPCStats.Importer.Events.EventImporterFactory.EventImporterSlurm")
    @mock.patch("HPCStats.Importer.FSUsage.FSUsageImporterFactory.FSUsageImporterSSH")
    @mock.patch("HPCStats.Importer.Users.UserImporterFactory.UserImporterLdap")
    @mock.patch("HPCStats.Importer.Architectures.ArchitectureImporterFactory.ArchitectureImporterArchfile")
    def test_run(self, arch_m, user_m, fs_m, event_m, job_m):
        """HPCStatsImporter.run() calls all importer load/update methods.
        """

        # Get mocked classes instances, and configure the cluster attribute of
        # ArchImporter instance
        arch_i = arch_m.return_value
        arch_i.cluster = Cluster(self.cluster, 0)
        user_i = user_m.return_value
        fs_i = fs_m.return_value
        event_i = event_m.return_value
        job_i = job_m.return_value

        self.importer.run()

        arch_i.load.assert_called_once_with()
        arch_i.update.assert_called_once_with()
        user_i.load.assert_called_once_with()
        user_i.update.assert_called_once_with()
        fs_i.load.assert_called_once_with()
        fs_i.update.assert_called_once_with()
        event_i.load.assert_called_once_with()
        event_i.update.assert_called_once_with()
        job_i.load_update_window.assert_called_once_with()

    def test_run_exception_no_hpcstatsdb(self):
        """HPCStatsImporter.run() raise exception when hpcstatsdb section is
           missing.
        """
        del self.conf.conf['hpcstatsdb']

        self.assertRaisesRegexp(
               HPCStatsConfigurationException,
               "section hpcstatsdb not found",
               self.importer.run)

if __name__ == '__main__':

    loadtestcase(TestsHPCStatsImporter)
