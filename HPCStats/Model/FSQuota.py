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
Schema of the ``fsquota`` table in HPCStats database:

.. code-block:: sql

    fsquota(
      fsquota_time   timestamp NOT NULL,
      fsquota_name          character varying(30) NOT NULL,
      fsquota_block_KB       integer NOT NULL,
      fsquota_block_quota    integer NOT NULL,
      fsquota_block_limit    integer NOT NULL,
      fsquota_block_in_doubt integer NOT NULL,
      fsquota_block_grace    character varying(30) NOT NULL,
      fsquota_file_files     integer NOT NULL,
      fsquota_file_quota     integer NOT NULL,
      fsquota_file_limit     integer NOT NULL,
      fsquota_file_in_doubt  integer NOT NULL,
      fsquota_file_grace     character varying(30) NOT NULL,
      filesystem_id  integer NOT NULL,
      cluster_id     integer NOT NULL,
      CONSTRAINT fsquota_pkey PRIMARY KEY (fsquota_time, filesystem_id, cluster_id, fsquota_name)
    )

"""

import logging
logger = logging.getLogger(__name__)
from datetime import datetime
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class FSQuota(object):
    """Model class for the fsquota table."""

    def __init__(self, filesystem, timestamp, name, block_KB, block_quota,
                 block_limit, block_in_doubt, block_grace, file_files,
                 file_quota, file_limit, file_in_doubt, file_grace):

        self.filesystem = filesystem
        self.timestamp = timestamp
        self.name = name
        self.block_KB = block_KB
        self.block_quota = block_quota
        self.block_limit = block_limit
        self.block_in_doubt = block_in_doubt
        self.block_grace = block_grace
        self.file_files = file_files
        self.file_quota = file_quota
        self.file_limit = file_limit
        self.file_in_doubt = file_in_doubt
        self.file_grace = file_grace
        self.exists = None

    def __str__(self):

        return "FSQuota for %s on %s: at %s %s/%s/%s bytes %s/%s/%s files" % \
                   ( self.name,
                     self.filesystem,
                     self.timestamp,
                     self.block_KB,
                     self.block_quota,
                     self.block_limit,
                     self.file_files,
                     self.file_quota,
                     self.file_limit)

    def existing(self, db):
        """Returns True if the FSQuota already exists in database (same cluster,
           filesystem, name and timestamp), or False if not.
        """

        req = """
                SELECT fsquota_time
                  FROM fsquota
                 WHERE cluster_id = %s
                   AND filesystem_id = %s
                   AND fsquota_name = %s
                   AND fsquota_time = %s
              """
        params = ( self.filesystem.cluster.cluster_id,
                   self.filesystem.fs_id,
                   self.name,
                   self.timestamp )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("fsusage %s not found in DB", str(self))
            self.exists = False
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several fsusage found in DB for fsusage %s" \
                      % (str(self)))
        else:
            logger.debug("fsusage %s found in DB", str(self))
            self.exists = True
        return self.exists

    def save(self, db):
        """Insert FSQuota in database. It first makes sure that the FSQuota
           does not already exist in database yet by calling FSQuota.existing()
           method if needed. If the fsquota already exists in database, it
           raises HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert fsquota %s since already existing in "\
                    "database" % (str(self)))

        req = """
                INSERT INTO fsquota ( filesystem_id,
                                      cluster_id,
                                      fsquota_time,
                                      fsquota_name,
                                      fsquota_block_KB,
                                      fsquota_block_quota,
                                      fsquota_block_limit,
                                      fsquota_block_in_doubt,
                                      fsquota_block_grace,
                                      fsquota_file_files,
                                      fsquota_file_quota,
                                      fsquota_file_limit,
                                      fsquota_file_in_doubt,
                                      fsquota_file_grace )
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )
              """
        params = ( self.filesystem.fs_id,
                   self.filesystem.cluster.cluster_id,
                   self.timestamp,
                   self.name,
                   self.block_KB,
                   self.block_quota,
                   self.block_limit,
                   self.block_in_doubt,
                   self.block_grace,
                   self.file_files,
                   self.file_quota,
                   self.file_limit,
                   self.file_in_doubt,
                   self.file_grace )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)

def get_last_fsquota_datetime(db, cluster, filesystem):#, name
    """Get the datetime of the last fsquota for the fs and the name in DB."""

    req = """
            SELECT MAX(fsquota_time) AS last_usage
              FROM fsquota
             WHERE cluster_id = %s
               AND filesystem_id = %s
               
          """#AND fsquota_name = %s
    params = ( cluster.cluster_id,
               filesystem.fs_id)
              # name )
    db.execute(req, params)
    if db.cur.rowcount == 0:
        return datetime(1970, 1, 1, 0, 0)
    else:
        return db.cur.fetchone()[0]
