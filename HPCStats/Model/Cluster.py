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
Schema of the ``Cluster`` table in HPCStats database:

.. code-block:: sql

    Cluster(
      cluster_id   SERIAL,
      cluster_name character varying(30) NOT NULL,
      CONSTRAINT Cluster_pkey PRIMARY KEY (cluster_id),
      CONSTRAINT Cluster_unique UNIQUE (cluster_name)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Cluster(object):
    """Model class for Cluster table"""

    def __init__(self, name, cluster_id=None):

        self.cluster_id = cluster_id
        self.name = name
    
    def __str__(self):

        return self.name

    def __eq__(self, other):

        return self.name == other.name

    def find(self, db):
        """Search the Cluster in the database based on its name. If exactly
           one cluster matches in database, set cluster_id attribute properly
           and returns its value. If more than one cluster matches, raises
           HPCStatsDBIntegrityError. If no cluster is found, returns None.
        """

        req = """
                SELECT cluster_id
                  FROM Cluster
                 WHERE cluster_name = %s
              """
        params = ( self.name, )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("cluster %s not found in DB", str(self))
            return None
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several cluster_id found in DB for cluster %s" \
                      % (str(self)))
        else:
            self.cluster_id = db.cur.fetchone()[0]
            logger.debug("cluster %s found in DB with id %d",
                         str(self),
                         self.cluster_id )
            return self.cluster_id

    def save(self, db):
        """Insert Cluster in database. You must make sure that the Cluster does
           not already exist in database yet (typically using Cluster.find()
           method else there is a risk of future integrity errors because of
           duplicated clusters. If cluster_id attribute is set, it raises
           HPCStatsRuntimeError.
        """

        if self.cluster_id is not None:
            raise HPCStatsRuntimeError(
                    "could not insert cluster %s since already existing in "\
                    "database" \
                      % (str(self)))

        req = """
                INSERT INTO Cluster ( cluster_name )
                VALUES ( %s )
                RETURNING cluster_id
              """
        params = ( self.name, )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.cluster_id = db.cur.fetchone()[0]

    def get_nb_cpus(self, db):
        """Returns the total number of CPUs available on the cluster"""

        if self.cluster_id is None:
            raise HPCStatsRuntimeError(
                    "could not search for data with cluster %s since not " \
                    "found in database" \
                      % (str(self)))

        req = """
                SELECT SUM(node_nbCpu)
                  FROM Node
                 WHERE cluster_id = %s
              """
        params = ( self.cluster_id, )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        return db.cur.fetchone()[0]

    def get_min_datetime(self, db):
        """Returns the start datetime of the oldest started and unfinished
           job on the cluster.
        """

        if self.cluster_id is None:
            raise HPCStatsRuntimeError(
                    "could not search for data with cluster %s since not " \
                    "found in database" \
                      % (str(self)))

        req = """
                SELECT MIN(job_start)
                  FROM Job
                 WHERE cluster_id = %s
                   AND job_state NOT IN ('CANCELLED', 'NODE_FAIL', 'PENDING')
              """
        params = ( self.cluster_id, )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        return db.cur.fetchone()[0]

   
    def get_nb_accounts(self, db, creation_date):
        """Returns the total of users on the cluster whose account have been
           created defore date given in parameter.
        """

        if self.cluster_id is None:
            raise HPCStatsRuntimeError(
                    "could not search for data with cluster %s since not " \
                    "found in database" \
                      % (str(self)))

        req = """
                SELECT COUNT (userhpc_id)
                  FROM Userhpc,
                       Account
                 WHERE Account.userhpc_id = Userhpc.userhpc_id
                   AND Account.account_creation < %s
                   AND Account.cluster_id = %s
              """
        params = (creation_date, self.cluster_id )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        
        return db.cur.fetchone()[0]

    def get_nb_active_users(self, db, start, end):
        """Returns the total number of users who have run job(s) on the cluster
           between start and end datetimes in parameters.
        """

        if self.cluster_id is None:
            raise HPCStatsRuntimeError(
                    "could not search for data with cluster %s since not " \
                    "found in database" \
                      % (str(self)))

        req = """
                SELECT COUNT(DISTINCT userhpc_id)
                  FROM Job
                 WHERE Job.cluster_id = %s,
                   AND ((job_start BETWEEN %s AND %s)
                        OR (job_end BETWEEN %s AND %s)
                        OR (job_start <= %s AND job_end >= %s))
              """
        params = (self.cluster_id, start, end, start, end, start, end)
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        
        return db.cur.fetchone()[0]
