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

class MockMySQLdb(object):

    """Class with static methods to mock all used functions in MySQLdb module"""

    def __init__(self):
        pass

    @staticmethod
    def connect(host, user, passwd, db, port):
        """Mock of MySQLdb.connect()"""
        return MockMySQLdbConnect(host, user, passwd, db, port)

class MockMySQLdbCursor(object):

    req_references = { "get_assocs": "SELECT id_assoc, user FROM .*_assoc_table WHERE user != '';" }
    req_results = {
        "get_assocs": [ { 'id_assoc': 1, 'user': 'toto' } ]
    }

    def __init__(self):
        pass

    def execute(self, req, params=None):
        self.ref = None
        req = req.replace('\n','').strip()
        req_clean = re.sub(' +',' ',req)
        for reqref, reqpattern in MockMySQLdbCursor.req_references.iteritems():
            result = re.match(reqpattern, req_clean)
            if result:
                self.ref = reqref
                break
        pass

    def fetchall(self):
        if self.ref is not None:
            return MockMySQLdbCursor.req_results[self.ref]
        else:
            return []

class MockMySQLdbConnect(object):

    def __init__(self, host, user, passwd, db, port):

        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db
        self.port = port
        self._cursor = MockMySQLdbCursor()

    def cursor(self, stuff):

        return self._cursor

def mock_mysqldb():

    mysqldb_m = mock.Mock()
    mysqldb_m.connect.side_effect = MockMySQLdb.connect
    return mysqldb_m