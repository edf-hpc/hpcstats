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
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Business import Business
from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm
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
    'password': 'dbpassword'
  }
}

MockMySQLdb.MY_REQS['get_jobs_after_batchid'] = {
  'req': "SELECT job_db_inx, " \
                "id_job, " \
                "id_user, " \
                "id_group, " \
                "time_submit, " \
                "time_start, " \
                "time_end, " \
                "timelimit, " \
                "nodes_alloc, " \
                "(cpus_alloc|tres_alloc), " \
                "job.partition, " \
                "qos.name AS qos, " \
                "job.account, " \
                "state, " \
                "nodelist, " \
                "assoc.user, " \
                "job_name, " \
                "wckey " \
          "FROM .*_job_table job, "\
               ".*_assoc_table assoc, " \
               "qos_table qos " \
         "WHERE job_db_inx >= %s " \
           "AND assoc.id_assoc = job.id_assoc " \
           "AND qos.id = job.id_qos " \
      "ORDER BY job_db_inx",
  'res': [],
}

MockMySQLdb.MY_REQS['get_jobs_after_batchid_w_parts'] = {
  'req': "SELECT job_db_inx, " \
                "id_job, " \
                "id_user, " \
                "id_group, " \
                "time_submit, " \
                "time_start, " \
                "time_end, " \
                "timelimit, " \
                "nodes_alloc, " \
                "(cpus_alloc|tres_alloc), " \
                "job.partition, " \
                "qos.name AS qos, " \
                "job.account, " \
                "state, " \
                "nodelist, " \
                "assoc.user, " \
                "job_name, " \
                "wckey " \
          "FROM .*_job_table job, "\
               ".*_assoc_table assoc, " \
               "qos_table qos " \
         "WHERE job_db_inx >= %s " \
           "AND job.partition IN (.*) " \
           "AND assoc.id_assoc = job.id_assoc " \
           "AND qos.id = job.id_qos " \
      "ORDER BY job_db_inx",
  'res': [],
}

