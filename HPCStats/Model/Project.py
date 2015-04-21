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

class Project:
    def __init__(self, name, description, sector=None, domain=None):

        self.name = name
        self.description = description
        self.domain = domain
        self.sector = sector

    def __str__(self):
        if self.sector == None:
           sector = "unknown"
        else:
           sector = self.sector
        if self.domain == None:
           domain = "unknown"
        else:
           domain = self.domain
        if self.description == None:
           description = "unknown"
        else:
           description = self.description
        return self.name + " : " + self.sector + " - " + self.domain + " - " + self.description

    def save(self, db):
        req = """
            INSERT INTO projects (
                              id_sector,
                              id_domain,
                              description,
                              pareo )
            VALUES (%s, %s, %s, %s);"""
        datas = (
            self.sector,
            self.domain,
            self.description,
            self.name )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE projects SET
                         sector = %s,
                         domain = %s,
                         description = %s
            WHERE pareo = %s;"""
        datas = (
            self.sector,
            self.domain,
            self.description,
            self.name )
        db.get_cur().execute(req, datas)

    def already_exist(self, db):
        cur = db.get_cur()
        cur.execute("SELECT * FROM projects WHERE pareo = %s", (self.name,))
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False

    def project_from_name(self, db, name):
        cur = db.get_cur()
        cur.execute("SELECT pareo, description, sector, domain FROM projects WHERE pareo = %s", (name,))
        res = cur.fetchone()
        self.name = res[0]
        self.description = res[1]
        self.sector = res[2]
        self.domain = res[3]

def delete_projects(db):
    db.get_cur().execute("ALTER SEQUENCE projects_id_seq RESTART WITH 1;")   
    db.get_cur().execute("DELETE FROM projects;")

def get_name_id(db, name):
    cur = db.get_cur()
    cur.execute("SELECT id_project FROM projects WHERE lower(pareo) = lower(%s)", (name,))
    results = cur.fetchone()
    return results[0]

