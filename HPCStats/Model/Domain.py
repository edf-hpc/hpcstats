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
# On Calibre systems, the  complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

"""
Schema of the ``Domain`` table in HPCStats database:

.. code-block:: sql

    Domain(
      domain_id   character varying(4) NOT NULL,
      domain_name character varying(30),
      CONSTRAINT Domain_pkey PRIMARY KEY (domain_id),
      CONSTRAINT Domain_unique UNIQUE (domain_name)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class Domain(object):

    """Model class for the Domain table."""

    def __init__(self, key, name):
       
        self.key = key
        self.name = name

        self.exists = None

    def __str__(self):

        return "domain [%s] %s" % (self.key, self.name)

    def __eq__(self, domain):

        return domain.key == self.key

    def existing(self, db):
        """Returns True if the domain already exists in database (same key), or
           False if not.
        """

        req = """
                SELECT domain_id
                  FROM Domain
                 WHERE domain_id = %s
              """
        params = ( self.key, )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("domain %s not found in DB", str(self))
            self.exists = False
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several domain found in DB for domain %s" \
                      % (str(self)))
        else:
            logger.debug("domain %s found in DB", str(self))
            self.exists = True
        return self.exists

    def save(self, db):
        """Insert Domain in database. It first makes sure that the Domain does
           not already exist in database yet by calling Domain.existing()
           method if needed. If the domain already exists in database, it
           raises HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert domain %s since already existing in "\
                    "database" % (str(self)))

        req = """
                INSERT INTO Domain ( domain_id,
                                     domain_name )
                VALUES ( %s, %s )
              """
        params = ( self.key,
                   self.name )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.exists = True

    def update(self, db):
        """Update Domain name in database. Raises HPCStatsRuntimeError if
           exists is False.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is False:
            raise HPCStatsRuntimeError(
                    "could not update domain %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Domain
                   SET domain_name = %s
                 WHERE domain_id = %s
              """
        params = ( self.name,
                   self.key )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
