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

"""
Model class for the Cluster table:

Job(
  job_id         SERIAL,
  job_sched_id   integer NOT NULL,
  job_batch_id   character varying(30) NOT NULL,
  job_nbCpu      integer NOT NULL,
  job_name       character varying(30),
  job_state      character varying(30) NOT NULL,
  job_queue      character varying(30),
  job_submission timestamp NOT NULL,
  job_start      timestamp,
  job_end        timestamp,
  userhpc_id     integer NOT NULL,
  cluster_id     integer NOT NULL,
  project_id     integer NOT NULL,
  business_code  character varying(30) NOT NULL,
  CONSTRAINT Job_pkey PRIMARY KEY (job_id),
  CONSTRAINT Job_unique UNIQUE (job_batch_id, cluster_id)
)

"""

from datetime import datetime
import logging
import string
import os
from ClusterShell.NodeSet import NodeSet, NodeSetParseRangeError
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Job:

    def __init__( self, cluster, user, project, business, nodeset,
                  sched_id, batch_id, name, nbcpu, state, queue,
                  submission, start, end, job_id=None):

        self.job_id = job_id
        self.sched_id = sched_id # user interface ID
        self.batch_id = batch_id # internal ID
        self.name = name
        self.nbcpu = nbcpu
        self.state = state
        self.queue = queue

        self.submission = submission
        self.start = start
        self.end = end

        self.cluster = cluster
        self.user = user
        self.project = project
        self.business = business
        self.nodeset = nodeset

    def __str__(self):

        # format datetimes strings
        submission = self.submission.strftime('%Y-%m-%d %H:%M:%S')
        if self.start is None:
           start = "notyet"
        else:
           start = self.start.strftime('%Y-%m-%d %H:%M:%S')
        if self.end is None:
           end = "notyet"
        else:
           end = self.end.strftime('%Y-%m-%d %H:%M:%S')

        return "job %d on %s(%d) by %s: state:%s queue:%s %s/%s/%s" % \
               ( self.sched_id,
                 self.cluster.name,
                 self.nbcpu
                 self.user.login,
                 self.state,
                 self.squeue,
                 submission,
                 start,
                 end )

    def find(self, db):
        """Search the Job in the database based on its sched_id and cluster. If
           exactly one job matches in database, set job_id attribute properly
           and returns its value. If more than one job matches, raises
           HPCStatsDBIntegrityError. If no job is found, returns None.
        """

        req = """
                SELECT job_id
                  FROM Job
                 WHERE cluster_id = %s
                   AND job_batch_id = %s
              """
        params = ( self.cluster.cluster_id,
                   self.batch_id )
        cur = db.get_cur()
        cur.execute(req, params)
        nb_rows = cur.rowcount
        if nb_rows == 0:
            logging.debug("job %s not found in DB" % (str(self)))
            return None
        elif nb_rows == 1:
            raise HPCStatsDBIntegrityError(
                    "several job_id found in DB for job %s" \
                      % (str(self)))
        else:
            self.job_id = cur.fetchone()[0]
            logging.debug("job %s found in DB with id %d" \
                            % (str(self),
                               self.job_id))
            return self.job_id

    def save(self, db):
        """Insert Job in database. You must make sure that the Job does not
           already exist in database yet (typically using Job.find() method
           else there is a risk of future integrity errors because of
           duplicated jobs. If job_id attribute is set, it raises
           HPCStatsRuntimeError.
        """

        if self.job_id is not None:
            raise HPCStatsRuntimeError(
                    "could not insert job %s since already existing in "\
                    "database" \
                      % (str(self)))

        req = """
                INSERT INTO job ( job_sched_id,
                                  job_batch_id,
                                  job_name,
                                  job_nbCpu,
                                  job_state,
                                  job_queue,
                                  job_submission,
                                  job_start,
                                  job_end,
                                  cluster_id,
                                  userhpc_id,
                                  project_id,
                                  business_code )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING job_id
              """

        params = ( self.sched_id,
                   self.batch_id,
                   self.name,
                   self.nbcpu,
                   self.state,
                   self.queue,
                   self.submission,
                   self.start,
                   self.end,
                   self.cluster.cluster_id,
                   self.user.user_id,
                   self.project.project_id,
                   self.business.code )

        cur = db.get_cur()
        #print cur.mogrify(req, params)
        cur.execute(req, params)
        self.job_id = cur.fetchone()[0]
        # TODO: Run creation should be done in JobImporter, not here
        try:
            if self.nodeset is not None
                for node_name in NodeSet(self.nodeset):
                    node = Node(node_name, self.cluster, "", 0, 0, 0)
                    node_id = node.find()
                    if node_id is None:
                        raise HPCStatsDBIntegrityError(
                                "unable to find node %s for job %s" \
                                  % (node_name, str(self)))

                    run = Run(self.cluster, node, self)
                    run.save()
        except NodeSetParseRangeError as e:
            logging.error("could not parse nodeset %s", self.nodeset)
        
    def update(self, db):
        """Update Job sched_id, nbcpu, name, state, queue, submission, start and
           end in database. Raises HPCStatsRuntimeError if self.job_id is None.
        """

        if self.job_id is None:
            raise HPCStatsRuntimeError(
                    "could not update job %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Job
                   SET job_sched_id = %s,
                       job_nbCpu = %s,
                       job_name = %s,
                       job_state = %s,
                       job_queue = %s,
                       job_submission = %s,
                       job_start = %s,
                       job_end = %s
                 WHERE job_id = %s
              """
        params = ( self.sched_id
                   self.nbcpu,
                   self.name,
                   self.state,
                   self.queue,
                   self.submission,
                   self.start,
                   self.end,
                   self.job_id )

        cur = db.get_cur()
        #print cur.mogrify(req, params)
        cur.execute(req, params)

        # TODO: Run creation should be done in JobImporter, not here
        try:
            if self.nodeset is not None
                for node_name in NodeSet(self.nodeset):
                    # fake temporary Node just to get the node
                    node = Node(node_name, self.cluster, "", 0, 0, 0)
                    node_id = node.find()
                    if node_id is None:
                        raise HPCStatsDBIntegrityError(
                                "unable to find node %s for job %s" \
                                  % (node_name, str(self)))

                    run = Run(self.cluster, node, self)
                    if not run.existing():
                        run.save()
        except NodeSetParseRangeError as e:
            logging.error("could not parse nodeset %s", self.nodeset)
