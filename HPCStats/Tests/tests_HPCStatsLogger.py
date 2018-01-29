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

import logging

from HPCStats.Log.Logger import HPCStatsLogger
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors

from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase
from HPCStats.Tests.Mocks.Log import MockLoggingHandler

class MockHPCStatsErrorMgr(object):

    def __init__(self):

        self.ignored_errors = set()

class TestsHPCStatsLogger(HPCStatsTestCase):

    def setUp(self):
        logging.setLoggerClass(HPCStatsLogger)
        self.logger = logging.getLogger(__name__)
        self.handler = MockLoggingHandler()
        self.logger.addHandler(self.handler)
        self.handler.reset()

    def test_warn(self):
        """HPCStatsLogger.warn() runs w/o problem
        """

        # none error manager
        HPCStatsLogger.set_error_mgr(None)
        self.logger.warn(Errors.E_T0001, "error 1 %s", 'test')
        self.assertIn('TestsHPCStatsLogger: error 1 test', self.handler.messages['warning'])
        self.handler.reset()

        error_mgr = MockHPCStatsErrorMgr()
        HPCStatsLogger.set_error_mgr(error_mgr)

        # error manager w/o ignored errors -> warning with ERROR <code> prefix
        self.logger.warn(Errors.E_T0001, "error 2 %s", 'test')
        self.assertIn('TestsHPCStatsLogger: ERROR E_T0001: error 2 test',
                      self.handler.messages['warning'])
        print self.handler.messages
        self.assertEquals(len(self.handler.messages['debug']), 0)
        self.handler.reset()

        # add E_T0001 to error manager ignored errors set -> debug with IGNORED
        # ERROR <code> prefix
        error_mgr.ignored_errors.add(Errors.E_T0001)
        self.logger.warn(Errors.E_T0001, "error 3 %s", 'test')
        self.assertIn('TestsHPCStatsLogger: (IGNORED) ERROR E_T0001: error 3 test',
                      self.handler.messages['debug'])
        self.assertEquals(len(self.handler.messages['warning']), 0)
        self.handler.reset()

if __name__ == '__main__':

    loadtestcase(TestsHPCStatsLogger)
