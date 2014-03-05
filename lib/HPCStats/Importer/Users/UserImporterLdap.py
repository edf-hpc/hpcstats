#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Users.UserImporter import UserImporter
from HPCStats.Model.User import User
import ldap
from datetime import datetime, date
import base64
import logging
import sys
class UserImporterLdap(UserImporter):

    def __init__(self, db, config, cluster_name):

        UserImporter.__init__(self, db, cluster_name)

        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        ldap_section = self._cluster_name + "/ldap"

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
        cur = db.get_cur()
        cur.execute("SELECT * FROM users WHERE cluster = %s",
            (self._cluster_name,) )
        results = cur.fetchall()
        for user in results:
            #logging.debug("JBL : test login : %s", user)
            users_from_db.append(self.create_user_from_db(user))
        return users_from_db
     
        
    def get_members_from_group(self, group):
            if self._cluster_name != 'casanova':
              self._ldap_users = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"(&(objectclass=posixGroup)(cn=" + group + "))", ["memberUid"])
            else:
              self._ldap_users = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"(&(objectclass=posixGroup)(cn=" + group + "))", ["member"])

            return self._ldap_users    
    
    def get_user_from_id(self, uid):
        if self._cluster_name == 'casanova':
            self._ldapbase = "ou=people,dc=calibre,dc=edf,dc=fr"
            self._ldap_users_info = self._ldapconn.search_s(self._ldapbase, ldap.SCOPE_SUBTREE, "uid="+str(uid),["uid","uidNumber","gidNumber","cn","createTimestamp"])
        else:
            self._ldapbase = "ou=Personnes,dc=der,dc=edf,dc=fr"
            self._ldap_users_info = self._ldapconn.search_s(self._ldapbase, ldap.SCOPE_SUBTREE, "uid="+str(uid),["uid","uidNumber","gidNumber","sn","createTimestamp", "givenName","departmentNumber"])
        return self._ldap_users_info
        
    def get_all_users(self):
        if self._cluster_name != 'casanova':
           _attr = "memberUid"
        else:
           _attr = "member"

        users = []
        self._members = self.get_members_from_group(self._ldapgroup)
        logging.info("NAN => %s" % (self._members))
        for item in self._members:
            logging.info("NAN item0 => %s :" % (item[0]))
            
            if item[1] != {}:
                logging.info("NAN item1 => %s \n" % (' '.join(item[1][_attr])))
                
                for member in item[1][_attr]:
                    if self._cluster_name != 'casanova':
                      user_info = self.get_user_from_id(member)
                    else:
                      user_info = self.get_user_from_id(member.split(",")[0].split("=")[1])

                    if len(user_info) >= 1:
                        lu = user_info[0][1]
                        
                        for clef, valeur in user_info[0][1].items():
                           logging.info("NAN => %s : %s" % (clef, valeur[0]))
                           
                        if self._cluster_name == "casanova":
                            createTimestamp = lu["createTimestamp"][0]
                            logging.info("NAN => %s" % (createTimestamp))
                            user = User( name = lu["cn"][0],
                                    #login = lu["uid"][0].upper(),
                                    login = lu["uid"][0].lower(),
                                    cluster_name = self._cluster_name,
                                    uid = lu["uidNumber"][0],
                                    gid = lu["gidNumber"][0],
                                    department = "SEPTEN",
                                    creation_date = datetime.strptime(createTimestamp[:14], "%Y%m%d%H%M%S"))
                        else:    
                            createTimestamp = lu["createTimestamp"][0]
                            logging.info("NAN => %s" % (createTimestamp))
			    # departmentNumber might be empty
			    if 'departmentNumber' in lu.keys():
                                _department = lu["departmentNumber"][0]
                            else:
                                _department = "OMITTED"

                            user = User( name = lu["givenName"][0] + " " + lu["sn"][0],
                                    #login = lu["uid"][0].upper(),
                                    login = lu["uid"][0].lower(),
                                    cluster_name = self._cluster_name,
                                    uid = lu["uidNumber"][0],
                                    gid = lu["gidNumber"][0],
                                    department = _department,
                                    creation_date = datetime.strptime(createTimestamp[:14], "%Y%m%d%H%M%S"))
                        users.append(user)
                    else:
                        logging.error("NAN => user %s not found in defined OU" % (member))
        return users

    def update_users(self):
        users = self.get_all_users()
        users_db = self.get_all_users_from_db(self._db)

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
                # update departement column for casanova if necesary
                if self._cluster_name == "casanova":
                    user_name = user_from_ldap[0][1]["cn"][0]
                    user_department = "SEPTEN"
                    if user.get_department() != user_department:
                        logging.debug("updating department for user %s set from %s to %s", \
                                       user.get_login(), \
                                       user.get_department(), \
                                       user_department)
                        user.set_department(user_department)
                        boolean = True
                else:
                    user_name = user_from_ldap[0][1]["givenName"][0] \
                                     + " " \
                                     + user_from_ldap[0][1]["sn"][0]
                    # update departement column for other cluster if necesary
                    if 'departmentNumber' in user_from_ldap[0][1].keys():
                        user_department = user_from_ldap[0][1]["departmentNumber"][0]
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
                               self._cluster_name)
                user.update(self._db)

        #create users
        for user in users: # scrutation of ldap list users
            if not user.exists_in_db(self._db):
                user.set_creation_date(datetime.now())
                logging.debug("creating user %s", user)
                user.save(self._db) 

    def decypher(self, s):
        x = []
        for i in xrange(len(s)):
            j = ord(s[i])
            if j >= 33 and j <= 126:
                x.append(chr(33 + ((j + 14) % 94)))
            else:
                x.append(s[i])
        return ''.join(x)
