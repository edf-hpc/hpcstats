#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Users.UserImporter import UserImporter
from HPCStats.Model.User import User
import ldap
from datetime import datetime

class UserImporterLdap(UserImporter):

    def __init__(self, db, config, cluster_name):

        UserImporter.__init__(self)

        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        ldap_section = self._cluster_name + "/ldap"

        self._ldapurl = config.get(ldap_section,"url")
        self._ldapbase = config.get(ldap_section,"basedn")
        self._ldapdn = config.get(ldap_section,"dn")
        self._ldappass = config.get(ldap_section,"password")
        self._ldapconn = ldap.initialize(self._ldapurl)
        self._ldapconn.simple_bind(self._ldapdn, self._ldappass)

        
    def get_all_users(self):
        users = []
        ldap_users = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"(objectClass=posixAccount)",["uid","uidNumber","gidNumber","sn","createTimestamp"])
        for ldap_user in ldap_users:
            lu = ldap_user[1]
            createTimestamp = lu["createTimestamp"][0]
            user = User( name = lu["sn"][0],
                     login = lu["uid"][0],
                     cluster = self._cluster_name,
                     uid = lu["uidNumber"][0],
                     gid = lu["gidNumber"][0],
                     department = lu["gidNumber"][0],
                     creation_date = datetime.strptime(createTimestamp[:14], "%Y%m%d%H%M%S"))
            users.append(user)
        return users

