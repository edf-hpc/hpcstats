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

from HPCStats.Tests.Mocks.ArchitectureImporter import MockArchitectureImporter
from HPCStats.Tests.Mocks.UserImporter import MockUserImporter
from HPCStats.Tests.Mocks.ProjectImporter import MockProjectImporter
from HPCStats.Tests.Mocks.BusinessCodeImporter import MockBusinessCodeImporter

class MockApp(object):

    def __init__(self, db, config, cluster):
        self.params = { 'since_event': '1970-01-01',
                        'since_jobid': -1 }
        self.arch = MockArchitectureImporter(self, db, config, cluster.name)
        self.users = MockUserImporter(self, db, config, cluster)
        self.projects = MockProjectImporter(self, db, config)
        self.business = MockBusinessCodeImporter(self, db, config)
