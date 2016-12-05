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

from datetime import datetime, date
import time
import mock
import base64
import logging

from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Model.Cluster import Cluster
from HPCStats.Importer.Users.UserImporterLdapSlurm import UserImporterLdapSlurm
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Utils import decypher
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Log.Logger import HPCStatsLogger
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MockPg2 import init_reqs, mock_psycopg2
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockLdap import mock_ldap, fill_ldap_users
import HPCStats.Tests.Mocks.MockLdap as MockLdap # for LDAP_REQS
from HPCStats.Tests.Mocks.MySQLdb import mock_mysqldb
import HPCStats.Tests.Mocks.MySQLdb as MockMySQLdb # for MY_REQS
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
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
  'testcluster/ldap': {
    'url': 'test_url',
    'basedn': 'test_basedn',
    'dn': 'test_dn',
    'phash': base64.b64encode(decypher(base64.b64encode('test_passwd'))),
    'groups': 'test_groupA,test_groupB',
    'group_dpt_search': 'test_group_dpt_search',
    'group_dpt_regexp': 'cn=(.+)-dp-(.+),ou.*',
  },
  'testcluster/slurm': {
    'host': 'dbhost',
    'port': 3128,
    'name': 'dbname',
    'user': 'dbuser',
    'password': 'dbpassword'
  }
}

MockMySQLdb.MY_REQS['get_users'] = {
  'req': "SELECT DISTINCT user " \
          "FROM .*_assoc_table",
  'res': [],
}

p_module = 'HPCStats.Importer.Users.UserImporterLdap'
module = 'HPCStats.Importer.Users.UserImporterLdapSlurm'

# set logger here to make sure HPCStatsLogger.warn() is used
logging.setLoggerClass(HPCStatsLogger)

class TestsUserImporterLdapSlurm(HPCStatsTestCase):

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def setUp(self):
        self.filename = 'fake'
        self.cluster = Cluster('testcluster')
        self.cluster.cluster_id = 0
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG.copy()
        self.db = HPCStatsDB(self.conf)
        self.db.bind()
        self.app = MockApp(self.db, self.conf, self.cluster)
        self.importer = UserImporterLdapSlurm(self.app,
                                              self.db,
                                              self.conf,
                                              self.cluster)
        # Disable strict_user_membership to avoid exception when user found
        # in Slurm and not in LDAP then.
        self.importer.strict_user_membership = False
        init_reqs()

    def test_init(self):
        """UserImporterLdap.__init__() initializes w/o error
        """
        pass

    @mock.patch("%s.ldap" % (p_module), mock_ldap())
    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_user_no_ldap(self):
        """UserImporterLdapSlurm.load() should not user from Slurm if not found
           in LDAP.
        """

        users = [ ]
        users_no_group = [ ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users, users_no_group)

        MockMySQLdb.MY_REQS['get_users']['res'] = \
        [ [ 'login1' ] ]

        self.importer.load()
        self.assertEquals(len(self.importer.users), 0)

    @mock.patch("%s.ldap" % (p_module), mock_ldap())
    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_user_ok_ldap(self):
        """UserImporterLdapSlurm.load() should load user from Slurm if also
           found in LDAP.
        """

        users = [ ]
        users_no_group = [ 'login1' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users, users_no_group)

        MockMySQLdb.MY_REQS['get_users']['res'] = \
        [ [ 'login1' ] ]

        self.importer.load()
        self.assertEquals(len(self.importer.users), 1)
        self.assertEquals(len(self.importer.users_acct_ldap), 0)
        self.assertEquals(len(self.importer.users_acct_slurm), 1)

    @mock.patch("%s.ldap" % (p_module), mock_ldap())
    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_user_in_group(self):
        """UserImporterLdapSlurm.load() should not load user from Slurm if
           already loaded because it is member of cluster group.
        """

        users = [ 'login1' ]
        users_no_group = [ ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users, users_no_group)

        MockMySQLdb.MY_REQS['get_users']['res'] = \
        [ [ 'login1' ] ]

        self.importer.load()
        self.assertEquals(len(self.importer.users), 1)
        self.assertEquals(len(self.importer.users_acct_ldap), 1)
        self.assertEquals(len(self.importer.users_acct_slurm), 0)


    @mock.patch("%s.ldap" % (p_module), mock_ldap())
    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    def test_load_no_redundancy(self):
        """UserImporterLdapSlurm.load() should manage redundancy with LDAP.
        """

        users = [ 'login1', 'login2', 'login3' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        MockMySQLdb.MY_REQS['get_users']['res'] = \
        [ [ 'login1' ], [ 'login2' ], [ 'login4' ] ]

        self.importer.load()
        self.assertEquals(len(self.importer.users), 3)
        self.assertEquals(len(self.importer.accounts), 3)

    @mock.patch("%s.ldap" % (p_module), mock_ldap())
    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    @mock.patch("%s.User.save" % (module))
    @mock.patch("%s.Account.save" % (module))
    def test_update_new_user(self, m_account_save, m_user_save):
        """UserImporterLdapSlurm.slurm() should save the user and the account if
           not existing in DB
        """

        users = [ ]
        users_no_group = [ 'login1' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users, users_no_group)

        MockMySQLdb.MY_REQS['get_users']['res'] = \
        [ [ 'login1' ] ]

        user1_id = 1

        MockPg2.PG_REQS['find_user'].set_assoc(
          params=( 'login1', ),
          result=[ ]
          )
        MockPg2.PG_REQS['existing_account'].set_assoc(
          params=( user1_id, self.cluster.cluster_id, ),
          result=[ ]
          )

        self.importer.load()
        self.importer.update()
        self.assertEquals(self.importer.accounts[0].creation_date,
                          date(1970, 1, 1))
        self.assertEquals(self.importer.accounts[0].deletion_date,
                          date(1970, 1, 1))
        m_user_save.assert_called_with(self.db)
        m_account_save.assert_called_with(self.db)

    @mock.patch("%s.ldap" % (p_module), mock_ldap())
    @mock.patch("%s.MySQLdb" % (module), mock_mysqldb())
    @mock.patch("%s.User.update" % (module))
    @mock.patch("%s.Account.update" % (module))
    def test_update_user_account_exist(self, m_account_update, m_user_update):
        """UserImporterLdapSlurm.slurm() should update the user and do not
           touch the account if they already exist in DB
        """

        users = [ ]
        users_no_group = [ 'login1' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users, users_no_group)

        MockMySQLdb.MY_REQS['get_users']['res'] = \
        [ [ 'login1' ] ]

        user1_id = 1

        MockPg2.PG_REQS['find_user'].set_assoc(
          params=( 'login1', ),
          result=[ [ user1_id ] ]
          )
        MockPg2.PG_REQS['existing_account'].set_assoc(
          params=( user1_id, self.cluster.cluster_id, ),
          result=[ [ 0 ] ]
          )

        self.importer.load()
        self.importer.update()
        m_user_update.assert_called_with(self.db)
        # ensure Account.update() is not called
        self.assertRaises(AssertionError,
                          m_account_update.assert_called_with,
                          self.db,
                          None)

if __name__ == '__main__':

    loadtestcase(TestsUserImporterLdapSlurm)
