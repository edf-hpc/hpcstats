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
    def test_load(self, m_isfile):
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

loadtestcase(TestsProjectImporterCSV)
