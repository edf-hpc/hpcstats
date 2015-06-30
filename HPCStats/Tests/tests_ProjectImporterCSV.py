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
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Project import Project
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Mocks.Utils import mock_open
import HPCStats.Tests.Mocks.MockPg2 as MockPg2 # for PG_REQS
from HPCStats.Tests.Mocks.MockPg2 import mock_psycopg2
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

class TestsProjectImporterCSVLoad(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'testcluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG
        self.app = None
        self.db = None
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
        self.assertEquals(project.domain.key, 'dom1')
        self.assertEquals(project.domain.name, 'domain name 1')

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
        self.assertEquals(project1.domain.key, 'dom1')
        self.assertEquals(project2.domain.name, 'domain name 2')

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
        self.assertEquals(len(self.importer.domains), 2)

        project2 = self.importer.projects[1]
        project4 = self.importer.projects[3]

        self.assertEquals(project2.code, 'code2')
        self.assertEquals(project4.description, 'project description 4')
        self.assertEquals(project2.domain.key, 'dom1')
        self.assertEquals(project4.domain.name, 'domain name 2')

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

class TestsProjectImporterCSVUpdate(HPCStatsTestCase):

    @mock.patch("HPCStats.DB.HPCStatsDB.psycopg2", mock_psycopg2())
    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'testcluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG
        self.app = None
        self.db = HPCStatsDB(self.conf)
        self.db.bind()
        self.importer = ProjectImporterCSV(self.app, self.db, self.conf)

    def test_update(self):
        """ProjectImporterCSV.update() works with simple data
        """

        domain1 = Domain('dom1', 'domain name 1')
        project1 = Project(domain1, 'code1', 'project description 1')

        MockPg2.PG_REQS['save_project'].set_assoc(
          params=( project1.code, project1.description, domain1.key ),
          result=[ [ 1 ] ]
        )
        self.importer.projects = [ project1 ]
        self.importer.domains = [ domain1 ]

        self.importer.update()

if __name__ == '__main__':

    loadtestcase(TestsProjectImporterCSVLoad)
    loadtestcase(TestsProjectImporterCSVUpdate)
