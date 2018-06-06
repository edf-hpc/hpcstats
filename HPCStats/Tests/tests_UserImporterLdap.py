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
from datetime import date
import base64
from StringIO import StringIO

from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Model.Cluster import Cluster
from HPCStats.Importer.Users.UserImporterLdap import UserImporterLdap
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Utils import decypher
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MockPg2 import init_reqs, mock_psycopg2
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockLdap import mock_ldap, fill_ldap_users
import HPCStats.Tests.Mocks.MockLdap as MockLdap # for LDAP_REQS
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Mocks.Conf import MockConf
from HPCStats.Tests.Mocks.App import MockApp
from HPCStats.Tests.Mocks.Utils import mock_open

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
}

module = 'HPCStats.Importer.Users.UserImporterLdap'

class TestsUserImporterLdap(HPCStatsTestCase):

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
        self.importer = UserImporterLdap(self.app,
                                         self.db,
                                         self.conf,
                                         self.cluster)
        init_reqs()

    def test_init(self):
        """UserImporterLdap.__init__() initializes w/o error
        """
        pass


    @mock.patch("%s.ldap" % (module), mock_ldap())
    @mock.patch("%s.os.path.isfile" % module)
    def test_check_groups_alias_file(self, m_isfile):
        """UserImporterLdap.check() should raise HPCStatsSourceError if
           groups_alias_file does not exist
        """

        # define file path to run the isfile check
        self.importer.groups_alias_file = 'test'

        # if file exist, everything is OK
        m_isfile.return_value = True
        self.importer.check()

        # if file does not exist, must raise HPCStatsSourceError
        m_isfile.return_value = False
        self.assertRaisesRegexp(
               HPCStatsSourceError,
               "Groups alias file test does not exist",
               self.importer.check)


    def test_load_groups_alias(self):
        """UserImporterLdap.load_groups_alias() tests
        """

        self.importer.groups_alias_file = 'test'

        # tests valid content
        aliases = "testAlong testA\n" \
                  "testBlong testB\n"

        m_open = mock_open(data=StringIO(aliases))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.importer.load_groups_alias()

        self.assertEquals(self.importer.groups_alias,
                          {'testAlong': 'testA',
                           'testBlong': 'testB'})

        # tests various invalid content
        wrong_aliases = ["testAlong", "testBlong testB fail\n",
                         "test:fail", "test;epic"]
        for wrong_alias in wrong_aliases:
            m_open = mock_open(data=StringIO(wrong_alias))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.assertRaisesRegexp(
                    HPCStatsSourceError,
                    "Malformed line in alias file test",
                    self.importer.load_groups_alias)


    @mock.patch("%s.ldap" % (module), mock_ldap())
    def test_load_simple(self):
        """UserImporterLdap.load() should work with simple data from LDAP.
        """

        users = [ 'login1', 'login2', 'login3' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        MockPg2.PG_REQS['get_unclosed_accounts'].set_assoc (
          params=( 0, ),
          result=[ ]
        )

        self.importer.load()
        self.assertEquals(len(self.importer.users), 3)
        self.assertEquals(len(self.importer.accounts), 3)

    @mock.patch("%s.ldap" % (module), mock_ldap())
    def test_load_simple2(self):
        """UserImporterLdap.load() should work with simple data from LDAP and
           HPCStatsDB.
        """

        users = [ 'login1', 'login2', 'login3' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        creation_user4 = datetime(2015, 3, 2, 16, 0, 1)
        MockPg2.PG_REQS['get_unclosed_accounts'].set_assoc(
          params=( 0, ),
          result=[ [ 0, 'login4', 'name_user4', 'firstname_user4',
                     'department_user4', 0, 0, creation_user4 ] ]
          )

        self.importer.load()
        self.assertEquals(len(self.importer.users), 4)
        self.assertEquals(len(self.importer.accounts), 4)


    @mock.patch("%s.ldap" % (module), mock_ldap())
    def test_load_user_no_dp_group(self):
        """UserImporterLdap.load() should work with user having no secondary group.
        """

        user = 'login1'
        fill_ldap_users(CONFIG['testcluster/ldap'], [user])
        # remove secondary group result for login1
        MockLdap.LDAP_REQS['secondary_groups_login1']['res'] = []

        # set the cn result of the prim_group LDAP query
        primary_group = 'primgrouptest'
        MockLdap.LDAP_REQS['prim_group_0']['res'][0][1]['cn'][0] = primary_group

        MockPg2.PG_REQS['get_unclosed_accounts'].set_assoc (
          params=( 0, ),
          result=[ ]
        )

        # test the user department has been computed based on its primary group
        self.importer.load()
        self.assertEquals(self.importer.users[0].department,
                          primary_group+'-unknown')

        # test with alternative default subdir
        subdir = 'testA'
        self.importer.default_subdir = subdir
        self.importer.load()
        self.assertEquals(self.importer.users[0].department,
                          primary_group+'-'+subdir)

        # test with alias
        primary_group_complicated = 'primgrouptestcomplicated'
        MockLdap.LDAP_REQS['prim_group_0']['res'][0][1]['cn'][0] = \
            primary_group_complicated
        self.importer.groups_alias = \
            { primary_group_complicated: primary_group }
        self.importer.load()
        self.assertEquals(self.importer.users[0].department,
                          primary_group+'-'+subdir)

        # test without primary group -> department must be None
        MockLdap.LDAP_REQS['prim_group_0']['res'] = {}
        self.importer.load()
        self.assertEquals(self.importer.users[0].department, None)

        # test with multiple primary groups -> must raise HPCStatsSourceError
        primary_group_complicated = 'primgrouptestcomplicated'
        MockLdap.LDAP_REQS['prim_group_0']['res'] = [ 'result1', 'result2' ]
        self.assertRaisesRegexp(
            HPCStatsSourceError,
            "too much results .%d. found for user %s primary group %d in " \
            "base %s" % (2, user, 0, self.importer.ldap_dn_groups),
            self.importer.load)


    @mock.patch("%s.ldap" % (module), mock_ldap())
    @mock.patch("%s.User.save" % (module))
    @mock.patch("%s.Account.save" % (module))
    def test_load_update_new_user_other_accounts(self, m_account_save, m_user_save):
        """UserImporterLdap.update() create new user/account found in LDAP
           and not found in HPCStatsDB with a creation date equals to today
           because there are already existing accounts.
        """

        users = [ 'login1' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        MockPg2.PG_REQS['get_unclosed_accounts'].set_assoc(
          params=( self.cluster.cluster_id, ),
          result=[ ]
          )
        MockPg2.PG_REQS['nb_existing_accounts'].set_assoc(
          params=( self.cluster.cluster_id, ),
          result=[ [ 0 ], [ 1 ] ]
          )

        self.importer.load()
        self.importer.update()
        self.assertEquals(self.importer.accounts[0].creation_date, date.today())
        m_user_save.assert_called_with(self.db)
        m_account_save.assert_called_with(self.db)

    @mock.patch("%s.ldap" % (module), mock_ldap())
    @mock.patch("%s.User.save" % (module))
    @mock.patch("%s.Account.save" % (module))
    def test_load_update_new_user_no_account(self, m_account_save, m_user_save):
        """UserImporterLdap.update() save new user/account found in LDAP
           and not found in HPCStatsDB with a creation date equals to epoch
           because there is none existing accounts
        """

        users = [ 'login1' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        self.importer.load()
        self.importer.update()
        self.assertEquals(self.importer.accounts[0].creation_date, date(1970, 1, 1))
        m_user_save.assert_called_with(self.db)
        m_account_save.assert_called_with(self.db)

    @mock.patch("%s.ldap" % (module), mock_ldap())
    @mock.patch("%s.Account.update" % (module))
    def test_load_update_close_account(self, m_account_update):
        """UserImporterLdap.update() close account found as unclosed in
           HPCStatsDB and not found in LDAP.
        """

        users = [ ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        creation_user2 = datetime(2015, 3, 2, 16, 0, 1)

        MockPg2.PG_REQS['get_unclosed_accounts'].set_assoc(
          params=( self.cluster.cluster_id, ),
          result=[ [ 2, 'login2', 'name_user2', 'firstname_user2',
                     'department_user2', 0, 0, creation_user2 ] ]
          )

        self.importer.load()
        self.importer.update()
        self.assertEquals(self.importer.accounts[0].deletion_date, date.today())
        m_account_update.assert_called_with(self.db)

    @mock.patch("%s.ldap" % (module), mock_ldap())
    @mock.patch("%s.User.update" % (module))
    @mock.patch("%s.Account.save" % (module))
    def test_load_update_user_wo_account(self, m_account_save, m_user_update):
        """UserImporterLdap.update() create account and update user found in
           LDAP and in HPCStatsDB but w/o account on the cluster.
        """

        users = [ 'login3' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        user3_id = 3

        MockPg2.PG_REQS['find_user'].set_assoc(
          params=( 'login3', ),
          result=[ [ user3_id ] ]
          )
        MockPg2.PG_REQS['existing_account'].set_assoc(
          params=( user3_id, self.cluster.cluster_id, ),
          result=[ ]
          )

        self.importer.load()
        self.importer.update()
        m_user_update.assert_called_with(self.db)
        m_account_save.assert_called_with(self.db)

    @mock.patch("%s.ldap" % (module), mock_ldap())
    @mock.patch("%s.User.update" % (module))
    @mock.patch("%s.Account.update" % (module))
    def test_load_update_user_w_account(self, m_account_update, m_user_update):
        """UserImporterLdap.update() update user found in LDAP and in HPCStatsDB
           with an unclosed account on the cluster.
        """

        users = [ 'login4' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        creation_user4 = datetime(2015, 3, 2, 16, 0, 1)
        user4_id = 4
        MockPg2.PG_REQS['find_user'].set_assoc(
          params=( 'login4', ),
          result=[ [ user4_id ] ]
          )
        MockPg2.PG_REQS['existing_account'].set_assoc(
          params=( user4_id, self.cluster.cluster_id, ),
          result=[ [ 0 ] ]
          )
        MockPg2.PG_REQS['load_account'].set_assoc(
          params=( user4_id, self.cluster.cluster_id, ),
          result=[ [ 0, 0, creation_user4, None ] ]
        )

        self.importer.load()
        self.importer.update()
        m_user_update.assert_called_with(self.db)
        # ensure Account.update() is not called
        self.assertRaises(AssertionError,
                          m_account_update.assert_called_with,
                          self.db,
                          None)

    @mock.patch("%s.ldap" % (module), mock_ldap())
    @mock.patch("%s.User.update" % (module))
    @mock.patch("%s.Account.update" % (module))
    def test_load_update_user_closed_account(self, m_account_update, m_user_update):
        """UserImporterLdap.update() update user found in LDAP and in HPCStatsDB
           with a closed account on the cluster.
        """
        users = [ 'login5' ]
        fill_ldap_users(CONFIG['testcluster/ldap'], users)

        user5_creation = datetime(2015, 3, 2, 16, 0, 1)
        user5_deletion = datetime(2015, 3, 2, 16, 0, 1)
        user5_id = 5
        MockPg2.PG_REQS['find_user'].set_assoc(
          params=( 'login5', ),
          result=[ [ user5_id ] ]
          )
        MockPg2.PG_REQS['existing_account'].set_assoc(
          params=( user5_id, self.cluster.cluster_id, ),
          result=[ [ 0 ] ]
          )
        MockPg2.PG_REQS['load_account'].set_assoc(
          params=( user5_id, self.cluster.cluster_id, ),
          result=[ [ 0, 0, user5_creation, user5_deletion ] ]
        )

        self.importer.load()
        self.importer.update()
        self.assertEquals(self.importer.accounts[0].deletion_date, None)
        m_user_update.assert_called_with(self.db)
        m_account_update.assert_called_with(self.db)

if __name__ == '__main__':

    loadtestcase(TestsUserImporterLdap)
