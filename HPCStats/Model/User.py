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

from datetime import datetime
import logging

class User:
    def __init__(self, name = "", login = "", cluster_name = "", department = "", uid = -1, gid = -1, creation_date = None, deletion_date = None):

        self._name = name
        self._login = login
        self._cluster_name = cluster_name
        self._department = department
        self._uid = uid
        self._gid = gid
        self._creation_date = creation_date
        self._deletion_date = deletion_date

    def __str__(self):
        if self._creation_date == None:
           creation_date = "unknown"
        else:
           creation_date = self._creation_date.strftime('%Y-%m-%d')
        if self._deletion_date == None:
           deletion_date = "unknown"
        else:
           deletion_date = self._deletion_date.strftime('%Y-%m-%d')
        return self._name + " [" + self._department + "] " + self._login + " - " + self._cluster_name + " (" + str(self._uid) + "|" + str(self._gid) + "): " + creation_date + "/" + deletion_date

    def __eq__(self, other):
        return self._cluster_name == other._cluster_name and self._login == other._login


    """ getter accessors """
    def get_name(self):
        return self._name

    def get_login(self):
        return self._login

    def get_cluster_name(self):
        return self._cluster_name

    def get_department(self):
        return self._department

    def get_uid(self):
        return self._uid

    def get_gid(self):
        return self._gid

    def get_creation_date(self):
        return self._creation_date

    def get_deletion_date(self):
        return self._deletion_date

    """ setter accessors """
    def set_name(self, name):
        self._name = name

    def set_login(self, login):
        self._login = login

    def set_cluster_name(self, cluster_name):
        self._cluster_name = cluster_name

    def set_department(self, department):
        self._department = department

    def set_uid(self, uid):
        self._uid = uid

    def set_gid(self, gid):
        self._gid = gid

    def set_creation_date(self, creation_date):
        self._creation_date = creation_date

    def set_deletion_date(self, deletion_date):
        self._deletion_date = deletion_date


    """ functions """
    def exists_in_db(self, db):
        cur = db.get_cur()
        cur.execute("SELECT login FROM users WHERE login = %s AND cluster = %s",
                     (self._login,
                      self._cluster_name ) )
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False
        else:
           raise UserWarning, ("incorrect number of results (%d) for login \
                                %s on cluster %s" % \
                                ( nb_rows,
                                  self._login,
                                  self._cluster_name ) )

    def save(self, db):
        req = """
            INSERT INTO users (
                            name,
                            login,
                            cluster,
                            department,
                            creation,
                            deletion,
                            uid,
                            gid )
            VALUES ( %s, lower(%s), %s, %s, %s, %s, %s, %s); """
        datas = (
            self._name,
            self._login,
            self._cluster_name,
            self._department,
            self._creation_date,
            self._deletion_date,
            self._uid,
            self._gid )

        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE users SET
                       name = %s,
                       department = %s,
                       creation = %s,
                       deletion = %s
            WHERE login = %s
              AND cluster = %s; """
        datas = (
            self._name,
            self._department,
            self._creation_date,
            self._deletion_date,
            self._login,
            self._cluster_name )

        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    def update_name(self, db):
        req = """
            UPDATE users SET name = %s
            WHERE uid = %s AND cluster = %s;"""
        datas = (
            self._name,
            self._uid,
            self._cluster_name )

        db.get_cur().execute(req, datas)

    def update_deletion_date(self, db):
        req = """
            UPDATE users SET deletion = %s
            WHERE uid = %s AND cluster = %s;"""
        datas = (
            self._deletion_date,
            self._uid,
            self._cluster_name )

        db.get_cur().execute(req, datas)

    def update_department(self, db):
        req = """
            UPDATE users SET department = %s
            WHERE login = %s AND cluster = %s;"""
        datas = (
            self._department,
            self._login,
            self._cluster_name )

        db.get_cur().execute(req, datas)

    def update_creation_date(self, db):
        req = """
            UPDATE users SET
                        creation = %s
            WHERE login = %s AND cluster = %s;"""
        datas = (
            self._creation_date,
            self._login,
            self._cluster_name )

        db.get_cur().execute(req, datas)
