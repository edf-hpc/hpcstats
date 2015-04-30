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

class JobImporter(Importer):

    def __init__(self, app, db, config, cluster):

        super(JobImporter, self).__init__(app, db, config, cluster)

    def get_last_job_id(self):
        """Returns the last inserted id_job in HPCStats DB."""

        last_job_id = 0
        req = """
            SELECT MAX(id_job) AS last_id
            FROM jobs
            WHERE clustername = %s; """
        datas = (self.cluster.name,)
        cur = self._db.cur
        cur.execute(req, datas)
        results = cur.fetchall()
        for job in results:
            if last_job_id < job[0]:
                last_job_id = job[0]
        return last_job_id

    def get_unfinished_job_id(self):
        """Returns the list of sched_id of unfinished jobs in HPCStats DB."""

        unfinished_job_dbid = []
        req = """
            SELECT sched_id
            FROM jobs
            WHERE clustername = %s
              AND (   state = 'PENDING'
                   OR state = 'RUNNING' ); """
        datas = (self.cluster.name,)
        cur = self._db.cur
        cur.execute(req, datas)
        results = cur.fetchall()
        for job in results:
            unfinished_job_dbid.append(job[0])
        return unfinished_job_dbid
