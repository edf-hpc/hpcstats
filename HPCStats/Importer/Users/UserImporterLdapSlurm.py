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

import ldap
import MySQLdb
import _mysql_exceptions
from datetime import date
import logging
from HPCStats.Importer.Users.UserImporter import UserImporter
from HPCStats.Model.User import User

class UserImporterLdapSlurm(UserImporter):

    def __init__(self, app, db, config, cluster):

        super(UserImporterLdapSlurm, self).__init__(app, db, config, cluster)

        ldap_section = self.cluster.name + "/ldap"
        xls_section = self.cluster.name + "/xls"
        db_section = self.cluster.name + "/slurm"

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

        self._xlsfile = config.get(xls_section,"file")
        self._xlssheetname = config.get(xls_section,"sheet")
        self._xlsworkbook = xlrd.open_workbook(self._xlsfile)
        self._xlssheet = self._xlsworkbook.sheet_by_name(self._xlssheetname)

        self._dbhost = config.get(db_section,"host")
        self._dbport = int(config.get(db_section,"port"))
        self._dbname = config.get(db_section,"name")
        self._dbuser = config.get(db_section,"user")
        self._dbpass = config.get(db_section,"password")
        try:
            self._conn = MySQLdb.connect( host = self._dbhost,
                                          user = self._dbuser,
                                          passwd = self._dbpass,
                                          db = self._dbname,
                                          port = self._dbport )
        except _mysql_exceptions.OperationalError as e:
            logging.error("connection to Slurm DBD MySQL failed: %s", e)
            raise RuntimeError
        self._cur = self._conn.cursor(MySQLdb.cursors.DictCursor)

    def update_users(self):
        users = self.get_all_users()
        for user in users:
            if user.exists_in_db(self.db):
                logging.debug("updating user %s", user)
                user.update_creation_deletion(self.db)
            # Il 'ny a plus de création pour le XLS
            #else:
                #logging.debug("creating user %s", user)
                #user.save(self.db)

        #uids = self._get_unknown_users(self.db)
        #if not uids: 
        #        logging.debug("no unknown users found")
        #else:
        #    for unknown_uid in uids:
        #        user = self.find_with_uid(unknown_uid)
        #        if user:
        #            if user.exists_in_db(self.db):
        #                logging.debug("updating user %s", user)
        #                user.update(self.db)
        #            else:
        #                logging.debug("creating user %s", user)
        #                user.save(self.db)
        #        else:
        #            logging.warning("unknown user with uid %d", unknown_uid)

    def get_all_users(self):
        users = []
        previous_user = None

        # start from row 8 in xls sheet which starts itself from 0
        for rownum in range(8,self._xlssheet.nrows):
            try:
                xls_row = self._xlssheet.row_values(rownum)

                if self._user_row(xls_row):
                    user = self.user_from_xls_row(xls_row)

                    if user.get_cluster_name() == self.cluster.name and (not previous_user or not user == previous_user):

                        [uid, gid] = self.get_ids_from_ldap(user)
                        user.set_uid(uid)
                        user.set_gid(gid)

                        users.append(user)
                        previous_user = user

            except TypeError as e:
                #print "Error in %s: %s" % (self.__class__.__name__, e)
                continue

        return users

    def _user_row(self, xls_row):
        """ Return True is the XLS row refers to a user instead of a project """
        return xls_row[1].encode('utf-8').strip() == "U"

    def get_ids_from_ldap(self, user):
        self._ldapbase = "ou=Personnes,dc=der,dc=edf,dc=fr"
        r = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"uid="+user.get_login(),["uidNumber","gidNumber"])
        try:
            attrib_dict = r[0][1]
            uid = int(attrib_dict['uidNumber'][0])
            gid = int(attrib_dict['gidNumber'][0])
            return [uid, gid]
        except IndexError:
            logging.error("login %s (%s) not found in LDAP",
                           user.get_login(),
                           user.get_name() )
            # loosely search for user with the same name in LDAP
            r = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"cn="+user.get_name(),["uid","uidNumber","gidNumber"])
            if len(r) > 0:
                attrib_dict = r[0][1]
                login = attrib_dict['uid'][0]
                uid = int(attrib_dict['uidNumber'][0])
                gid = int(attrib_dict['gidNumber'][0])
                logging.info("login %s not found in LDAP but found user %s with login %s",
                              user.get_login(),
                              user.get_name(),
                              login )
                return [uid, gid]
            # try in Slurm Database
            else:
                req = """
                    SELECT DISTINCT(id_user) AS uid,
                           id_group AS gid
                     FROM %s_job_table
                     WHERE account = %%s; """ % (self.cluster.name)
                datas = (user.get_login().lower(),)
                nb_rows = self._cur.execute(req, datas)
                if nb_rows == 1:
                    row = self._cur.fetchone()
                    uid = int(row['uid'])
                    gid = int(row['gid'])
                    logging.info("found login %s in SlurmDBD with %d/%d",
                                  user.get_login(),
                                  uid,
                                  gid )
                    return [uid, gid]

                elif nb_rows > 1:
                    logging.info("found login %s in SlurmDBD with incorrect (%d) number of UID/GID",
                                  user.get_login(),
                                  nb_rows )

            return [-1, -1]

    def user_from_xls_row(self, xls_row):

        login = xls_row[2].encode('utf-8').strip()
        if login == "":
            raise TypeError, "login is empty"
        # workaround for a problem on last row
        if type(xls_row[3]) == int:
            raise TypeError, "firstname box is an int instead of {str, unicode}"
        firstname = xls_row[3].encode('utf-8').strip().capitalize()
        lastname = xls_row[4].encode('utf-8').strip().upper()
        department = xls_row[5].encode('utf-8').strip().upper()
        if department == "":
            department = "UNKNOWN"
        project = xls_row[16].encode('utf-8').strip().upper()
        email = xls_row[13].encode('utf-8').strip().lower()
        cluster_name = xls_row[15].encode('utf-8').strip().lower()
        creation = xls_row[6]
        if type(creation) == float and creation != 1.0:
            # see: https://secure.simplistix.co.uk/svn/xlrd/trunk/xlrd/doc/xlrd.html#xldate.xldate_as_tuple-function
            (year,month,day,hour,minute,second) = xlrd.xldate_as_tuple(creation, 0)
            creation_date = date(year, month, day)
        else :
            creation_date = None
        deletion = xls_row[7]
        if type(deletion) == float and deletion != 1.0:
            (year,month,day,hour,minute,second) = xlrd.xldate_as_tuple(deletion, 0)
            deletion_date = date(year, month, day)
        else :
            deletion_date = None

        user = User( name = firstname + " " + lastname,
                     login = login,
                     cluster_name = cluster_name,
                     department = department,
                     creation_date = creation_date,
                     deletion_date = deletion_date )
        return user

    def user_from_ldap_row(self, ldap_row):
        login = ldap_row['uid'][0]
        uid = ldap_row['uidNumber'][0]
        gid = ldap_row['gidNumber'][0]
        name = ldap_row['givenName'][0] + " " + ldap_row['sn'][0]

        department = "UNKNOWN"
        try:
            department = ldap_row['departmentNumber'][0]
            if department == "":
                department = "UNKNOWN"
        except KeyError:
            logging.error("login %s %s (%s/%s) has no department in LDAP",
                           login,
                           name,
                           uid,
                           gid )
        if ldap_row.has_key('mail'):    
            email = ldap_row['mail'][0]
        else:
            email = None
        user = User( name = name,
                     login = login,
                     uid = uid,
                     gid = gid,
                     cluster_name = self.cluster.name,
                     department = department )
        return user

    def user_from_slurm_row(self, slurm_row):
        login = slurm_row['login']
        uid = int(slurm_row['uid'])
        gid = int(slurm_row['gid'])
        user = User( login = login,
                     uid = uid,
                     gid = gid,
                     cluster_name = self.cluster.name )
        return user

    def find_with_uid(self, uid):
        user = None
        # search in LDAP
        r = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"uidNumber="+str(uid),["uid","sn","givenName","mail","uidNumber","gidNumber","departmentNumber"])
        if len(r) > 0:
            attrib_dict = r[0][1]
            user = self.user_from_ldap_row(attrib_dict)
            logging.info("uid %d found in LDAP with user %s",
                          uid,
                          user )
        # else search in SlurmDBD
        else:
            req = """
                SELECT id_user uid,
                       id_group gid,
                       user login
                  FROM %s_assoc_table AS assoc,
                       %s_job_table AS jobs
                 WHERE jobs.id_assoc = assoc.id_assoc
                   AND jobs.id_user = %%s
              GROUP BY login; """ % (self.cluster.name, self.cluster.name)
            datas = (uid,)
            nb_rows = self._cur.execute(req, datas)
            if nb_rows == 1:
                row = self._cur.fetchone()
                user = self.user_from_slurmdbd_row(row)
                logging.info("uid %d found in SlurmDBD with user %s",
                              uid,
                              user )
            elif nb_rows > 1:
                logging.info("uid %d found in too many times in SlurmDBD",
                              uid )
        return user

    def decypher(self, s):
        x = []
        for i in xrange(len(s)):
            j = ord(s[i])
            if j >= 33 and j <= 126:
                x.append(chr(33 + ((j + 14) % 94)))
            else:
                x.append(s[i])
        return ''.join(x)
