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
Model class for the ContextAccount table:

ContextAccount(
  userhpc_id    character varying(30) NOT NULL,
  cluster_id    integer NOT NULL,
  business_code character varying(30) NOT NULL,
  project_id    integer NOT NULL,
  CONSTRAINT ContextAccount_pkey PRIMARY KEY (userhpc_id, cluster_id, business_code, project_id)
)

"""

import logging
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError

class ContextAccount:

    def __init__(self, cluster, user, business, project):

        self.cluster = cluster
        self.user = user
        self.business = business
        self.project = project

        self.exists = None

    def __str__(self):

        return  "contextaccount cluster: %s user: %s business: %s " \
                "project: %s" \
                  % ( self.cluster.name,
                      self.user.login,
                      self.business.code,
                      self.project.name )


    def existing(self, db):
        """Returns True if the ContextAccount already exists in database (same
           cluster, user, business and project), or False if not.
        """

        req = """
                SELECT userhpc_id
                  FROM ContextAccount
                 WHERE cluster_id = %s
                   AND userhpc_id = %s
                   AND business_code = %s
                   AND project_id = %s
              """
        params = ( self.cluster.cluster_id,
                   self.userhpc.userhpc_id,
                   self.business.code,
                   self.project.project_id )
        cur = db.get_cur()
        cur.execute(req, params)
        nb_rows = cur.rowcount
        if nb_rows == 0:
            logging.debug("contextaccount %s not found in DB" % (str(self)))
            self.exists = False
        elif nb_rows == 1:
            raise HPCStatsDBIntegrityError(
                    "several contextaccount found in DB for " \
                    "contextaccount %s" \
                      % (str(self)))
        else:
            logging.debug("contextaccount %s found in DB" % (str(self)))
            self.exists = True
        return self.exists

    def save(self, db):
        """Insert ContextAccount in database. It first makes sure that the
           ContextAccount does not already exist in database yet by calling
           ContextAccount.existing() method if needed. If the account already
           exists in database, it raises HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert contextaccount %s since already " \
                    "existing in database" % (str(self)))

        req = """
                INSERT INTO ContextAccount ( cluster_id,
                                             userhpc_id,
                                             business_code,
                                             project_id )
                VALUES ( %s, %s, %s, %s )
              """
        params = ( self.cluster.cluster_id,
                   self.user.user_id,
                   self.business.code,
                   self.project.project_id )
        cur = db.get_cur()
        #print cur.mogrify(req, params)
        cur.execute(req, params)
        self.exists = True
