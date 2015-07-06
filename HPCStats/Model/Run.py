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
Schema of the ``Run`` table in HPCStats database:

.. code-block:: sql

    Run(
      job_id         integer NOT NULL,
      node_id        integer NOT NULL,
      cluster_id     integer NOT NULL,
      CONSTRAINT Run_pkey PRIMARY KEY (job_id, node_id, cluster_id)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Run(object):

    """Model class for the Run table."""

    def __init__(self, cluster, node, job):

        self.cluster = cluster
        self.node = node
        self.job = job
        self.exists = None

    def __str__(self):

        return "run on %s [%s] for job %d" % \
               ( self.node.name,
                 self.cluster.name,
                 self.job.sched_id )

    def existing(self, db):
        """Returns True if theRunt already exists in database (same cluster,
           node and job), or False if not.
        """

        req = """
                SELECT node_id
                  FROM Run
                 WHERE cluster_id = %s
                   AND node_id = %s
                   AND job_id = %s
              """
        params = ( self.cluster.cluster_id,
                   self.node.node_id,
                   self.job.job_id )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("run %s not found in DB", str(self))
            self.exists = False
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several run found in DB for run %s" \
                      % (str(self)))
        else:
            logger.debug("run %s found in DB", str(self))
            self.exists = True
        return self.exists

    def save(self, db):
        """Insert Run in database. It first makes sure that the Run does not
           already exist in database yet by calling Run.existing() method if
           needed. If the Run already exists in database, it raises
           HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert run %s since already existing in "\
                    "database" % (str(self)))

        req = """
                INSERT INTO Run ( job_id,
                                  node_id,
                                  cluster_id )
                VALUES (%s, %s, %s)
              """
        params = ( self.job.job_id,
                   self.node.node_id,
                   self.cluster.cluster_id )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.exists = True
