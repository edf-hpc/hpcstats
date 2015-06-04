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
Sector table in HPCStatsDB:

Sector(
  sector_key    character varying(5) NOT NULL,
  sector_name   character varying(25),
  domain_id     character varying(4) NOT NULL,
  CONSTRAINT Sector_pkey PRIMARY KEY (sector_key, domain_id)
)

"""

import logging
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Sector(object):

    """Model class for the Sector table."""

    def __init__(self, domain, key, name):

        self.key = key
        self.name = name
        self.domain = domain

        self.exists = None

    def __str__(self):

        return "sector (%s): [%s] %s" % (self.domain.key, self.key, self.name)

    def __eq__(self, sector):

        return sector.domain.key == self.domain.key and \
               sector.key == self.key

    def existing(self, db):
        """Returns True if the Sector already exists in database (same key and
           domain), or False if not.
        """

        req = """
                SELECT sector_key
                  FROM Sector
                 WHERE sector_key = %s
                   AND domain_id = %s
              """
        params = ( self.key, self.domain.key )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logging.debug("sector %s not found in DB", str(self))
            self.exists = False
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several sector found in DB for sector %s" \
                      % (str(self)))
        else:
            logging.debug("sector %s found in DB", str(self))
            self.exists = True
        return self.exists

    def save(self, db):
        """Insert Sector in database. It first makes sure that the Sector does
           not already exist in database yet by calling Sector.existing()
           method if needed. If the sector already exists in database, it
           raises HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert sector %s since already existing in "\
                    "database" % (str(self)))

        req = """
                INSERT INTO Sector ( sector_key,
                                     sector_name,
                                     domain_id )
                VALUES ( %s, %s, %s )
              """
        params = ( self.key,
                   self.name,
                   self.domain.key )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.exists = True

    def update(self, db):
        """Update Sector name in database. Raises HPCStatsRuntimeError if
           exists is False.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is False:
            raise HPCStatsRuntimeError(
                    "could not update sector %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Sector
                   SET sector_name = %s
                 WHERE sector_key = %s
                   AND domain_id = %s
              """
        params = ( self.name,
                   self.key,
                   self.domain.key )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
