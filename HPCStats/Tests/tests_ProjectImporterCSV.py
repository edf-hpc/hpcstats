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
from HPCStats.Importer.Projects.ProjectImporterCSV import ProjectImporterCSV
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Mocks.Utils import mock_open
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase

CONFIG = {
           'hpcstatsdb': {
             'hostname': 'test_hostname',
             'port':     'test_port',
             'dbname':   'test_name',
             'user':     'test_user',
             'password': 'test_password',
           },
           'projects': {
             'file': 'fake_project_file',
           },
         }

module = "HPCStats.Importer.Projects.ProjectImporterCSV"

class TestsProjectImporterCSV(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'testcluster'
        MockConfigParser.conf = CONFIG
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.app = None
        self.db = HPCStatsDB(self.conf)
        self.importer = ProjectImporterCSV(self.app, self.db, self.conf)

    def test_init(self):
        """ProjectImporterCSV.__init__() runs w/o problem
        """
        pass

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_1(self, m_isfile):
        """ProjectImporterCSV.load() works with simple data
        """

        m_isfile.return_value = True

        csv = "code1;project description 1;" \
              "[dom1] domain name 1;[sect1] sector name 1"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.importer.load()

        project = self.importer.projects[0]
        self.assertEquals(project.code, 'code1')
        self.assertEquals(project.description, 'project description 1')
        self.assertEquals(project.sector.key, 'sect1')
        self.assertEquals(project.sector.name, 'sector name 1')
        self.assertEquals(project.sector.domain.key, 'dom1')
        self.assertEquals(project.sector.domain.name, 'domain name 1')

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_multiple_lines(self, m_isfile):
        """ProjectImporterCSV.load() works with multiple lines
        """

        m_isfile.return_value = True

        csv = "code1;project description 1;" \
              "[dom1] domain name 1;[sect1] sector name 1\n" \
              "code2;project description 2;" \
              "[dom2] domain name 2;[sect2] sector name 2\n"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.importer.load()

        self.assertEquals(len(self.importer.projects), 2)

        project1 = self.importer.projects[0]
        project2 = self.importer.projects[1]

        self.assertEquals(project1.code, 'code1')
        self.assertEquals(project2.description, 'project description 2')
        self.assertEquals(project1.sector.key, 'sect1')
        self.assertEquals(project2.sector.name, 'sector name 2')
        self.assertEquals(project1.sector.domain.key, 'dom1')
        self.assertEquals(project2.sector.domain.name, 'domain name 2')

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_domain_invalid(self, m_isfile):
        """ProjectImporterCSV.load() raise exception when domain format is
           invalid
        """

        m_isfile.return_value = True

        csv = "code1;project description 1;" \
              "domain name 1;[sect1] sector name 1"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.assertRaisesRegexp(
                   HPCStatsSourceError,
                   "Project CSV code1 domain format is invalid",
                   self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_domain_empty_key(self, m_isfile):
        """ProjectImporterCSV.load() raise exception when domain key is empty
        """

        m_isfile.return_value = True

        keys = [ '', " ", "      " ]
        for key in keys:
            csv = "code1;project description 1;" \
                  "[%s] domain name 1;[sect1] sector name 1" % (key)

            m_open = mock_open(data=StringIO(csv))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.assertRaisesRegexp(
                       HPCStatsSourceError,
                       "Project CSV code1 domain key is empty",
                       self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_domain_empty_name(self, m_isfile):
        """ProjectImporterCSV.load() raise exception when domain name is empty
        """

        m_isfile.return_value = True

        names = [ '', " ", "      " ]
        for name in names:
            csv = "code1;project description 1;" \
                  "[dom1] %s;[sect1] sector name 1" % (name)

            m_open = mock_open(data=StringIO(csv))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.assertRaisesRegexp(
                       HPCStatsSourceError,
                       "Project CSV code1 domain name is empty",
                       self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_sector_invalid(self, m_isfile):
        """ProjectImporterCSV.load() raise exception when sector format is
           invalid
        """

        m_isfile.return_value = True

        csv = "code1;project description 1;" \
              "[dom1] domain name 1;sector name 1"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.assertRaisesRegexp(
                   HPCStatsSourceError,
                   "Project CSV code1 sector format is invalid",
                   self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_sector_empty_key(self, m_isfile):
        """ProjectImporterCSV.load() raise exception when sector key is empty
        """

        m_isfile.return_value = True

        keys = [ '', " ", "      " ]
        for key in keys:
            csv = "code1;project description 1;" \
                  "[dom1] domain name 1;[%s] sector name 1" % (key)

            m_open = mock_open(data=StringIO(csv))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.assertRaisesRegexp(
                       HPCStatsSourceError,
                       "Project CSV code1 sector key is empty",
                       self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_sector_empty_name(self, m_isfile):
        """ProjectImporterCSV.load() raise exception when sector name is empty
        """

        m_isfile.return_value = True

        names = [ '', " ", "      " ]
        for name in names:
            csv = "code1;project description 1;" \
                  "[dom1] domain name 1;[sect1] %s" % (name)

            m_open = mock_open(data=StringIO(csv))
            with mock.patch("%s.open" % (module), m_open, create=True):
                self.assertRaisesRegexp(
                       HPCStatsSourceError,
                       "Project CSV code1 sector name is empty",
                       self.importer.load)

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_duplicate_sectors_domains(self, m_isfile):
        """ProjectImporterCSV.load() does not create duplicate sectors and
           domains
        """

        m_isfile.return_value = True

        csv = "code1;project description 1;" \
              "[dom1] domain name 1;[sect1] sector name 1\n" \
              "code2;project description 2;" \
              "[dom1] domain name 1;[sect1] sector name 1\n" \
              "code3;project description 3;" \
              "[dom1] domain name 1;[sect2] sector name 2\n" \
              "code4;project description 4;" \
              "[dom2] domain name 2;[sect3] sector name 3\n"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.importer.load()

        self.assertEquals(len(self.importer.projects), 4)
        self.assertEquals(len(self.importer.sectors), 3)
        self.assertEquals(len(self.importer.domains), 2)

        project2 = self.importer.projects[1]
        project4 = self.importer.projects[3]

        self.assertEquals(project2.code, 'code2')
        self.assertEquals(project4.description, 'project description 4')
        self.assertEquals(project2.sector.key, 'sect1')
        self.assertEquals(project4.sector.name, 'sector name 3')
        self.assertEquals(project2.sector.domain.key, 'dom1')
        self.assertEquals(project4.sector.domain.name, 'domain name 2')

    @mock.patch("%s.os.path.isfile" % module)
    def test_load_duplicate_project(self, m_isfile):
        """ProjectImporterCSV.load() raise Error when duplicate project codes
           found in CSV file
        """

        m_isfile.return_value = True

        csv = "code1;project description 1;" \
              "[dom1] domain name 1;[sect1] sector name 1\n" \
              "code1;project description 2;" \
              "[dom1] domain name 1;[sect1] sector name 1\n"

        m_open = mock_open(data=StringIO(csv))
        with mock.patch("%s.open" % (module), m_open, create=True):
            self.assertRaisesRegexp(
                   HPCStatsSourceError,
                   "duplicated project code code1 in CSV file",
                   self.importer.load)

loadtestcase(TestsProjectImporterCSV)
