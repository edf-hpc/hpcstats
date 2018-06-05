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

"""This module contains the UserImporterLdap class."""

import os
import ldap
import base64
import re
from datetime import date
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Utils import decypher
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors
from HPCStats.Importer.Users.UserImporter import UserImporter
from HPCStats.Model.User import User
from HPCStats.Model.Account import Account, load_unclosed_users_accounts, nb_existing_accounts

class UserImporterLdap(UserImporter):

    """This UserImporter is a bit tricky since it also has to calculate start
       and end datetime of users' Accounts. For this purpose, the load() method
       must first get all user accounts that are currently defined w/o end
       datetime in database to find out if they have disapeared or not in LDAP
       directory. If yes, update the account end datetime with todays date.
    """
    def __init__(self, app, db, config, cluster):

        super(UserImporterLdap, self).__init__(app, db, config, cluster)

        ldap_section = self.cluster.name + '/ldap'

        self._ldapurl = config.get(ldap_section, 'url')
        self._ldapbase = config.get(ldap_section, 'basedn')
        self._ldapdn = config.get(ldap_section, 'dn')
        self._ldaphash = config.get(ldap_section, 'phash')
        self.ldap_password = \
          base64.b64decode(decypher(base64.b64decode(self._ldaphash)))
        self._ldapcert = config.get_default(ldap_section, 'cert', None)

        self._ldapgroups = []
        group_list = config.get_default(ldap_section, 'groups', None)
        if group_list is not None:
            self._ldapgroups = group_list.split(',')
        single_ldapgroup = config.get_default(ldap_section, 'group', None)
        if single_ldapgroup is not None:
            self.log.warn(Errors.E_U0005,
                          "Deprecated config option,"
                          "'group' is replaced by 'groups'")
            self._ldapgroups += [single_ldapgroup]

        self.ldap_rdn_people = config.get_default(ldap_section,
                                                  'rdn_people',
                                                  'ou=people')
        self.ldap_rdn_groups = config.get_default(ldap_section,
                                                  'rdn_groups',
                                                  'ou=groups')

        self.ldap_dn_people = self.ldap_rdn_people + ',' + self._ldapbase
        self.ldap_dn_groups = self.ldap_rdn_groups + ',' + self._ldapbase
        self.group_dpt_search = config.get(ldap_section, 'group_dpt_search')
        self.group_dpt_regexp = config.get(ldap_section, 'group_dpt_regexp')
        self.default_subdir = config.get_default(ldap_section,
                                                 'default_subdir',
                                                 'unknown')

        self.strict_user_membership = config.get_default( \
                                               'constraints',
                                               'strict_user_membership',
                                               True,
                                               bool)

        self.groups_alias_file = config.get_default(ldap_section,
                                                    'groups_alias_file',
                                                    None)
        self.groups_alias = {} # hash of aliases

        self.users_acct_ldap = None
        self.users_acct_db = None

        self.ldap_conn = None

    def connect_ldap(self):
        """Connect to LDAP directory and set ldap_conn attribute accordingly.
           Raises HPCStatsSourceError in case of error.
        """

        if self._ldapcert is not None:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self._ldapcert)
        try:
            self.ldap_conn = ldap.initialize(self._ldapurl)
            self.ldap_conn.simple_bind(self._ldapdn, self.ldap_password)
        except ldap.SERVER_DOWN, err:
            raise HPCStatsSourceError( \
                    "unable to connect to LDAP server: %s" % (err))

    def check(self):
        """Check the LDAP directory is available for connections."""

        self.connect_ldap()

        # check groups alias file exist if defined
        if self.groups_alias_file is not None:
            if not os.path.isfile(self.groups_alias_file):
                raise HPCStatsSourceError( \
                        "Groups alias file %s does not exist" \
                          % (self.groups_alias_file))

    def load(self):
        """Load (User,Account) tuples from both LDAP directoy and DB."""

        self.users = []
        self.accounts = []

        self.check()

        self.load_groups_alias()
        self.load_ldap()
        self.load_db()

        # merge everying into self.users and self.accounts attributes

        for user, account in self.users_acct_ldap:
            self.accounts.append(account)
            self.users.append(user)

        for user, account in self.users_acct_db:
            if user not in self.users:
                self.users.append(user)
                self.accounts.append(account)

    def load_groups_alias(self):

        if self.groups_alias_file is not None:
            with open(self.groups_alias_file, 'r') as f_groups_alias:
                for line in f_groups_alias.readlines():
                    s_line = line.split(' ')
                    if len(s_line) != 2:
                        raise HPCStatsSourceError( \
                            "Malformed line in alias file %s" \
                            % (self.groups_alias_file))
                    self.groups_alias[s_line[0].strip()] = s_line[1].strip()

    def load_ldap(self):
        """Load (User,Account) tuples from LDAP directory."""

        self.users_acct_ldap = []
        for group in self._ldapgroups:
            self.users_acct_ldap = list(set(
                self.get_group_members(group) + self.users_acct_ldap
            ))

    def get_group_members(self, group):
        """Return the list of (Users,Account) tuples members of a group in LDAP
           directory.
        """

        search = "(&(objectclass=posixGroup)(cn=" + group + "))"
        self.log.debug("search in: %s %s", self.ldap_dn_groups, search)

        try:
            members = self.ldap_conn.search_s(self.ldap_dn_groups,
                                              ldap.SCOPE_SUBTREE,
                                              search,
                                              [ 'member', 'memberUid' ])
        except ldap.NO_SUCH_OBJECT:
            raise HPCStatsSourceError( \
                    "no result found for group %s in base %s" \
                       % (group, self.ldap_dn_groups))
        # Structure of members is a list of tuples whose 1st member is a
        # string dn and 2nd member is a dict with all attributes for this dn.
        #
        # Here is an example:
        # [ (dn1, {'attr1': 'val1', 'attr2': 'val2' }),
        #   (dn2, {'attr1': 'val3', 'attr2': 'val4' }) ]
        #
        # Uncomment the following line to see content of members in debug
        # mode:
        #self.log.debug("members: %s", members)
        #
        # There should be only one result for the group search. Check this
        # or raise HPCStatsSourceError.

        nb_results = len(members)
        if nb_results == 0:
            raise HPCStatsSourceError( \
                    "no result found for group %s in base %s" \
                      % (group, self.ldap_dn_groups))
        if nb_results > 1:
            raise HPCStatsSourceError( \
                    "too much results (%d) found for group %s in base %s" \
                      % (nb_results, group, self.ldap_dn_groups))

        # Then the goal is to extract the list of user logins out of search
        # result.
        #
        # Groups members could be represented using 2 different attributes in
        # LDAP directories:
        #
        #  - member: the value is a dn
        #  - memberUid: the value is just the login of the POSIX user
        #
        # We have to handle both cases properly here.
        #
        # The logins are down-cased here systematically. This way HPCStats only
        # manipulates down-cased logins then, just as Slurm does.

        logins = None
        # get attributes of 1st search result, the only one to consider
        first_res_attr = members[0][1]
        if first_res_attr.has_key('member'):
            # Extract the logins out of a list of dn strings and append it to
            # logins. Here is an example:
            # [ 'uid=foo,ou=people,dc=company,dc=tld',
            #   'uid=bar,ou=people,dc=company,dc=tld' ]
            # -> [ 'foo', 'bar']
            logins = [ member.split(',')[0].split('=')[1].lower()
                       for member in first_res_attr['member'] ]
        if first_res_attr.has_key('memberUid'):
            logins = [ member.lower()
                       for member in first_res_attr['memberUid'] ]

        # Uncomment the following line to see content of logins in debug
        # mode:
        #self.log.debug("logins: %s", logins)

        members = [ self.get_user_account_from_login(login)
                    for login in logins ]
        # Filter out None eventually returned by get_user_account_from_login()
        members = filter(None, members)
        return members

    def get_user_account_from_login(self, login):
        """Returns (User,Account) objects tuple with information found in LDAP
           for the login in parameter. The login in parameter must be
           down-cased.

           The created account have None creation date and deletion date. It is
           up-to update() method to set them well.

           When no account could be found in LDAP directory for the login, if
           strict_user_membership attribute is True, this function raises an
           HPCStatsSourceError exception. If the attribute is False, None is
           returned.
        """

        def_keys = [ "uid", "uidNumber", "gidNumber",
                     "sn", "createTimestamp", "givenName" ]

        userdn = "uid=%s,%s" % (login, self.ldap_dn_people)
        search = "uid=%s" % (login)

        # uid search in LDAP is case-insensitive so it matches even if the
        # login is stored upper-cased.
        self.log.debug("search in: %s %s", self.ldap_dn_people, search)
        try:
            user_res = self.ldap_conn.search_s(self.ldap_dn_people,
                                               ldap.SCOPE_SUBTREE,
                                               search, def_keys)
        except ldap.NO_SUCH_OBJECT:
            msg = "no result found for user %s in base %s" \
                    % (login, self.ldap_dn_people)
            if self.strict_user_membership:
                raise HPCStatsSourceError(msg)
            else:
                self.log.warn(Errors.E_U0001, msg)
                return None

        # Structure of user_res is a list of tuples whose 1st member is a
        # string dn and 2nd member is a dict with all attributes for this dn.
        #
        # Here is an example:
        # [ (dn1, {'attr1': 'val1', 'attr2': 'val2' }),
        #   (dn2, {'attr1': 'val3', 'attr2': 'val4' }) ]
        #
        # Uncomment the following line to see content of members in debug
        # mode:
        #self.log.debug("user_res: %s", user_res)
        #
        # There should be only one result for the group search. Check this
        # or raise HPCStatsSourceError.

        nb_results = len(user_res)
        if nb_results == 0:
            msg = "no result found for user %s in base %s" \
                    % (login, self.ldap_dn_people)
            if self.strict_user_membership:
                raise HPCStatsSourceError(msg)
            else:
                self.log.warn(Errors.E_U0001, msg)
                return None
        if nb_results > 1:
            raise HPCStatsSourceError( \
                    "too much results (%d) found for user %s in base %s" \
                    % (nb_results, login, self.ldap_dn_people))

        # Then extract information from attributes of 1st result
        user_attr = user_res[0][1]

        firstname_attr = 'givenName'
        # Firstname is optional, set to None (with warn) if not found.
        if user_attr.has_key(firstname_attr):
            firstname = user_attr[firstname_attr][0]
        else:
            firstname = None
            self.log.warn(Errors.E_U0002,
                          "dn %s does not have %s attribute on %s",
                          userdn, firstname_attr, self._ldapurl)

        lastname = user_attr['sn'][0]
        uid = int(user_attr['uidNumber'][0])
        gid = int(user_attr['gidNumber'][0])

        department = self.get_user_department(login, gid)

        user = User(login, firstname, lastname, department)
        account = Account(user, self.cluster, uid, gid, None, None)
        return (user, account)


    def get_user_department(self, login, gid):
        """Search for the user department based on its group membership. If
           unable to compute a department name this way, use the primary group.
        """
        department = self.get_user_department_groups_member(login)
        if department is not None:
            return department
        return self.get_user_department_prim_group(login, gid)


    def get_user_department_groups_member(self, login):
        """Search for user department based on its groups membership.

           The login in parameter must be downcased.
        """

        userdn_down = "uid=%s,%s" % (login, self.ldap_dn_people)
        userdn_upper = "uid=%s,%s" % (login.upper(), self.ldap_dn_people)

        # Then search users groups in LDAP. Search of member/memberUid in
        # LDAP is case-sensitive so we have to try both down-cased and
        # upper-cased login/dn here.
        search = "(&(|(member=%s)(member=%s)(memberUid=%s)(memberUid=%s))" \
                 "(cn=%s))" \
                   % (userdn_down, userdn_upper, login,
                      login.upper(), self.group_dpt_search)
        self.log.debug("search in: %s %s", self.ldap_dn_groups, search)
        user_groups = self.ldap_conn.search_s(self.ldap_dn_groups,
                                              ldap.SCOPE_SUBTREE,
                                              search,
                                              ["isMemberOf"])

        # Structure of user_groups is a list of tuples whose 1st member is a
        # string dn and 2nd member is a dict with all attributes for this dn.
        #
        # Here is an example:
        # [ (dn1, {'attr1': 'val1', 'attr2': 'val2' }),
        #   (dn2, {'attr1': 'val3', 'attr2': 'val4' }) ]
        #
        # Uncomment the following line to see content of members in debug
        # mode:
        #self.log.debug("user_groups: %s", user_groups)

        department = None
        for user_group in user_groups:
            group_name = user_group[0] # group name in dn on result
            match = re.match(self.group_dpt_regexp, group_name)
            if match:
                m_groups = match.groups()
                direction = m_groups[0]
                subdirection = m_groups[1]
                department = direction + '-' + subdirection
                break

        # if department not found, warn
        if not department:
            self.log.warn(Errors.E_U0003,
                          "department not found for user %s (%s) on " \
                          "cluster %s based on groups membership!",
                          login,
                          userdn_down,
                          self.cluster.name)

        return department

    def get_user_department_prim_group(self, login, gid):
        """Define the user department based on the name of its primary group.
        """

        # Search for the group with the provided gid in LDAP.
        search = "gidNumber=%d" % (gid)
        self.log.debug("search in: %s %s", self.ldap_dn_groups, search)
        prim_group_res = self.ldap_conn.search_s(self.ldap_dn_groups,
                                                 ldap.SCOPE_SUBTREE,
                                                 search,
                                                 ['cn'])

        # Structure of prim_group_res is a list of tuples whose 1st member is a
        # string dn and 2nd member is a dict with all attributes for this dn.
        #
        # Here is an example:
        # [ (dn1, {'cn': ['group1'] }) ]
        #
        # Uncomment the following line to see content of members in debug
        # mode:
        #self.log.debug("prim_group_res: %s", prim_group_res)

        nb_results = len(prim_group_res)
        if nb_results == 0:
            self.log.warn(Errors.E_U0006,
                          "primary group %d not found for user %s on " \
                          "cluster %s!",
                          gid,
                          login,
                          self.cluster.name)
            return None
        if nb_results > 1:
            raise HPCStatsSourceError( \
                    "too much results (%d) found for user %s primary group %d in base %s" \
                    % (nb_results, login, gid, self.ldap_dn_groups))

        # Then extract information from attributes of 1st result
        primary_group = prim_group_res[0][1]['cn'][0]

        # Use alias if defined
        if self.groups_alias.has_key(primary_group):
            alias = self.groups_alias[primary_group]
            self.log.debug("Using alias %s for primary group %s",
                           alias, primary_group)
            primary_group = alias

        # Compose department name with primary group as the direction and
        # default subdirection configuration parameter
        department = primary_group + "-" + self.default_subdir
        self.log.info("user %s is assigned to fake department %s " \
                      "based on the primary group",
                      login, department)

        return department

    def load_db(self):
        """Load (User,Account) tuples w/o account deletion date from DB."""

        self.users_acct_db = load_unclosed_users_accounts(self.db,
                                                          self.cluster)

    def update(self):
        """Update Users and Accounts in DB based on what has been loaded from
           LDAP directory and current DB content.
        """

        new_date = self.get_default_new_date()
        for user, account in self.users_acct_ldap:
            if user.find(self.db) is None:
                # the user nor the account do not exist, create them.
                user.save(self.db)
                account.creation_date = new_date
                account.save(self.db)
            else:
                # update user name, firstname and department
                user.update(self.db)
                # user already exists, check account
                if not account.existing(self.db):
                    account.creation_date = new_date
                    account.save(self.db)
                else:
                    # user and account already exists. In this case, we have
                    # to load the account to check its deletion date and get
                    # its creation date. If its deletion date is not None, it
                    # means the account has been re-opened. In this case, we
                    # simply remove its deletion date.
                    account.load(self.db)
                    if account.deletion_date is not None:
                        account.deletion_date = None
                        account.update(self.db)

        users_ldap = [ user for user, account in self.users_acct_ldap ]

        for user, account in self.users_acct_db:
            if user not in users_ldap:
                account.deletion_date = date.today()
                account.update(self.db)

    def get_default_new_date(self):
        """Returns the date that is used as creation date for new accounts.
           If there is no account for this cluster in DB yet, we consider this
           is an import from scratch and the creation date is epoch. Else the
           creation date is today.
        """

        if nb_existing_accounts(self.db, self.cluster) == 0:
            return date(1970, 1, 1)
        else:
            return date.today()
