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
Schema of the ``Project`` table in HPCStats database:

.. code-block:: sql

    Project(
      project_id          SERIAL,
      project_code        character varying(30) NOT NULL,
      project_description text,
      domain_id           character varying(4),
      CONSTRAINT Project_pkey PRIMARY KEY (project_id),
      CONSTRAINT Project_unique UNIQUE (project_code)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError
from HPCStats.Model.Domain import Domain

class Project(object):
    """Model class for the Project table"""

    def __init__(self, domain, code, description, project_id=None):

        self.project_id = project_id
        self.code = code
        self.description = description

        self.domain = domain

    def __str__(self):

        return "project %s [%s]: %s" \
                 % (self.code,
                    self.domain,
                    self.description)

    def __eq__(self, other):

        return other.code == self.code

    def find(self, db):
        """Search the Project in the database based on its code. If exactly
           one project matches in database, set project_id attribute properly
           and returns its value. If more than one project matches, raises
           HPCStatsDBIntegrityError. If no project is found, returns None.
        """

        req = """
                SELECT project_id
                  FROM Project
                 WHERE project_code = %s
              """
        params = ( self.code, )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("project %s not found in DB", str(self))
            return None
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several project_id found in DB for project %s" \
                      % (str(self)))
        else:
            self.project_id = db.cur.fetchone()[0]
            logger.debug("project %s found in DB with id %d",
                         str(self),
                         self.project_id )
            return self.project_id

    def load(self, db):
        """Load the Project based on the content of the DB and set objects
           attributes accordingly. The project_id attribute must have been
           set previously, typically by calling find() method. It raises
           raises HPCStatsRuntimeError if the Project is not found in DB.
        """

        if self.project_id is None:
            raise HPCStatsRuntimeError(
                    "could not load project %s since not found in database" \
                      % (str(self)))

        req = """
                SELECT project_code,
                       project_description,
                       domain_id
                  FROM Project
                 WHERE project_id = %s
              """
        params = ( self.project_id, )
        db.execute(req, params)
        # We know here there is only one result thanks to existing() method
        result = db.cur.fetchone()
        self.code = result[0]
        self.description = result[1]
        # build the Domain object with the key found in DB
        domain_key = result[2]
        self.domain = Domain(domain_key, None)

    def save(self, db):
        """Insert Project in database. You must make sure that the Project does
           not already exist in database yet (typically using Project.find()
           method else there is a risk of future integrity errors because of
           duplicated clusters. If project_id attribute is set, it raises
           HPCStatsRuntimeError.
        """

        if self.project_id is not None:
            raise HPCStatsRuntimeError(
                    "could not insert project %s since already existing in "\
                    "database" \
                      % (str(self)))

        req = """
                INSERT INTO Project ( project_code,
                                      project_description,
                                      domain_id )
                VALUES ( %s, %s, %s )
                RETURNING project_id
              """

        params = ( self.code,
                   self.description,
                   self.domain.key )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.project_id = db.cur.fetchone()[0]

    def update(self, db):
        """Update Project description field in database. Raises
           HPCStatsRuntimeError if self.project_id is None.
        """
        if self.project_id is None:
            raise HPCStatsRuntimeError(
                    "could not update project %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Project
                   SET project_description = %s,
                       domain_id = %s
                 WHERE project_id = %s
             """
        params = ( self.description,
                   self.domain.key,
                   self.project_id )

        #print db.cur.mogrify(req, params)
        db.execute(req, params)
