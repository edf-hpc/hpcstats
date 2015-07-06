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
Schema of the ``Business`` table in HPCStats database:

.. code-block:: sql

    Business(
      business_code        character varying(30) NOT NULL,
      business_description text NOT NULL,
      CONSTRAINT Business_pkey PRIMARY KEY (business_code)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Business(object):

    """Model class for the Business table."""

    def __init__(self, code, description):

        self.code = code
        self.description = description
        self.exists = None

    def __str__(self):
        if self.description == None:
            description = "(empty)"
        else:
            description = self.description
        return self.code + " - " + description

    def __eq__(self, other):

        return other.code == self.code

    def existing(self, db):
        """Returns True if the business already exists in database (with same
           code), or False if not.
        """

        req = """
                SELECT business_code
                  FROM Business
                 WHERE business_code = %s
              """
        params = ( self.code, )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("business %s not found in DB", str(self))
            self.exists = False
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several businesses found in DB for account %s" \
                      % (str(self)))
        else:
            logger.debug("business %s found in DB", str(self))
            self.exists = True
        return self.exists

    def save(self, db):
        """Insert Business in database. It first makes sure that the Business
           does not already exist in database yet by calling
           Business.existing() method if needed. If the business already exists
           in database, it raises HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert business %s since already existing in "\
                    "database" % (str(self)))

        logger.info("creating business code %s" % str(self))

        req = """
                INSERT INTO Business ( business_code,
                                       business_description )
                VALUES (%s, %s)
              """
        params = ( self.code, self.description )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.exists = True

    def update(self, db):
        """Update Business description in database. Raises HPCStatsRuntimeError
           if exists is False.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is False:
            raise HPCStatsRuntimeError(
                    "could not update business %s since not found in " \
                    "database" \
                      % (str(self)))

        logger.debug("updating business code %s" % str(self))

        req = """
                UPDATE Business
                   SET business_description = %s
                 WHERE business_code = %s
              """
        params = ( self.description,
                   self.code )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
