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
Schema of the ``Account`` table in HPCStats database:

.. code-block:: sql

    Account(
      account_uid      integer NOT NULL,
      account_gid      integer NOT NULL,
      account_creation date NOT NULL,
      account_deletion date NOT NULL,
      userhpc_id       integer NOT NULL,
      cluster_id       integer NOT NULL,
      CONSTRAINT Account_pkey PRIMARY KEY (userhpc_id, cluster_id)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsDBIntegrityError, HPCStatsRuntimeError
from HPCStats.Model.User import User

class Account(object):
    """Model class for the Account table."""

    def __init__(self, user, cluster, uid, gid, creation_date,
                 deletion_date, exists=None):

        self.user = user
        self.cluster = cluster
        self.uid = uid
        self.gid = gid
        self.creation_date = creation_date
        self.deletion_date = deletion_date
        self.exists = exists

    def __str__(self):

        if self.creation_date == None:
            creation_date = "unknown"
        else:
            creation_date = self.creation_date.strftime('%Y-%m-%d')
        if self.deletion_date == None:
            deletion_date = "unknown"
        else:
            deletion_date = self.deletion_date.strftime('%Y-%m-%d')

        return self.user.login \
               + " (" + str(self.uid) + "|" + str(self.gid) + "): " \
               + creation_date + "/" + deletion_date

    def __eq__(self, other):

        return self.cluster.name == other.cluster.name and \
               self.user.login == other.user.login

    def existing(self, db):
        """Returns True if the account already exists in database (same cluster
           and user), or False if not.
        """

        req = """
                SELECT account_uid
                  FROM Account
                 WHERE userhpc_id = %s
                   AND cluster_id = %s
              """
        params = ( self.user.user_id,
                   self.cluster.cluster_id )
        db.execute(req, params)
        nb_rows = db.cur.rowcount
        if nb_rows == 0:
            logger.debug("account %s not found in DB", str(self))
            self.exists = False
        elif nb_rows > 1:
            raise HPCStatsDBIntegrityError(
                    "several account found in DB for account %s" \
                      % (str(self)))
        else:
            logger.debug("account %s found in DB", str(self))
            self.exists = True
        return self.exists

    def load(self, db):
        """Load the Account based on the content of the DB and set objects
           attributes accordingly. It calls existing() method if needed and
           raises HPCStatsRuntimeError if the Account is not found in DB.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is False:
            raise HPCStatsRuntimeError(
                    "could not update load %s since not found in database" \
                      % (str(self)))

        req = """
                SELECT account_uid,
                       account_gid,
                       account_creation,
                       account_deletion
                  FROM Account
                 WHERE userhpc_id = %s
                   AND cluster_id = %s
              """
        params = ( self.user.user_id,
                   self.cluster.cluster_id )
        db.execute(req, params)
        # We know here there is only one result thanks to existing() method
        result = db.cur.fetchone()
        self.uid = result[0]
        self.gid = result[1]
        self.creation_date = result[2]
        self.deletion_date = result[3]

    def save(self, db):
        """Insert Account in database. It first makes sure that the Account
           does not already exist in database yet by calling Account.existing()
           method if needed. If the account already exists in database, it
           raises HPCStatsRuntimeError.
        """

        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is True:
            raise HPCStatsRuntimeError(
                    "could not insert account %s since already existing in "\
                    "database" % (str(self)))

        req = """
                INSERT INTO Account ( account_uid,
                                      account_gid,
                                      account_creation,
                                      account_deletion,
                                      userhpc_id,
                                      cluster_id )
                VALUES ( %s, %s, %s, %s, %s, %s )
              """
        params = ( self.uid,
                   self.gid,
                   self.creation_date,
                   self.deletion_date,
                   self.user.user_id,
                   self.cluster.cluster_id )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.exists = True

    def update(self, db):
        """Update Account uid, gid, creation date and deletion date in
           database. Raises HPCStatsRuntimeError is exists is False.
        """
        
        if self.exists is None: # not checked yet
            self.existing(db)
        if self.exists is False:
            raise HPCStatsRuntimeError(
                    "could not update account %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Account
                   SET account_uid = %s,
                       account_gid = %s,
                       account_creation = %s,
                       account_deletion = %s
                 WHERE userhpc_id = %s
                   AND cluster_id = %s
              """
        params = ( self.uid,
                   self.gid,
                   self.creation_date,
                   self.deletion_date,
                   self.user.user_id,
                   self.cluster.cluster_id )
        #print db.cur.mogrify(req, params)
        db.execute(req, params)

def load_unclosed_users_accounts(db, cluster):
    """Load (User,Account) tuples w/o account deletion date on cluster from
       DB.
    """

    tuples = []
    req = """
            SELECT Userhpc.userhpc_id,
                   userhpc_login,
                   userhpc_name,
                   userhpc_firstname,
                   userhpc_department,
                   account_uid,
                   account_gid,
                   account_creation
             FROM Userhpc,
                  Account
            WHERE Account.cluster_id = %s
              AND Account.userhpc_id = Userhpc.userhpc_id
              AND Account.account_deletion = NULL
          """
    params = ( cluster.cluster_id, )
    db.execute(req, params)
    results = db.cur.fetchall()

    for result in results:
        user_id = result[0]
        login = result[1]
        lastname = result[2]
        firstname = result[3]
        department = result[4]
        uid = result[5]
        gid = result[6]
        creation = result[7]
        user = User(login, firstname, lastname, department, user_id=user_id)
        account = Account(user, cluster, uid, gid, creation, None, exists=True)
        tuples.append((user, account))

    return tuples

def nb_existing_accounts(db, cluster):
    """Return the number of existing account for the cluster in DB."""

    req = """
            SELECT account_uid
              FROM Account
             WHERE cluster_id = %s
          """
    params = ( cluster.cluster_id, )
    db.execute(req, params)
    return db.cur.rowcount
