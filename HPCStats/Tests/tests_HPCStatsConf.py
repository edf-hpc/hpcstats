#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2018 EDF SA
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

import copy

from HPCStats.Conf.HPCStatsConf import HPCStatsConf
from HPCStats.Tests.Mocks.MockConfigParser import MockConfigParser
from HPCStats.Tests.Utils import HPCStatsTestCase, loadtestcase

CONFIG = {
  'sectiona': {
    'option_str':  'test_value',
    'option_int':  123,
    'option_bool': False,
    'option_list': 'john,doe',
  },
}

module = "HPCStats.Conf.HPCStatsConf"

class TestsHPCStatsConf(HPCStatsTestCase):

    def setUp(self):
        self.filename = 'fake'
        self.cluster = 'test_cluster'
        HPCStatsConf.__bases__ = (MockConfigParser, object)
        self.conf = HPCStatsConf(self.filename, self.cluster)
        self.conf.conf = CONFIG.copy()

    def test_init(self):
        """HPCStatsConf.__init__() tests
        """
        pass

    def test_get(self):
        """HPCStatsConf.get() tests
        """
        self.assertEquals('test_value', self.conf.get('sectiona', 'option_str'))
        self.assertEquals('test_value', self.conf.get('sectiona', 'option_str', str))
        self.assertEquals(123, self.conf.get('sectiona', 'option_int', int))
        self.assertEquals(False, self.conf.get('sectiona', 'option_bool', bool))
        self.assertEquals('john,doe', self.conf.get('sectiona', 'option_list'))

    def test_get_default(self):
        """HPCStatsConf.get_default() tests
        """
        self.assertEquals('default', self.conf.get_default('inexisting', 'param', 'default'))
        self.assertEquals(3, self.conf.get_default('inexisting', 'param', 3))
        self.assertEquals([], self.conf.get_default('inexisting', 'param', []))
        self.assertEquals(None, self.conf.get_default('inexisting', 'param', None))

    def test_get_clusters_list(self):
        """HPCStatsConf.get_clusters_list() tests
        """
        self.conf.conf['clusters'] = {}
        self.conf.conf['clusters']['clusters'] = 'clustera'
        self.assertEquals(['clustera'], self.conf.get_clusters_list())
        self.conf.conf['clusters']['clusters'] = 'clustera,clusterb'
        self.assertEquals(['clustera','clusterb'], self.conf.get_clusters_list())

    def test_get_list(self):
        """HPCStatsConf.get_list() tests
        """
        self.assertEquals([], self.conf.get_list('inexisting', 'param'))
        self.conf.conf['sectiona']['option_list'] = 'item1'
        self.assertEquals(['item1'], self.conf.get_list('sectiona', 'option_list'))
        self.conf.conf['sectiona']['option_list'] = 'item1,item2'
        self.assertEquals(['item1', 'item2'], self.conf.get_list('sectiona', 'option_list'))
        self.conf.conf['sectiona']['option_list'] = ' item1 ,item2 '
        self.assertEquals(['item1', 'item2'], self.conf.get_list('sectiona', 'option_list'))
        self.conf.conf['sectiona']['option_list'] = ' ,, item1 ,item2  ,, '
        self.assertEquals(['item1', 'item2'], self.conf.get_list('sectiona', 'option_list'))

if __name__ == '__main__':

    loadtestcase(TestsHPCStatsConf)
