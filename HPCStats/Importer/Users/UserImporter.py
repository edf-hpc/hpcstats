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

from HPCStats.Importer.Importer import Importer

class UserImporter(Importer):

    def __init__(self, app, db, config, cluster):

        super(UserImporter, self).__init__(app, db, config, cluster)

    def _get_unknown_users(self, db):
        req = """
            SELECT distinct(uid)
              FROM jobs
             WHERE clustername = %s
               AND uid NOT IN (SELECT uid FROM users WHERE users.cluster = %s); """
        datas = (self.cluster.name, self.cluster.name)

        cur = db.cur
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)

        unknown_users = []

        while (1):

            row = cur.fetchone()
            if row == None: break
            uid = int(row[0])
            unknown_users.append(uid)

        return unknown_users;