MockMySQLdb.MY_REQS['job_table_cols'] = {
  'req': "SHOW COLUMNS FROM .*_job_table LIKE 'cpus_alloc'",
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
        init_reqs()

    def test_init(self):
        """JobImporterSlurm.__init__() initializes object with attributes
        """
        self.assertEquals(self.importer._dbhost,
                          self.conf.conf[self.cluster.name + '/slurm']['host'])

    def load_app(self):
        """Load App objects for JobImporterSlurm.load() normal operation."""
        j1_submit = datetime(2015, 3, 2, 16, 0, 1)
        j1_start = datetime(2015, 3, 2, 16, 0, 2)
        j1_end = datetime(2015, 3, 2, 16, 0, 3)
        j1_submit_ts = time.mktime(j1_submit.timetuple())
        j1_start_ts = time.mktime(j1_start.timetuple())
        j1_end_ts = time.mktime(j1_end.timetuple())

        node1 = Node('node1', self.cluster, 'model1', 'partition1', 4, 4, 0)
        node2 = Node('node2', self.cluster, 'model1', 'partition1', 4, 4, 0)

        a1_create = datetime(2010, 1, 1, 12, 0, 0)
        user1 = User('user1', 'firstname1', 'lastname1', 'department1')
        account1 = Account(user1, self.cluster, 1000, 1000, a1_create, None)

        domain1 = Domain('domain1', 'domain 1')
        project1 = Project(domain1, 'project1', 'description project 1')

        business1 = Business('business1', 'business description 1')

        self.app.arch.nodes = [ node1, node2 ]
        self.app.users.users = [ user1 ]
        self.app.users.accounts = [ account1 ]
        self.app.projects.projects = [ project1 ]
        self.app.business.businesses = [ business1 ]

        MockMySQLdb.MY_REQS['get_jobs_after_batchid']['res'] = \
          [
            [ 0, 0, 1000, 1000, j1_submit_ts, j1_start_ts, j1_end_ts, '03:59:59',
              2, '1=4', 'partition1', 'qos1', 'job_acct1', 1, 'node[1-2]',
              'user1', 'job1', 'project1:business1' ],
          ]
        MockMySQLdb.MY_REQS['get_jobs_after_batchid_w_parts']['res'] = \
          [
            [ 0, 0, 1000, 1000, j1_submit_ts, j1_start_ts, j1_end_ts, '03:59:59',
              2, '1=8', 'partition1', 'qos1', 'job_acct1', 1, 'node[1-2]',
              'user1', 'job2', 'project1:business1' ],
          ]

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_is_old_schema(self):
        """JobImporterSlurm._is_old_schema() should return True is SlurmDBD
           <15.08 is detected, False otherwise."""

        self.load_app()
        self.importer.connect_db()
        MockMySQLdb.MY_REQS['job_table_cols']['res'] = \
          [ [ 'cpus_alloc', ] , ]
        self.assertEquals(self.importer._is_old_schema(), True)

        MockMySQLdb.MY_REQS['job_table_cols']['res'] = []
        self.assertEquals(self.importer._is_old_schema(), False)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load(self):
        """JobImporterSlurm.load() works with simple data."""

        self.load_app()
        # make sure new-schema is used here
        MockMySQLdb.MY_REQS['job_table_cols']['res'] = [ ]

        self.importer.load()

        self.assertEquals(len(self.importer.jobs), 1)

        job = self.importer.jobs[0]

        self.assertEquals(job.nbcpu, 4)
        self.assertEquals(job.state, 'RUNNING')
        self.assertEquals(job.name, 'job1')
        self.assertEquals(job.queue, 'partition1-qos1')
        self.assertEquals(job.account, self.app.users.accounts[0])
        self.assertEquals(job.project, self.app.projects.projects[0])
        self.assertEquals(job.business, self.app.business.businesses[0])
        self.assertEquals(len(job.runs), 2)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_with_parts(self):
        """JobImporterSlurm.load() works with simple data."""

        self.load_app()
        self.importer.partitions = ['partition2']
        # make sure new-schema is used here
        MockMySQLdb.MY_REQS['job_table_cols']['res'] = [ ]

        self.importer.load()

        self.assertEquals(len(self.importer.jobs), 1)

        job = self.importer.jobs[0]

        self.assertEquals(job.nbcpu, 8)
        self.assertEquals(job.state, 'RUNNING')
        self.assertEquals(job.name, 'job2')
        self.assertEquals(job.queue, 'partition1-qos1')
        self.assertEquals(job.account, self.app.users.accounts[0])
        self.assertEquals(job.project, self.app.projects.projects[0])
        self.assertEquals(job.business, self.app.business.businesses[0])
        self.assertEquals(len(job.runs), 2)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_old_schema(self):
        """JobImporterSlurm.load() works with simple data from old SlurmDBD
           <15.08 schema."""

        self.load_app()

        MockMySQLdb.MY_REQS['job_table_cols']['res'] = \
          [ [ 'cpus_alloc', ] , ]
        # replace TRES '1=4' by cpus_alloc 4
        MockMySQLdb.MY_REQS['get_jobs_after_batchid']['res'][0][9] = 4

        self.importer.load()

        self.assertEquals(len(self.importer.jobs), 1)

        job = self.importer.jobs[0]

        self.assertEquals(job.nbcpu, 4)
        self.assertEquals(job.state, 'RUNNING')
        self.assertEquals(job.name, 'job1')
        self.assertEquals(job.queue, 'partition1-qos1')
        self.assertEquals(job.account, self.app.users.accounts[0])
        self.assertEquals(job.project, self.app.projects.projects[0])
        self.assertEquals(job.business, self.app.business.businesses[0])
        self.assertEquals(len(job.runs), 2)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    @mock.patch("%s.JobImporterSlurm.get_jobs_after_batchid" % (module))
    def test_load_search_batchid(self, mock_get_jobs):
        """JobImporterSlurm.load() must search jobs after correct batch_id."""

        MockPg2.PG_REQS['get_batchid_oldest_unfinished'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ [ 2 ] ]
        )
        MockPg2.PG_REQS['get_batchid_last'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ [ 3 ] ]
        )

        self.importer.load()
        mock_get_jobs.assert_called_with(2)

        # None unfinished job, search must be done with batch_id of lasti job.
        MockPg2.PG_REQS['get_batchid_oldest_unfinished'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ ]
        )
        MockPg2.PG_REQS['get_batchid_last'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ [ 4 ] ]
        )

        self.importer.load()
        mock_get_jobs.assert_called_with(4)

        # No job in DB: search starting -1.
        MockPg2.PG_REQS['get_batchid_oldest_unfinished'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ ]
        )
        MockPg2.PG_REQS['get_batchid_last'].set_assoc(
          params=( self.cluster.cluster_id ),
          result=[ ]
        )

        self.importer.load()
        mock_get_jobs.assert_called_with(-1)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_account_not_found(self):
        """JobImporterSlurm.load() raises exception when account not found"""

        self.load_app()
        self.app.users.accounts = [ ]

        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "account user1 not found in loaded account",
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_invalid_tres(self):
        """JobImporterSlurm.load() raises exception if invalid tres for a job
           is found"""

        self.load_app()

        MockMySQLdb.MY_REQS['get_jobs_after_batchid']['res'][0][9] = '0=0'
        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "unable to extract cpus_alloc from job tres",
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_invalid_wckey(self):
        """JobImporterSlurm.load() raises exception when format of wckey is
           invalid.
        """

        self.load_app()

        MockMySQLdb.MY_REQS['get_jobs_after_batchid']['res'][0][17] = 'fail'

        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "format of wckey fail is not valid",
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_project_not_found(self):
        """JobImporterSlurm.load() raises exception when project not found."""

        self.load_app()
        self.app.projects.projects = [ ]

        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "project project1 not found in loaded projects",
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_business_not_found(self):
        """JobImporterSlurm.load() raises exception when business not found."""

        self.load_app()
        self.app.business.businesses = [ ]

        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "business code business1 not found in loaded business codes",
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_invalid_nodelist(self):
        """JobImporterSlurm.load() raises exception when format of nodelist
           is invalid.
        """

        self.load_app()

        MockMySQLdb.MY_REQS['get_jobs_after_batchid']['res'][0][14] = \
          'nodelistfail[5-4]'

        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "could not parse nodeset nodelistfail\[5\-4\] for job 0",
               self.importer.load)

    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_node_not_found(self):
        """JobImporterSlurm.load() does not create runs when node not found."""

        self.load_app()
        self.app.arch.nodes = [ ]
        self.importer.load()
        job = self.importer.jobs[0]
        self.assertEquals(len(job.runs), 0)

    def test_job_partition(self):
        """JobImporterSlurm.job_partition() must return correct partition for
           based on job partition list and its nodelist.
        """

        # Only one element in job partition list: it must be returned whatever
        # the nodelist and ArchitectureImporter job partitions
        self.app.arch.partitions = { }
        result = self.importer.job_partition(0, 'partition2', 'node[1-100]')
        self.assertEquals(result, 'partition2')

        # Multiple elements but None nodelist: it must return arbitrary the
        # first partition
        self.app.arch.partitions = { }
        result = self.importer.job_partition(0, 'partition1,partition2', None)
        self.assertEquals(result, 'partition1')

        # Multiple elements in partition and defined nodelist: it must return
        # a corresponding partition loaded by ArchitectureImporter and
        # associated to a nodelist that fully intersects
        self.app.arch.partitions = { 'node[1-100]': [ 'partitionX', 'partition2'] }
        result = self.importer.job_partition(0, 'partition1,partition2', 'node[1-100]')
        self.assertEquals(result, 'partition2')

        self.app.arch.partitions = { 'node[1-99]': [ 'partition1' ],
                                     'node[1-100],bm[1-10]': [ 'partitionX', 'partition2' ] }
        result = self.importer.job_partition(0, 'partition1,partition2', 'node[1-100]')
        self.assertEquals(result, 'partition2')

if __name__ == '__main__':

    loadtestcase(TestsJobImporterSlurm)
