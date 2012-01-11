#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Users.UserImporterXLSLdap import UserImporterXLSLdap

class UserImporter(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name,"users") == "xls+ldap":
            print "return UserImporterXLSLdap"
            return UserImporterXLSLdap(db, config, cluster_name)
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
