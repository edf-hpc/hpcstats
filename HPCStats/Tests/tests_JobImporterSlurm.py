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
from HPCStats.Model.User import User
from HPCStats.Model.Account import Account
from HPCStats.Model.Project import Project
from HPCStats.Model.Sector import Sector
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Business import Business
from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm
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
    'password': 'dbpassword'
  }
}

MockMySQLdb.MY_REQS['get_jobs_after_batchid'] = {
  'req': "SELECT id_job, " \
                "job_db_inx, " \
                "id_user, " \
                "id_group, " \
                "time_submit, " \
                "time_start, " \
                "time_end, " \
                "nodes_alloc, " \
                "cpus_alloc, " \
                "partition, " \
                "qos.name AS qos, " \
                "state, " \
                "nodelist, " \
                "assoc.user, " \
                "job_name, " \
                "wckey " \
          "FROM .*_job_table job, "\
               ".*_assoc_table assoc, " \
               "qos_table qos " \
         "WHERE id_job >= %s " \
           "AND assoc.id_assoc = job.id_assoc " \
           "AND qos.id = job.id_qos " \
      "ORDER BY id_job",
  'res': [],
}

MockPg2.PG_REQS['get_batchid_oldest_unfinished'] = {
  'req': "SELECT MIN\(job_batch_id\) AS last_id " \
           "FROM Job " \
          "WHERE cluster_id = %s " \
            "AND \(job_start IS NULL " \
             "OR job_end IS NULL\)",
  'res': [],
}
MockPg2.PG_REQS['get_batchid_last'] = {
  'req': "SELECT MAX\(job_batch_id\) AS last_id " \
           "FROM Job "  \
          "WHERE cluster_id = %s",
  'res': [],
}

module = 'HPCStats.Importer.Jobs.JobImporterSlurm'

class TestsJobImporterSlurm(HPCStatsTestCase):

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
        self.importer = JobImporterSlurm(self.app,
                                         self.db,
                                         self.conf,
                                         self.cluster)

    def test_init(self):
        """JobImporterSlurm.__init__() initializes object with attributes
        """
        self.assertEquals(self.importer._dbhost,
                          self.conf.conf[self.cluster.name + '/slurm']['host'])

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load(self):
        """JobImporterSlurm.load() works with simple data."""

        j1_submit = datetime(2015, 3, 2, 16, 0, 1)
        j1_start = datetime(2015, 3, 2, 16, 0, 2)
        j1_end = datetime(2015, 3, 2, 16, 0, 3)
        j1_submit_ts = time.mktime(j1_submit.timetuple())
        j1_start_ts = time.mktime(j1_start.timetuple())
        j1_end_ts = time.mktime(j1_end.timetuple())

        node1 = Node('node1', self.cluster, 'partition1', 4, 4, 0)
        node2 = Node('node2', self.cluster, 'partition1', 4, 4, 0)

        a1_create = datetime(2010, 1, 1, 12, 0, 0)
        user1 = User('user1', 'firstname1', 'lastname1', 'department1')
        account1 = Account(user1, self.cluster, 1000, 1000, a1_create, None)

        domain1 = Domain('domain1', 'domain 1')
        sector1 = Sector(domain1, 'sector1', 'sector 1')
        project1 = Project(sector1, 'project1', 'description project 1')

        business1 = Business('business1', 'business description 1')

        MockMySQLdb.MY_REQS['get_jobs_after_batchid']['res'] = \
          [
            [ 0, 0, 1000, 1000, j1_submit_ts, j1_start_ts, j1_end_ts,
              2, 4, 'partition1', 'qos1', 1, 'node[1-2]', 'user1',
              'job1', 'project1:business1' ],
          ]

        self.app.arch.nodes = [ node1, node2 ]
        self.app.users.accounts = [ account1 ]
        self.app.projects.projects = [ project1 ]
        self.app.business.businesses = [ business1 ]
        self.importer.load()
        self.assertEquals(len(self.importer.jobs), 1)
        self.assertEquals(len(self.importer.runs), 2)
        job = self.importer.jobs[0]

        self.assertEquals(job.nbcpu, 4)
        self.assertEquals(job.state, 'RUNNING')
        self.assertEquals(job.name, 'job1')
        self.assertEquals(job.queue, 'partition1-qos1')
        self.assertEquals(job.account, account1)
        self.assertEquals(job.project, project1)
        self.assertEquals(job.business, business1)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    @mock.patch("%s.JobImporterSlurm.get_jobs_after_batchid" % (module))
    def test_load_search_batchid(self, mock_get_jobs):
        """JobImporterSlurm.load() must search jobs after correct batch_id."""

        MockPg2.PG_REQS['get_batchid_oldest_unfinished']['res'] = [ [ 2 ] ]
        MockPg2.PG_REQS['get_batchid_last']['res'] = [ [ 3 ] ]

        self.importer.load()
        mock_get_jobs.assert_called_with(2)

        # None unfinished job, search must be done with batch_id of lasti job.
        MockPg2.PG_REQS['get_batchid_oldest_unfinished']['res'] = [ ]
        MockPg2.PG_REQS['get_batchid_last']['res'] = [ [ 4 ] ]

        self.importer.load()
        mock_get_jobs.assert_called_with(4)

        # No job in DB: search starting -1.
        MockPg2.PG_REQS['get_batchid_oldest_unfinished']['res'] = [ ]
        MockPg2.PG_REQS['get_batchid_last']['res'] = [ ]

        self.importer.load()
        mock_get_jobs.assert_called_with(-1)

loadtestcase(TestsJobImporterSlurm)
