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

# the requests and results are then defined by tests themselves.
LDAP_REQS = dict()

class MockLdap(object):

    """Class with static methods to mock all used functions in psycogp2
       module
    """

    def __init__(self):
        pass

    @staticmethod
    def set_option(opt1, opt2):
        """Mock of ldap.set_options()"""
        pass

    @staticmethod
    def initialize(url):
        return MockLdapConn()

class MockLdapConn(object):

    def __init__(self):
        pass

    def simple_bind(self, dn, passwd):
        pass

    def search_s(self, req_dn, flag, req_search, attrs):

        for req in LDAP_REQS.keys():
            (dn, search) =  LDAP_REQS[req]['req']
            print("req   : %s/%s" % (dn, search))
            print("params: %s/%s" % (req_dn, req_search))
            if dn == req_dn and search == req_search:
                print("match %s!" % (req))
                return LDAP_REQS[req]['res']

def mock_ldap():

    ldap_m = mock.Mock()
    ldap_m.initialize.side_effect = MockLdap.initialize
    return ldap_m


def fill_ldap_users(ldap_config, users):

    LDAP_REQS['get_group_members'] = {
      'req':
        ( "ou=groups,%s" % (ldap_config['basedn']),
          "(&(objectclass=posixGroup)(cn=%s))" % (ldap_config['group']) ),
      'res': [ ('dn_group1', { 'member': None } ) ],
    }
    # replace None with list of users
    LDAP_REQS['get_group_members']['res'][0][1]['member'] = \
      [ 'dn=%s,ou=people' % user for user in users ]

    for user in users:
        LDAP_REQS["get_user_%s" % user] = {
          'req':
            ( "ou=people,%s" % (ldap_config['basedn']),
              "uid=%s" % user ),
          'res': [ ( "dn_%s" % user,

                    { 'givenName': [ "given_name_%s" % user ],
                      'sn': [ "sn_%s" % user ],
                      'uidNumber': [ 0 ],
                      'gidNumber': [ 0 ], } ) ]
        }
        LDAP_REQS["secondary_groups_%s" % user] = {
          'req':
            ( "ou=groups,%s" % (ldap_config['basedn']),
              "(&(|(member=uid=%s,ou=people,%s)(memberUid=%s))(cn=%s))"
                % ( user,
                    ldap_config['basedn'],
                    user,
                    ldap_config['group_dpt_search'] ) ),
          'res': [ ( 'cn=dir1-dp-dpt1,ou=groups', dict() ) ]
        }
