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
import string
import os
from ClusterShell.NodeSet import NodeSet, NodeSetParseRangeError

class Job:

    def __init__( self,
                  db_id = 0,
                  id_job = 0,
                  sched_id = 0,
                  cluster_name = "",
                  uid = -1,
                  gid = -1,
                  submission_datetime = 0,
                  running_datetime = 0,
                  end_datetime = 0,
                  nb_procs = 0,
                  nb_hosts = 0,
                  running_queue = "",
                  nodes = "",
                  state = "unknown",
                  login = "",
                  name = ""):
        self._db_id = db_id
        self._sched_id = sched_id
        self._id_job = id_job
        self._cluster_name = cluster_name
        self._uid = uid
        self._gid = gid
        self._submission_datetime = submission_datetime
        self._running_datetime = running_datetime
        self._end_datetime = end_datetime
        self._nb_procs = nb_procs
        self._nb_hosts = nb_hosts
        self._running_queue = running_queue
        self._nodes = nodes
        self._state = state
        self._login = login
        self._name = os.path.basename(name)[:29]

    def __str__(self):
        if self._running_datetime == 0:
           running_datetime = "notyet"
        else:
           running_datetime = self._running_datetime.strftime('%Y-%m-%d %H:%M:%S')
        if self._end_datetime == 0:
           end_datetime = "notyet"
        else:
           end_datetime = self._end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return "%s/%s (%d|%d) %s / %s / %s -> %d / %d [%s] %s %s %s" % \
               ( self._cluster_name,
                 self._id_job,
                 self._uid,
                 self._gid,
                 self._submission_datetime,
                 self._running_datetime,
                 self._end_datetime,
                 self._nb_hosts,
                 self._nb_procs,
                 self._nodes,
                 self._state,
                 self._login,
                 self._name )

    def save(self, db):
        req = """
           INSERT INTO jobs (
                           id_job,
                           sched_id,
                           uid,
                           gid,
                           clustername,
		       	   running_queue,
                           submission_datetime,
                           running_datetime,
                           end_datetime,
                           nb_nodes,
                           nb_cpus,
                           state,
                           login,
                           name)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id; """

        datas = (
           self._id_job,
           self._sched_id,
           self._uid,
           self._gid,
           self._cluster_name,
	   self._running_queue,
           self._submission_datetime.strftime('%Y-%m-%d %H:%M:%S'),
           self._running_datetime.strftime('%Y-%m-%d %H:%M:%S'),
           self._end_datetime.strftime('%Y-%m-%d %H:%M:%S'),
           self._nb_hosts,
           self._nb_procs,
           self._state,
           self._login,
           self._name)
 
        dbcursor = db.get_cur()

        #print dbcursor.mogrify(req, datas)
	logging.debug(datas)
        dbcursor.execute(req, datas)
        self._db_id = dbcursor.fetchone()[0]
        try:
	  if self._nodes is not None:
            for node in NodeSet(self._nodes.replace("x",",")):
                req = """
                    INSERT INTO job_nodes (
                                    job,
                                    node,
                                    cpu_id
                                    )
                    VALUES (%s, %s, %s); """
                datas = (
                    self._db_id,
                    node,
                    "unknown")
                db.get_cur().execute(req, datas)
        except NodeSetParseRangeError as e:
            logging.error("could not parse nodeset %s", self._nodes) 
        
    def update(self, db):
        req = """
           UPDATE jobs SET
                      id_job = %s,
                      uid = %s,
                      gid = %s,
                      clustername = %s,
                      running_queue = %s,
                      submission_datetime = %s,
                      running_datetime = %s,
                      end_datetime = %s,
                      nb_nodes = %s,
                      nb_cpus = %s,
                      state = %s,
                      login = %s,
                      name = %s
           WHERE sched_id = %s AND id_job = %s AND clustername = %s
           RETURNING id; """
        datas = (
           self._id_job,
           self._uid,
           self._gid,
           self._cluster_name,
           self._running_queue,
           self._submission_datetime.strftime('%Y-%m-%d %H:%M:%S'),
           self._running_datetime.strftime('%Y-%m-%d %H:%M:%S'),
           self._end_datetime.strftime('%Y-%m-%d %H:%M:%S'),
           self._nb_hosts,
           self._nb_procs,
           self._state,
           self._login,
           self._name,
           self._sched_id,
	   self._id_job,
	   self._cluster_name)

        dbcursor = db.get_cur()
        dbcursor.execute(req, datas)
        self._db_id = dbcursor.fetchone()[0]

        # Add nodes to job_nodes if not defined already
        req = """ SELECT count(job) FROM job_nodes WHERE job = %s; """
        datas = ( self._db_id, )

        #print dbcursor.mogrify(req, datas)

        dbcursor.execute(req, datas)
        nodecount = dbcursor.fetchone()[0]

        if nodecount == 0 and self._nodes is not None:
           for node in NodeSet(self._nodes.replace("x",",")):
               if node != "None assigned":
                   req = """
                       INSERT INTO job_nodes (
                                       job,
                                       node,
                                       cpu_id
                                       )
                       VALUES (%s, %s, %s); """
                   datas = (
                       self._db_id,
                       node,
                       "unknown")
	    #print (datas)
                   db.get_cur().execute(req, datas)

		    
    """ accessors """

    def get_db_id(self):
        return self._db_id

    def get_uid(self):
        return self._uid

    def get_running_datetime(self):
        return self._running_datetime

    def set_running_datetime(self, running_datetime):
        self._running_datetime = running_datetime

    def get_end_datetime(self):
        return self._end_datetime

    def get_nb_procs(self):
        return self._nb_procs

    def get_state(self):
        return self._state

    def get_cluster_name(self):
        return self._cluster_name
