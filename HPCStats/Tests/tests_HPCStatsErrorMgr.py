#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2016 EDF SA
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

from HPCStats.Conf.HPCStatsConf import HPCStatsConf

from HPCStats.Errors.Mgr import HPCStatsErrorMgr
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors

from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser


class TestsHPCStatsErrorMgr(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'test_cluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)

    def test_init(self):
        """HPCStatsErrorMgr.__init__() runs w/o problem
        """

        self.conf.conf = {}
        mgr = HPCStatsErrorMgr(self.conf)
        self.assertEquals(mgr.ignored_errors, set())

        section = 'constraints'

        self.conf.conf = { section: {'ignored_errors': ''}}
        mgr = HPCStatsErrorMgr(self.conf)
        self.assertEquals(mgr.ignored_errors, set())

        self.conf.conf = { section: {'ignored_errors': 'E_T0001'}}
        mgr = HPCStatsErrorMgr(self.conf)
        self.assertEquals(mgr.ignored_errors, set([Errors.E_T0001]))

        self.conf.conf = { section: {'ignored_errors': 'E_T0001, fail'}}
        mgr = HPCStatsErrorMgr(self.conf)
        self.assertEquals(mgr.ignored_errors, set([Errors.E_T0001]))

        self.conf.conf = { section: {'ignored_errors': ' fail  '}}
        mgr = HPCStatsErrorMgr(self.conf)
        self.assertEquals(mgr.ignored_errors, set())

        self.conf.conf = { section: {'ignored_errors': ' fail  , E_T0001, fail,,, faild, E_T0002,E_J1111'}}
        mgr = HPCStatsErrorMgr(self.conf)
        self.assertEquals(mgr.ignored_errors, set([Errors.E_T0001, Errors.E_T0002]))

        self.conf.conf = { section: {'ignored_errors': 'E_T0001,E_T0001'}}
        mgr = HPCStatsErrorMgr(self.conf)
        self.assertEquals(mgr.ignored_errors, set([Errors.E_T0001]))

if __name__ == '__main__':

    loadtestcase(TestsHPCStatsErrorMgr)
