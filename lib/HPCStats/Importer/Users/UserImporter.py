#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Users.UserImporterXLSLdap import UserImporterXLSLdap

class UserImporter(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name
        if config.get(cluster_name,"users") == "xls+ldap":
            print "return UserImporterXLSLdap"
            self.__class__ = UserImporterXLSLdap
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
