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
from HPCStats.Importer.BusinessCodes.BusinessCodeImporterCSV import BusinessCodeImporterCSV
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Model.Cluster import Cluster
from HPCStats.Model.Business import Business
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Mocks.Utils import mock_open
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockPg2 import mock_psycopg2, init_reqs
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase

CONFIG = {
  'hpcstatsdb': {
    'hostname': 'test_hostname',
    'port':     'test_port',
    'dbname':   'test_name',
    'user':     'test_user',
    'password': 'test_password',
  },
  'business': {
    'file': 'fake_project_file',
  },
}

module = "HPCStats.Importer.BusinessCodes.BusinessCodeImporterCSV"

class TestsBusinessCodeImporterCSVLoad(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = Cluster('testcluster')
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster.name)
        self.conf.conf = CONFIG
        self.app = None
        self.db = None
        self.importer = BusinessCodeImporterCSV(self.app, self.db, self.conf)
        init_reqs()

    def test_init(self):
        """ProjectImporterCSV.__init__() runs w/o problem
        """
        pass

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_1(self, m_isfile):
        """BusinessCodeImporterCSV.load() works with simple data
        """

        m_isfile.return_value = True

        csv = "code1;business description 1"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.importer.load()

        business = self.importer.businesses[0]
        self.assertEquals(business.code, 'code1')
        self.assertEquals(business.description, 'business description 1')

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_multiple_lines(self, m_isfile):
        """BusinessCodeImporterCSV.load() works with multiple lines
        """

        m_isfile.return_value = True

        csv = "code1;business description 1\n" \
              "code2;business description 2\n"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.importer.load()

        self.assertEquals(len(self.importer.businesses), 2)

        business1 = self.importer.businesses[0]
        business2 = self.importer.businesses[1]

        self.assertEquals(business1.code, 'code1')
        self.assertEquals(business1.description, 'business description 1')
        self.assertEquals(business2.code, 'code2')
        self.assertEquals(business2.description, 'business description 2')

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_invalid_line(self, m_isfile):
        """BusinessCodeImporterCSV.load() raise exception when a business code
           line in CSV file is invalid
        """

        m_isfile.return_value = True

        csvs = [ "line without separator",
                 "line;with;3_separators"]

        for csv in csvs:
            m_open = mock_open(data=StringIO(csv))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.assertRaisesRegexp(
                       HPCStatsSourceError,
                       "business line format in CSV is invalid",
                       self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_business_empty_code(self, m_isfile):
        """BusinessCodeImporterCSV.load() raise exception when business code is
           empty
        """

        m_isfile.return_value = True

        codes = [ '', " ", "      " ]
        for code in codes:
            csv = "%s;business description 1" % code

            m_open = mock_open(data=StringIO(csv))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.assertRaisesRegexp(
                       HPCStatsSourceError,
                       "business code in CSV is empty",
                       self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_business_empty_description(self, m_isfile):
        """BusinessCodeImporterCSV.load() set description to None when empty.
        """

        m_isfile.return_value = True

        descs = [ '', " ", "      " ]
        for desc in descs:
            csv = "code1;%s" % desc

            m_open = mock_open(data=StringIO(csv))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.importer.load()
                self.assertIsNone(self.importer.businesses[0].description)

class TestsBusinessCodeImporterCSVUpdate(HPCStatsTestCase):

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def setUp(self):
        self.filename = 'fake'
        self.cluster = Cluster('testcluster')
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster.name)
        self.conf.conf = CONFIG
        self.app = None
        self.db = HPCStatsDB(self.conf)
        self.db.bind()
        self.importer = BusinessCodeImporterCSV(self.app, self.db, self.conf)

    def test_update_not_exists(self):
        """ProjectImporterCSV.update() works when business code does not exist
        """
        business1 = Business('code1', 'business description 1')
        self.importer.businesses = [ business1 ]
        self.importer.update()

    @mock.patch("%s.Business.save" % (module))
    def test_update_not_exists_with_mock(self, mock_save):
        """ProjectImporterCSV.update() call Business.save() when business code
           does not exist
        """

        business1 = Business('code1', 'business description 1')

        MockPg2.PG_REQS['existing_business'].set_assoc(
          params=( business1.code, ),
          result=[ ]
        )

        self.importer.businesses = [ business1 ]
        self.importer.update()
        mock_save.assert_called_with(self.db)

    def test_update_exists(self):
        """ProjectImporterCSV.update() works when business code exists
        """

        business1 = Business('code1', 'business description 1')

        MockPg2.PG_REQS['existing_business'].set_assoc(
          params=( business1.code, ),
          result=[ [ 'code1' ] ]
        )

        self.importer.businesses = [ business1 ]
        self.importer.update()

    @mock.patch("%s.Business.update" % (module))
    def test_update_exists_with_mock(self, mock_update):
        """ProjectImporterCSV.update() call Business.update() when business
           code exists
        """
        business1 = Business('code1', 'business description 1')

        MockPg2.PG_REQS['existing_business'].set_assoc(
          params=( business1.code, ),
          result=[ [ 'code1' ] ]
        )

        self.importer.businesses = [ business1 ]
        self.importer.update()
        mock_update.assert_called_with(self.db)

if __name__ == '__main__':

    loadtestcase(TestsBusinessCodeImporterCSVLoad)
    loadtestcase(TestsBusinessCodeImporterCSVUpdate)
