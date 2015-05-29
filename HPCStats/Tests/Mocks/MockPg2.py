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
import re

# the requests and results are then defined by tests themselves.
PG_REQS = dict()

class MockPsycopg2(object):

    """Class with static methods to mock all used functions in psycogp2
       module
    """

    def __init__(self):
        pass

    @staticmethod
    def connect(conn):
        """Mock of psycopg2.connect()"""
        return MockPsycopg2Connect()

class MockPsycopg2Connect(object):

    def __init__(self):

        self._cursor = MockPsycopg2Cursor()

    def cursor(self):

        return self._cursor

    def commit(self):

        pass

class MockPsycopg2Cursor(object):

    def __init__(self):

        self.ref = None
        self.idx = 0

    def execute(self, req, params=None):

        self.ref = None
        req = req.replace('\n','').strip()
        req_clean = re.sub(' +',' ',req)
        for reqref, req in PG_REQS.iteritems():
            print ("clean: %s, req: %s" % (req_clean, req))
            result = re.match(req['req'], req_clean)
            if result:
                print ("match!")
                self.ref = reqref
                self.idx = 0
                break

    def fetchall(self):
        if self.ref is not None:
            return PG_REQS[self.ref]['res']
        else:
            return []

    def fetchone(self):
        if self.ref is not None:
            results = PG_REQS[self.ref]['res']
            if len(results) > self.idx:
                result = results[self.idx]
                self.idx += 1
                return result
        return None

    @property
    def rowcount(self):
        if self.ref is not None:
            return len(PG_REQS[self.ref]['res'])
        else:
            return 0

def mock_psycopg2():

    psycopg2_m = mock.Mock()
    psycopg2_m.connect.side_effect = MockPsycopg2.connect
    return psycopg2_m
