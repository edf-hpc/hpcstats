#!/usr/bin/python
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

class UserImporter(object):

    def __init__(self, app, db, cluster_name):

        self.app = app
        self._db = db
        self._cluster_name = cluster_name

    def _get_unknown_users(self, db):
        req = """
            SELECT distinct(uid)
              FROM jobs
             WHERE clustername = %s
               AND uid NOT IN (SELECT uid FROM users WHERE users.cluster = %s); """
        datas = (self._cluster_name, self._cluster_name)

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)

        unknown_users = []

        while (1):

            row = cur.fetchone()
            if row == None: break
            uid = int(row[0])
            unknown_users.append(uid)

        return unknown_users;
