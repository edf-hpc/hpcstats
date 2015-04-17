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

class Domain:
    def __init__(self, id = "", description = ""):
       
        self._id = id #id est ici un chaine de caractère
        self._description = description

    def __str__(self):
        if self._description == None:
           description = "unknown"
        else:
           description = self._description
        return self._id + " : " + self._description

    """ getter accessors """
    def get_id(self):
        return self._id

    def get_description(self):
        return self._description

    """ setter accessors """
    def set_description(self, description):
        self._description = description

    """ methodes """
    def save(self, db):
        req = """
            INSERT INTO domains (
                              id_domain,
                              description )
            VALUES (%s, %s);"""
        datas = (
            self._id,
            self._description )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE domains SET 
                         id_domain = %s,
                         description = %s 
            WHERE id_domain = %s;"""
        datas = (
            self._id,
            self._description,
            self._id )
        db.get_cur().execute(req, datas)

    def already_exist(self, db):
        cur = db.get_cur()
        cur.execute("SELECT * FROM domains WHERE id_domain = %s", (self._id,))
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False

def delete_domains(db):
    db.get_cur().execute("DELETE FROM domains;")

 
