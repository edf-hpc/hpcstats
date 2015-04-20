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

class Cluster:
    def __init__(self, name = ""):

        self._name = name
    
    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self._name == other._name

    def exists_in_db(self, db):
        cur = db.get_cur()
        cur.execute("SELECT name FROM clusters WHERE name = %s;", (self._name,) )
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False
        else:
           raise UserWarning, ("incorrect number of results (%d) for cluster \
                                %s" % \
                                ( nb_rows,
                                  self._name ) )

    def get_nb_cpus(self, db):

        req = """ SELECT SUM(cpu) FROM nodes WHERE cluster = %s; """
        datas = ( self._name, )

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        return cur.fetchone()[0]

    def get_min_datetime(self, db):

        req = """
            SELECT MIN(running_datetime)
              FROM jobs
             WHERE clustername = %s
               AND state NOT IN ('CANCELLED', 'NODE_FAIL', 'PENDING');
              """
        datas = ( self._name, )

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        return cur.fetchone()[0]

   
    def get_nb_accounts(self, db, creation_date):

        req = """
            SELECT COUNT (name)
              FROM users
             WHERE creation < %s
               AND cluster = %s; """
        datas = (creation_date, self._name)

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        
        return cur.fetchone()[0]

    def get_nb_active_users(self, db, start, end):
   
        req = """
            SELECT COUNT(DISTINCT uid)
              FROM jobs
            WHERE (running_datetime BETWEEN %s AND %s)
               OR (end_datetime BETWEEN %s AND %s)
               OR (running_datetime <= %s AND end_datetime >= %s); """
        datas = (start, end, start, end, start, end)
        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        
        return cur.fetchone()[0]

    def save(self, db):
        req = """ INSERT INTO clusters ( name ) VALUES ( %s ); """
        datas = ( self._name, )
 
        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    def update(self, db):
        # nothing to do here
        pass

    """ accessors """

    def get_name(self):
        return self._name
