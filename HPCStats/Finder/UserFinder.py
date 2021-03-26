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

from HPCStats.Model.User import User

class UserFinder():

    def __init__(self, db):

        self._db = db

    def find(self, cluster_name, uid):
        req = """
            SELECT name,
                   login,
                   department,
                   gid,
                   creation,
                   deletion
              FROM users
             WHERE uid = %s
               AND cluster = %s; """
        data = (
            uid,
            cluster_name )

        cur = self._db.cur
        #print cur.mogrify(req, data)
        cur.execute(req, data)
        
        nb_rows = cur.rowcount
        if nb_rows == 1:
            row = cur.fetchone()
            return User( name = row[0],
                         login = row[1],
                         cluster_name = cluster_name,
                         department = row[2],
                         uid = uid,
                         gid = row[3],
                         creation_date = row[4],
                         deletion_date = row[5] )

        elif nb_rows == 0:
           raise UserWarning ("no user found with uid %d \
                                on cluster %s" % \
                                ( uid,
                                  cluster_name ) )
        else:
           raise UserWarning ("incorrect number of results (%d) for uid \
                                %s on cluster %s" % \
                                ( nb_rows,
                                  uid,
                                  cluster_name ) )

