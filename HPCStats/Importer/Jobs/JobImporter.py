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

class JobImporter(object):

    def __init__(self, app, db, config, cluster_name):

        self.app = app
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

    def get_last_job_id(self):
        last_job_id = 0
        req = """
            SELECT MAX(id_job) AS last_id
            FROM jobs
            WHERE clustername = %s; """
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)
        results = cur.fetchall()
        for job in results:
            if last_job_id < job[0]:
                last_job_id = job[0]
        return last_job_id

    def get_unfinished_job_id(self):
        unfinished_job_dbid = []
        req = """
            SELECT sched_id
            FROM jobs
            WHERE clustername = %s
              AND (   state = 'PENDING'
                   OR state = 'RUNNING' ); """
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)
        results = cur.fetchall()
        for job in results:
            unfinished_job_dbid.append(job[0])
        return unfinished_job_dbid
