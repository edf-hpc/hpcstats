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
from HPCStats.CLI.HPCStatsModifier import HPCStatsModifier
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MockPg2 import init_reqs, mock_psycopg2
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS

CONFIG = {
  'clusters': {
    'clusters': 'testcluster,testcluster2',
  },
  'hpcstatsdb': {
    'hostname': 'test_hostname',
    'port':     'test_port',
    'dbname':   'test_name',
    'user':     'test_user',
    'password': 'test_password',
  },
  'globals': {
    'projects': 'csv',
  },
  'projects': {
    'file': 'fake_project_file',
  },
  'testcluster/slurm': {
    'host': 'dbhost',
    'port': 3128,
    'name': 'dbname',
    'user': 'dbuser',
    'password': 'dbpassword'
  },
}

class TestsHPCStatModifier(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'testcluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG.copy()
        init_reqs()

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_set_business_desc(self):
        """HPCStatsModifier.run() run w/o problem to set business code
           description.
        """
        params = { 'business': 'B1',
                   'project': None,
                   'set_description': 'B1 description',
                   'set_domain': None,
                   'new_domain': None,
                   'domain_name': None }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['existing_business'].set_assoc(
          params=( 'B1', ),
          result=[ [ 'B1' ] ]
          )
        self.modifier.run()

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_set_business_desc_inexisting_business(self):
        """HPCStatsModifier.run() raises exception when setting description
           of an inexisting business code.
        """
        params = { 'business': 'B1',
                   'project': None,
                   'set_description': 'B1 description',
                   'set_domain': None,
                   'new_domain': None,
                   'domain_name': None }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['existing_business'].set_assoc(
          params=( 'B1', ),
          result=[ ]
          )
        self.assertRaisesRegexp(HPCStatsRuntimeError,
                                "unable to find business code B1 in database",
                                self.modifier.run)

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_set_project_desc(self):
        """HPCStatsModifier.run() run w/o problem to set project
           description.
        """
        params = { 'business': None,
                   'project': 'P1',
                   'set_description': 'P1 description',
                   'set_domain': None,
                   'new_domain': None,
                   'domain_name': None }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['find_project'].set_assoc(
          params=( 'P1', ),
          result=[ [ 1 ] ]
          )
        MockPg2.PG_REQS['load_project'].set_assoc(
          params=( 1, ),
          result=[ [ 'P1', 'P1 old description', 'D1' ] ]
          )
        self.modifier.run()

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_set_project_desc_inexisting_project(self):
        """HPCStatsModifier.run() raises exception when setting a description
           of an inexisting project.
        """
        params = { 'business': None,
                   'project': 'P1',
                   'set_description': 'P1 description',
                   'set_domain': None,
                   'new_domain': None,
                   'domain_name': None }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['find_project'].set_assoc(
          params=( 'P1', ),
          result=[ ]
          )
        self.assertRaisesRegexp(HPCStatsRuntimeError,
                                "unable to find project P1 in database",
                                self.modifier.run)

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_set_project_domain(self):
        """HPCStatsModifier.run() run w/o problem to set project domain.
        """
        params = { 'business': None,
                   'project': 'P1',
                   'set_description': None,
                   'set_domain': 'D1',
                   'new_domain': None,
                   'domain_name': None }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['find_project'].set_assoc(
          params=( 'P1', ),
          result=[ [ 1 ] ]
          )
        MockPg2.PG_REQS['load_project'].set_assoc(
          params=( 1, ),
          result=[ [ 'P1', 'P1 description', 'D0' ] ]
          )
        MockPg2.PG_REQS['exist_domain'].set_assoc(
          params=( 'D1', ),
          result=[ [ 'D1' ] ]
          )
        self.modifier.run()

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_set_project_domain_inexisting_project(self):
        """HPCStatsModifier.run() raises exceptions when setting project domain
           on an inexisting project
        """
        params = { 'business': None,
                   'project': 'P1',
                   'set_description': None,
                   'set_domain': 'D1',
                   'new_domain': None,
                   'domain_name': None }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        # HPCStatsModifier.set_project_domain() searches for the domain first
        # so we need to fake domain presence before checking for project.
        MockPg2.PG_REQS['exist_domain'].set_assoc(
          params=( 'D1', ),
          result=[ [ 'D1' ] ]
          )
        MockPg2.PG_REQS['find_project'].set_assoc(
          params=( 'P1', ),
          result=[ ]
          )
        self.assertRaisesRegexp(HPCStatsRuntimeError,
                                "unable to find project P1 in database",
                                self.modifier.run)

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_set_project_domain_inexisting_domain(self):
        """HPCStatsModifier.run() raises exceptions when setting project domain
           with inexisting domain
        """
        params = { 'business': None,
                   'project': 'P1',
                   'set_description': None,
                   'set_domain': 'D1',
                   'new_domain': None,
                   'domain_name': None }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['exist_domain'].set_assoc(
          params=( 'D1', ),
          result=[ ]
          )
        self.assertRaisesRegexp(HPCStatsRuntimeError,
                                "unable to find domain D1 in database",
                                self.modifier.run)

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_create_domain(self):
        """HPCStatsModifier.run() run w/o problem to create a new domain.
        """
        params = { 'business': None,
                   'project': None,
                   'set_description': None,
                   'set_domain': None,
                   'new_domain': 'D1',
                   'domain_name': 'D1 description' }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['exist_domain'].set_assoc(
          params=( 'D1', ),
          result=[ ]
          )
        self.modifier.run()

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def test_run_create_domain_already_existing(self):
        """HPCStatsModifier.run() raises exception when creating a domain that
           already exists.
        """
        params = { 'business': None,
                   'project': None,
                   'set_description': None,
                   'set_domain': None,
                   'new_domain': 'D1',
                   'domain_name': 'D1 description' }
        self.modifier = HPCStatsModifier(self.conf, self.cluster, params)

        MockPg2.PG_REQS['exist_domain'].set_assoc(
          params=( 'D1', ),
          result=[ [ 'D1' ] ]
          )
        self.assertRaisesRegexp(HPCStatsRuntimeError,
                                "domain D1 already exists in database",
                                self.modifier.run)
if __name__ == '__main__':

    loadtestcase(TestsHPCStatsModifier)
