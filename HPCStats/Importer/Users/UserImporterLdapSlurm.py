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

"""This module contains the UserImporterLdapSlurm class."""

import MySQLdb
import _mysql_exceptions
from datetime import date
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors
from HPCStats.Importer.Users.UserImporterLdap import UserImporterLdap
from HPCStats.Model.User import User
from HPCStats.Model.Account import Account, load_unclosed_users_accounts, nb_existing_accounts

class UserImporterLdapSlurm(UserImporterLdap):

    """This class inherits from UserImporterLdap so it imports users from LDAP
       directory and ensure that accounts from DB are closed properly as well.
       But it also imports the list of users known in Slurm DB and tries to get
       information about them in LDAP. This is particularly usefull for users
       that are still in LDAP but not in cluster user group anymore since these
       users have not been imported by UserImporterLdap on purpose.
    """

    def __init__(self, app, db, config, cluster):

        super(UserImporterLdapSlurm, self).__init__(app, db, config, cluster)

        section = self.cluster.name + '/slurm'

        self.dbhost = config.get(section, 'host')
        self.dbport = int(config.get(section, 'port'))
        self.dbname = config.get(section, 'name')
        self.dbuser = config.get(section, 'user')
        self.dbpass = config.get_default(section, 'password', None)
        self.prefix = config.get_default(section, 'prefix', self.cluster.name)

        self.users_acct_slurm = None

        self.conn = None
        self.cur = None

    def connect_db(self):
        """Connect to cluster Slurm database and set conn/cur attribute
           accordingly. Raises HPCStatsSourceError in case of problem.
        """

        try:
            conn_params = {
               'host': self.dbhost,
               'user': self.dbuser,
               'db': self.dbname,
               'port': self.dbport,
            }
            if self.dbpass is not None:
                conn_params['passwd'] = self.dbpass

            self.conn = MySQLdb.connect(**conn_params)
            self.cur = self.conn.cursor()
        except _mysql_exceptions.OperationalError as error:
            raise HPCStatsSourceError( \
                    "connection to Slurm DBD MySQL failed: %s" % (error))

    def disconnect_db(self):
        """Disconnect from cluster Slurm database."""

        self.cur.close()
        self.conn.close()

    def load(self):

        super(UserImporterLdapSlurm, self).load()

        self.load_slurm_users()

        for user, account in self.users_acct_slurm:
            if user not in self.users:
                self.users.append(user)
                self.accounts.append(account)

    def load_slurm_users(self):

        self.users_acct_slurm = []

        self.connect_db()

        req = """
                SELECT DISTINCT user
                  FROM %s_assoc_table
              """ % (self.prefix)

        params = ( )
        self.cur.execute(req, params)

        while (1):
            row = self.cur.fetchone()
            if row == None:
                break

            login = row[0]

            searched_user = User(login, None, None, None)
            user = self.find_user(searched_user)
            if user is None:
                member = self.get_user_account_from_login(login)
                if member is None:
                    self.log.warn(Errors.E_U0004,
                                  "slurm user %s could not be found in " \
                                  "LDAP, ignoring this user", login)
                else:
                    self.log.debug("slurm user %s found in LDAP", login)
                    self.users_acct_slurm.append(member)

        self.disconnect_db()

    def update(self):

        super(UserImporterLdapSlurm, self).update()

        default_account_date = date(1970, 1, 1)
        for user, account in self.users_acct_slurm:
            # If the user does not exist we create/update it since having this
            # user in DB could be usefull anyway.
            if not user.find(self.db):
                user.save(self.db)
            else:
                user.update(self.db)
            # For the account, if it already exists, it probably have good
            # creation and deletion date so we do nothing. If it does not exist
            # it is created with default (wrong) creation/deletion dates.
            if not account.existing(self.db):
                self.log.info("account for slurm user %s saved with " \
                              "default dates in DB", user.login)
                account.deletion_date = default_account_date
                account.creation_date = default_account_date
                account.save(self.db)
