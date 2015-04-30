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

from HPCStats.Model.Job import Job

class JobFinder:

    def __init__(self, db):

        self._db = db

    def find_jobs_in_interval(self, cluster_name, begin, end):

        # get all jobs that have been running during (at least partially) during the interval
        req = """
            SELECT id_job,
                   sched_id,
                   uid,
                   gid,
                   submission_datetime,
                   running_datetime,
                   end_datetime,
                   nb_nodes,
                   nb_cpus,
                   running_queue,
                   state
              FROM jobs
             WHERE clustername = %s
                  AND state NOT IN ('CANCELLED', 'NODE_FAIL', 'PENDING')
                  AND (   (running_datetime BETWEEN %s AND %s)
                       OR (end_datetime BETWEEN %s AND %s)
                       OR (running_datetime <= %s AND end_datetime >= %s)
                      )
             ORDER BY end_datetime; """
        data = (cluster_name, begin, end, begin, end, begin, end)

        cur = self._db.cur
        #print cur.mogrify(req, data)
        cur.execute (req, data)

        jobs = []

        while (1):

            row = cur.fetchone()
            if row == None: break
            
            #print "row", len(row), row
            job = Job( id_job = row[0],
                       sched_id = row[1],
                       uid = row[2],
                       gid = row[3],
                       submission_datetime = row[4],
                       running_datetime = row[5],
                       end_datetime = row[6],
                       nb_hosts = row[7],
                       nb_procs = row[8],
                       running_queue = row[9],
                       state = row[10],
                       cluster_name = cluster_name)
            jobs.append(job)

        return jobs
