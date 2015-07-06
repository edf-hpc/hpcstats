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
Schema of the ``filesystem`` table in HPCStats database:

.. code-block:: sql

    filesystem(
      filesystem_id   SERIAL,
      filesystem_name character varying(30) NOT NULL,
      cluster_id      integer NOT NULL,
      CONSTRAINT filesystem_pkey PRIMARY KEY (filesystem_id, cluster_id),
      CONSTRAINT filesystem_unique UNIQUE (filesystem_name, cluster_id)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Filesystem(object):
    """Model class for the filesystem table."""

    def __init__(self, mountpoint, cluster, fs_id=None):

        self.fs_id = fs_id
        self.mountpoint = mountpoint
        self.cluster = cluster

    def __str__(self):

        return "filesystem: %s [cluster: %s]" % \
                   ( self.mountpoint,
                     self.cluster.name )

    def __eq__(self, other):

        return other.mountpoint == self.mountpoint and \
               other.cluster == self.cluster

    def find(self, db):
        """Search the Filesystem in the database based on its mountpoint and
           cluster. If exactly one filesystem matches in database, set fs_id
           attribute properly and returns its value. If more than one
           filesystem matches, raises HPCStatsDBIntegrityError. If no
           filesystem is found, returns None.
        """

        req = """
                SELECT filesystem_id
                  FROM filesystem
                 WHERE filesystem_name = %s
                   AND cluster_id = %s
              """
        params = ( self.mountpoint,
                   self.cluster.cluster_id )

        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("filesystem %s not found in DB", str(self))
            return None
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several filesystem_id found in DB for filesystem %s" \
                      % (str(self)))
        else:
            self.fs_id = db.cur.fetchone()[0]
            logger.debug("filesystem %s found in DB with id %d",
                         str(self),
                         self.fs_id )
            return self.fs_id

    def save(self, db):
        """Insert Filesystem in database. You must make sure that the
           Filesystem does not already exist in database yet (typically using
           Filesystem.find() method else there is a risk of future integrity
           errors because of duplicated filesystems. If fs_id attribute is set,
           it raises HPCStatsRuntimeError.
        """

        if self.fs_id is not None:
            raise HPCStatsRuntimeError(
                    "could not insert filesystem %s since already existing " \
                    "in database" \
                      % (str(self)))

        req = """
                INSERT INTO filesystem ( filesystem_name,
                                         cluster_id )
                VALUES ( %s, %s)
                RETURNING filesystem_id
              """
        params = ( self.mountpoint,
                   self.cluster.cluster_id )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.fs_id = db.cur.fetchone()[0]
