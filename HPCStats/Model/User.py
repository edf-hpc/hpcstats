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
Schema of the ``Userhpc`` table in HPCStats database:

.. code-block:: sql

    Userhpc(
      userhpc_id         SERIAL,
      userhpc_login      character varying(30) NOT NULL,
      userhpc_name       character varying(30) NOT NULL,
      userhpc_firstname  character varying(30) NOT NULL,
      userhpc_department character varying(30),
      CONSTRAINT Userhpc_pkey PRIMARY KEY (userhpc_id),
      CONSTRAINT Userhpc_unique UNIQUE (userhpc_login)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class User(object):

    """Model class for the Userhpc table."""

    def __init__(self, login, firstname, lastname, department, user_id=None):

        self.user_id = user_id
        self.login = login
        self.lastname = lastname
        self.firstname = firstname
        self.department = department

    def __str__(self):

        return str(self.firstname) + " " + str(self.lastname) \
               + " [" + str(self.department) + "] " + str(self.login)

    def __eq__(self, other):

        return self.login == other.login

    def find(self, db):
        """Search the User in the database based on its login. If exactly
           one user matches in database, set user_id attribute properly
           and returns its value. If more than one user matches, raises
           HPCStatsDBIntegrityError. If no user is found, returns None.
        """

        req = """
                SELECT userhpc_id
                  FROM Userhpc
                 WHERE userhpc_login = %s
              """
        params = ( self.login, )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("user %s not found in DB", str(self))
            return None
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several user_id found in DB for user %s" \
                      % (str(self)))
        else:
            self.user_id = db.cur.fetchone()[0]
            logger.debug("user %s found in DB with id %d",
                          str(self),
                          self.user_id )
            return self.user_id

    def save(self, db):
        """Insert User in database. You must make sure that the User does
           not already exist in database yet (typically using User.find()
           method else there is a risk of future integrity errors because of
           duplicated users. If user_id attribute is set, it raises
           HPCStatsRuntimeError.
        """

        if self.user_id is not None:
            raise HPCStatsRuntimeError(
                    "could not insert user %s since already existing in "\
                    "database" \
                      % (str(self)))

        req = """
                INSERT INTO Userhpc ( userhpc_login,
                                      userhpc_firstname,
                                      userhpc_name,
                                      userhpc_department)
                VALUES ( %s, %s, %s, %s)
                RETURNING userhpc_id
              """
        params = ( self.login,
                   self.firstname,
                   self.lastname,
                   self.department )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.user_id = db.cur.fetchone()[0]

    def update(self, db):
        """Update User firstname, lastname and department fields in database.
           Raises HPCStatsRuntimeError is user_id is None.
        """

        if self.user_id is None:
            raise HPCStatsRuntimeError(
                    "could not update user %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Userhpc
                   SET userhpc_firstname = %s,
                       userhpc_name = %s,
                       userhpc_department = %s
                WHERE userhpc_id = %s
              """
        params = ( self.firstname,
                   self.lastname,
                   self.department,
                   self.user_id )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
