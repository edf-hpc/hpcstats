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

class Business:
    def __init__(self, id = "", key="", description = ""):

        self._id = id
        self._key = key
        self._description = description

    def __str__(self):
        if self._description == None:
           description = "unknown"
        else:
           description = self._description
        return self._id + " : " + self._key + " - " + self._description

    """ getter accessors """
    def get_id(self):
        return self._id

    def get_key(self):
        return self._key

    def get_description(self):
        return self._description

    """ setter accessors """
    def set_description(self, description):
        self._description = description


    """ methodes """
    def save(self, db):
        req = """
            INSERT INTO business (
                              key,
                              description )
            VALUES (%s, %s);"""
        datas = (
            self._key,
            self._description )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE business SET 
                         key = %s,
                         description = %s 
            WHERE id = %s;"""
        datas = (
            self._key,
            self._description, 
            self._id )
        db.get_cur().execute(req, datas)

    def already_exist(self, db):
        cur = db.get_cur()
        cur.execute("SELECT * FROM business WHERE key = %s", (self._key,))
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False

    def business_from_key(self, db, key):
        cur = db.get_cur()
        cur.execute("SELECT * FROM business WHERE key = %s", (key,))
        res = cur.fetchone()
        self._id = res[0]
        self._key = res[1]
        self._description = res[2]

def delete_business(db):
    db.get_cur().execute("ALTER SEQUENCE business_id_seq RESTART WITH 1;")  
    db.get_cur().execute("DELETE FROM business;")  

def get_business_id(db, business):
    cur = db.get_cur()
    cur.execute("SELECT id_business FROM business WHERE lower(key) = lower(%s)", (business,))
    results = cur.fetchone()
    return results[0]
