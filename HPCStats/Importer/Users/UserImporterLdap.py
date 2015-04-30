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

from HPCStats.Importer.Users.UserImporter import UserImporter
from HPCStats.Model.User import User
import ldap
from datetime import datetime, date
import base64
import logging
import sys
import re

class UserImporterLdap(UserImporter):

    def __init__(self, app, db, config, cluster):

        super(UserImporterLdap, self).__init__(app, db, config, cluster)

        ldap_section = self.cluster.name + "/ldap"

        self._ldapurl = config.get(ldap_section,"url")
        self._ldapbase = config.get(ldap_section,"basedn")
        self._ldapdn = config.get(ldap_section,"dn")
        self._ldaphash = config.get(ldap_section,"phash")
        self._auth_cert = config.get(ldap_section, "auth_cert")
        self._ldapcert = config.get(ldap_section, "cert")
        self._ldapgroup = config.get(ldap_section, "group")
       
        try:            
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self._ldapcert)
            self._ldapconn = ldap.initialize(self._ldapurl)
            self._ldapconn.simple_bind(self._ldapdn, base64.b64decode(self.decypher(base64.b64decode(self._ldaphash))))
        except ldap.SERVER_DOWN as e:
            logging.error("connection to LDAP failed: %s", e)
            raise RuntimeError

    def create_user_from_db(self, db_user):
        user = User( name = db_user[0],
            login = db_user[1],
            cluster_name = db_user[2],
            department = db_user[3],
            uid = db_user[6],
            gid = db_user[7],
            creation_date = db_user[4],
            deletion_date = db_user[5])
        return user

    def get_all_users_from_db(self, db):
        users_from_db = []
        cur = db.cur
        cur.execute("SELECT * FROM users WHERE cluster = %s",
            (self.cluster.name,) )
        results = cur.fetchall()
        for user in results:
            users_from_db.append(self.create_user_from_db(user))
        return users_from_db
     
        
    def get_members_from_group(self, group):
            if self.cluster.name != 'casanova':
              self._ldap_users = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"(&(objectclass=posixGroup)(cn=" + group + "))", ["memberUid"])
            else:
              self._ldap_users = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"(&(objectclass=posixGroup)(cn=" + group + "))", ["member"])

            return self._ldap_users    
    
    def get_user_from_id(self, uid):
        if self.cluster.name == 'casanova':
            self._ldappeople = "ou=people,dc=calibre,dc=edf,dc=fr"
            def_member = "member=uid="
            def_department = "department"
            def_keys = ["uid","uidNumber","gidNumber","cn","createTimestamp"]
            def_ldapuser = str(uid).lower() + "," + self._ldappeople
        else:
            self._ldappeople = "ou=Personnes,dc=der,dc=edf,dc=fr"
            def_member = "memberUid="
            def_department = "departmentNumber"
            def_keys = ["uid","uidNumber","gidNumber","sn","createTimestamp", "givenName","departmentNumber"]
            def_ldapuser = str(uid).upper()
        # get ldap user info attribut defined by def_keys
        self._ldap_users_info = self._ldapconn.search_s(self._ldappeople, \
                                                       ldap.SCOPE_SUBTREE,
                                                       "uid=" + str(uid),\
                                                       def_keys)
        # get secondary group of the user to define departement values
        secondary_group = self._ldapconn.search_s(self._ldapbase,\
                                                  ldap.SCOPE_SUBTREE, \
                                                  "(&(" + \
                                                  def_member + \
                                                  def_ldapuser + \
                                                  ")(cn=*dp*))",["isMemberOf"])
        if len(secondary_group) is 1:
            match = re.match(r"cn=(.+)-dp-(.+),ou(.+)",secondary_group[-1][0]).groups()
            direction = match[0]
            group = match[1]
            match_department = direction + '-' + group
        else:
            match_department = "OMITTED"
        if len(self._ldap_users_info) > 0:
            self._ldap_users_info[0][1][def_department] = [match_department]
        return self._ldap_users_info

    def get_all_users(self):
        if self.cluster.name != 'casanova':
           _attr = "memberUid"
        else:
           _attr = "member"

        users = []
        self._members = self.get_members_from_group(self._ldapgroup)
        logging.info("list of uidMembers : %s" % (self._members))
        for item in self._members:
            logging.info("item0 => %s :" % (item[0]))

            if item[1] != {}:
                logging.info("item1 => %s \n" % (' '.join(item[1][_attr])))

                for member in item[1][_attr]:
                    if self.cluster.name != 'casanova':
                      user_info = self.get_user_from_id(member)
                    else:
                      user_info = self.get_user_from_id(member.split(",")[0].split("=")[1])
                    if len(user_info) >= 1:
                        lu = user_info[0][1]
                        for clef, valeur in user_info[0][1].items():
                           logging.info("%s : %s" % (clef, valeur[0]))
                           
                        if self.cluster.name == "casanova":
                            def_department = 'department'
                            def_name = lu["cn"][0]
                        else:
                            def_department = 'departmentNumber'
                            try :
                                def_name = lu["givenName"][0] + " " + lu["sn"][0]
                            except KeyError as ke:
                                def_name = lu["sn"][0]

                        createTimestamp = lu["createTimestamp"][0]
                        logging.info("createTimestamp => %s" % (createTimestamp))
                        if def_department in lu.keys():
                            _department = lu[def_department][0]
                        else:
                            _department = "OMITTED"
                        user = User( name = def_name,
                                    login = lu["uid"][0].lower(),
                                    cluster_name = self.cluster.name,
                                    uid = lu["uidNumber"][0],
                                    gid = lu["gidNumber"][0],
                                    department = _department,
                                    creation_date = datetime.strptime(createTimestamp[:14], "%Y%m%d%H%M%S"))
                        users.append(user)
                    else:
                        logging.debug("user %s not found in defined OU" % (member))
        return users

    def update_users(self):
        users = self.get_all_users()
        users_db = self.get_all_users_from_db(self.db)

        # scrutation of the db users table
        for user in users_db:
            boolean = False
            user_from_ldap = self.get_user_from_id(user.get_login())
            # verify if user still exist 
            if not (user_from_ldap):
                # update deletion date if necessary
                if not user.get_deletion_date():
                    logging.debug("updating deletion date for user : %s set from null to now", \
                                   user.get_login())
                    user.set_deletion_date(datetime.now())
                    boolean = True
            else:
                # traite the case of user be back in the group
                if user.get_deletion_date(): 
                    logging.debug("updating deletion date for user : %s set from %s to null", \
                                   user.get_login(), \
                                   user.get_deletion_date())
                    user.set_deletion_date(None)
                    logging.debug("updating creation date for user : %s set from %s to now", \
                                   user.get_login(), \
                                   user.get_creation_date())
                    user.set_creation_date(datetime.now())
                    boolean = True
                # update departement column if necesary
                if self.cluster.name == "casanova":
                    def_department = 'department'
                    user_name = user_from_ldap[0][1]["cn"][0]
                else:
                    def_department = 'departmentNumber'
                    try :
                        def_name = user_from_ldap[0][1]["givenName"][0] \
                                   + user_from_ldap[0][1]["sn"][0]
                    except KeyError as ke:
                        def_name = user_from_ldap[0][1]["sn"][0]
                        user_name = def_name
                if def_department in user_from_ldap[0][1].keys():
                    user_department = user_from_ldap[0][1][def_department][0]
                else:
                    user_department = "OMITTED"
                if user.get_department() != user_department:
                    logging.debug("updating department for user %s set from %s to %s", \
                                       user.get_login(), \
                                       user.get_department(), \
                                       user_department)
                    user.set_department(user_department)
                    boolean = True
                # update name column if necesary
                if user.get_name() != user_name: 
                    logging.debug("updating name for user %s set from %s to %s", \
                                   user.get_login(), \
                                   user.get_name(), \
                                   user_name)
                    user.set_name(user_name)
                    boolean = True
            if boolean is True:
                logging.debug("update user %s on cluster %s", \
                               user.get_login(),
                               self.cluster.name)
                try :
                    user.update(self.db)
                except :
                    logging.error("problem occured on user update")

        #create users
        for user in users: # scrutation of ldap list users
            if not user.exists_in_db(self.db):
                user.set_creation_date(datetime.now())
                logging.debug("creating user %s", user)
                user.save(self.db) 

    def decypher(self, s):
        x = []
        for i in xrange(len(s)):
            j = ord(s[i])
            if j >= 33 and j <= 126:
                x.append(chr(33 + ((j + 14) % 94)))
            else:
                x.append(s[i])
        return ''.join(x)
