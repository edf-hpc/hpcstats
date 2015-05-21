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
Model class for the fsusage table:

fsusage(
  fsusage_time  timestamp NOT NULL,
  fsusage_usage real NOT NULL,
  filesystem_id integer NOT NULL,
  cluster_id    integer NOT NULL,
  CONSTRAINT fsusage_pkey PRIMARY KEY (fsusage_time, filesystem_id, cluster_id)
)

"""

import logging
from datetime import datetime
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class FSUsage(object):

    def __init__(self, filesystem, datetime, usage):

        self.filesystem = filesystem
        self.datetime = datetime
        self.usage = usage
        self.exists = None

    def __str__(self):

        return "FSUsage %s [%s]: at %s %s% usage" % \
                   ( self.filesystem.name,
                     self.filesystem.cluster.name,
                     self.datetime,
                     self.usage )

    def existing(self, db):
        """Returns True if the FSUsage already exists in database (same cluster,
           filesystem and datetime), or False if not.
        """

        req = """
                SELECT fsusage_time
                  FROM fsusage
                 WHERE cluster_id = %s
                   AND filesystem_id = %s
                   AND fsusage_time = %s
              """
        params = ( self.filesystem.cluster.cluster_id,
                   self.filesystem.fs_id,
                   self.datetime )
        cur = db.cur
        cur.execute(req, params)
        nb_rows = cur.rowcount
        if nb_rows == 0:
            logging.debug("fsusage %s not found in DB" % (str(self)))
            self.exists = False
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several fsusage found in DB for fsusage %s" \
                      % (str(self)))
        else:
            logging.debug("fsusage %s found in DB" % (str(self)))
            self.exists = True
        return self.exists

    def save(self, db):
        """Insert FSUsage in database. It first makes sure that the FSUsage
           does not already exist in database yet by calling FSUsage.existing()
           method if needed. If the fsusage already exists in database, it
           raises HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert fsusage %s since already existing in "\
                    "database" % (str(self)))


        req = """
                INSERT INTO fsusage ( filesystem_id,
                                      cluster_id,
                                      fsusage_time,
                                      fsusage_usage )
                VALUES ( %s, %s, %s, %s )
              """
        params = ( self.filesystem.fs_id,
                   self.filesystem.cluster.cluster_id,
                   self.datetime,
                   self.usage )

        cur = db.cur
        #print cur.mogrify(req, params)
        cur.execute(req, params)


def get_last_fsusage_datetime(db, cluster, fs):
    """Get the datetime of the last fsusage for the fs in DB."""

    req = """
            SELECT MAX(fsusage_time) AS last_usage
              FROM fsusage
             WHERE cluster_id = %s
               AND filesystem_id = %s
          """
    params = ( cluster.cluster_id,
               fs.id )
    cur = self.db.cur
    cur.execute(req, params)
    if cur.rowcount == 0:
        return datetime(1970, 1, 1, 0, 0)
    else:
        return cur.fetchone()[0]
