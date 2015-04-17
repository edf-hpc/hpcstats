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

class Context:
    def __init__(self, id = "", login = "", job = "", project = "", business = "", cluster = ""):

        self._id = id
        self._login = login
        self._job = job
        self._project = project
        self._business = business
        self._cluster = cluster

    def __str__(self):
        if self._job == None:
           job = "unknown"
        else:
           job = self._job
        if self._project == None:
           project = "unknown"
        else:
           project = self._project
        if self._business == None:
           business = "unknown"
        else:
           business = self._business
        return  "user : " + self._login + ", job_id : " + str(job) + ", project id : " + str(project) + ", business id : " + str(business)

    """ getter accessors """
    def get_id(self):
        return self._id

    def get_login(self):
        return self._login

    def get_job(self):
        return self._job

    def get_project(self):
        return self._project

    def get_business(self):
        return self._business

    def get_cluster(self):
        return self._cluster

    """ setter accessors """
    def set_login(self, login):
        self._login = login

    def set_job(self, job):
        self._job = job

    def set_project(self, project):
        self._project = project

    def set_business(self, business):
        self._business = business

    def set_cluster(self, cluster):
        self._cluster = cluster

    """ methodes """
    def save(self, db):
        req = """
            INSERT INTO contexts (
                              login,
                              id_job,
                              id_project,
                              id_business,
                              name_cluster )
            VALUES (%s, %s, %s, %s, %s);"""
        datas = (
            self._login,
            self._job,
            self._project,
            self._business,
            self._cluster, )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE contexts SET 
                         login = %s,
                         id_job = %s,
                         id_project = %s,
                         id_business = %s,
            WHERE id_context = %s;"""
        datas = (
            self._login,
            self._job,
            self._project,
            self._business,
            self._id )
        db.get_cur().execute(req, datas)

def delete_contexts(db, cluster):
    #db.get_cur().execute("ALTER SEQUENCE contexts_id_seq RESTART WITH 1;")
    db.get_cur().execute("DELETE FROM contexts WHERE name_cluster=%s;", (cluster,))

def delete_contexts_with_business(db):
    db.get_cur().execute("DELETE FROM contexts where id_business is not null;")

def delete_contexts_with_pareo(db):
    db.get_cur().execute("DELETE FROM contexts where id_project is not null;")
