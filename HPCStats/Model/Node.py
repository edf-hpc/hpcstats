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
Schema of the ``Node`` table in HPCStats database:

.. code-block:: sql

    Node(
      node_id        SERIAL,
      node_name      character varying(30) NOT NULL,
      node_model     character varying(50) NOT NULL,
      node_nbCpu     integer,
      node_partition character varying(30) NOT NULL,
      node_flops     integer NOT NULL,
      node_memory    integer NOT NULL,
      cluster_id     integer NOT NULL,
      CONSTRAINT Node_pkey PRIMARY KEY (node_id, cluster_id),
      CONSTRAINT Node_unique UNIQUE (node_name, cluster_id)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Node(object):

    """Model class for the Node table."""

    def __init__(self, name, cluster, model, partition,
                 cpu, memory, flops, node_id=None):

        self.node_id = node_id
        self.name = name
        self.cluster = cluster
        self.model = model
        self.partition = partition
        self.cpu = cpu
        self.memory = memory
        self.flops = flops

    def __str__(self):

        return "%s/%s/%s: model: %s cpu:%d Gflops:%.2f memory:%dGB" % \
                   ( self.cluster.name,
                     self.partition,
                     self.name,
                     self.model,
                     self.cpu,
                     self.flops / float(1000**3),
                     self.memory / 1024**3 )

    def __eq__(self, other):

        return other.name == self.name and \
               other.cluster == self.cluster

    def find(self, db):
        """Search the Node in the database based on its name and cluster. If
           exactly one node matches in database, set node_id attribute properly
           and returns its value. If more than one node matches, raises
           HPCStatsDBIntegrityError. If no node is found, returns None.
        """

        req = """
                SELECT node_id
                  FROM Node
                 WHERE node_name = %s
                   AND cluster_id = %s
              """
        params = ( self.name,
                   self.cluster.cluster_id )

        db.execute(req, params)
        nb_rows = db.cur.rowcount

        if nb_rows == 0:
            logger.debug("node %s not found in DB", str(self))
            return None
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several node_id found in DB for node %s" \
                      % (str(self)))
        else:
            self.node_id = db.cur.fetchone()[0]
            logger.debug("node %s found in DB with id %d",
                         str(self),
                         self.node_id )
            return self.node_id

    def save(self, db):
        """Insert Node in database. You must make sure that the Node does not
           already exist in database yet (typically using Node.find() method
           else there is a risk of future integrity errors because of
           duplicated nodes. If node_id attribute is set, it raises
           HPCStatsRuntimeError.
        """

        if self.node_id is not None:
            raise HPCStatsRuntimeError(
                    "could not insert node %s since already existing in "\
                    "database" \
                      % (str(self)))

        req = """
                INSERT INTO Node ( node_name,
                                   cluster_id,
                                   node_model,
                                   node_partition,
                                   node_nbCpu,
                                   node_memory,
                                   node_flops )
                VALUES ( %s, %s, %s, %s, %s, %s, %s )
                RETURNING node_id
              """
        params = ( self.name,
                   self.cluster.cluster_id,
                   self.model,
                   self.partition,
                   self.cpu,
                   self.memory,
                   self.flops )
 
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.node_id = db.cur.fetchone()[0]

    def update(self, db):
        """Update Node partition, cpu, memory and flops fields in database.
           Raises HPCStatsRuntimeError if self.node_id is None.
        """
        if self.node_id is None:
            raise HPCStatsRuntimeError(
                    "could not update node %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Node
                   SET node_model = %s,
                       node_partition = %s,
                       node_nbCpu = %s,
                       node_memory = %s,
                       node_flops = %s
                 WHERE node_id = %s
             """
        params = ( self.model,
                   self.partition,
                   self.cpu,
                   self.memory,
                   self.flops,
                   self.node_id )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
