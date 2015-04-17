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

import logging

class Filesystem:
    def __init__(self, mount_point = "", cluster = "", type = ""):

        self._mount_point = mount_point
        self._cluster = cluster
        self._type = type

    def __str__(self):
        return "mount point : %s ,on cluster : %s, type : %s" % \
                   ( self._mount_point,
                     self._cluster,
                     self._type)

    def save(self, db):
        req = """
            INSERT INTO filesystem (
                            mount_point,
                            cluster,
                            type )
            VALUES ( %s, %s, %s); """
        datas = (
            self._mount_point,
            self._cluster,
            self._type )

        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)


    def delete(self, db):
        cur = db.get_cur()
        cur.execute("DELETE FROM filesystem WHERE mount_point = %s",(self._mount_point,))

    def get_fs_for_cluster(self, db, cluster):
        req = """
            SELECT mount_point
            FROM filesystem
            WHERE cluster = %s
              ;"""
        datas = (cluster,)
        cur = db.get_cur()
        cur.execute(req, datas)
        results = []
        while (1):
            db_row = cur.fetchone()
            if db_row == None: break
            results.append(db_row[0])
        return results

