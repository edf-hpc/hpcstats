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
import base64

from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Model.Cluster import Cluster
from HPCStats.Importer.Users.UserImporterLdap import UserImporterLdap
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Utils import decypher
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MockPg2 import mock_psycopg2
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockLdap import mock_ldap
import HPCStats.Tests.Mocks.MockLdap as MockLdap # for PG_REQS
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
    'group': 'test_group',
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

    def test_init(self):
        """UserImporterLdap.__init__() initializes w/o error
        """
        pass

    @mock.patch("%s.ldap" % (module), mock_ldap())
    def test_load_simple(self):
        """UserImporterLdap.load() should work with simple data.
        """
        ldap_config = CONFIG['testcluster/ldap']

        users = [ 'login1', 'login2', 'login3' ]

        MockLdap.LDAP_REQS['get_group_members'] = {
          'req':
            ( "ou=groups,%s" % (ldap_config['basedn']),
              "(&(objectclass=posixGroup)(cn=%s))" % (ldap_config['group']) ),
          'res': [ ('dn_group1', { 'member': None } ) ],
        }
        # replace None with list of users
        MockLdap.LDAP_REQS['get_group_members']['res'][0][1]['member'] = \
          [ 'dn=%s,ou=people' % user for user in users ]

        for user in users: 
            MockLdap.LDAP_REQS["get_user_%s" % user] = {
              'req':
                ( "ou=people,%s" % (ldap_config['basedn']),
                  "uid=%s" % user ),
              'res': [ ( "dn_%s" % user,
                        { 'givenName': [ "given_name_%s" % user ],
                          'sn': [ "sn_%s" % user ],
                          'uidNumber': [ 0 ],
                          'gidNumber': [ 0 ], } ) ]
            }
            MockLdap.LDAP_REQS["secondary_groups_%s" % user] = {
              'req':
                ( "ou=groups,%s" % (ldap_config['basedn']),
                  "(&(|(member=uid=%s,ou=people,%s)(memberUid=%s))(cn=%s))"
                    % ( user,
                        ldap_config['basedn'],
                        user,
                        ldap_config['group_dpt_search'] ) ),
              'res': [ ( 'cn=dir1-dp-dpt1,ou=groups', dict() ) ]
            }
        self.importer.load()
        self.assertEquals(len(self.importer.users), 3)

loadtestcase(TestsUserImporterLdap)
