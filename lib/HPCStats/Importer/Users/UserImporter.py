#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Users.UserImporterXLSLdapSlurm import UserImporterXLSLdapSlurm

class UserImporter(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name,"users") == "xls+ldap+slurm":
            return UserImporterXLSLdapSlurm(db, config, cluster_name)
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
        return None
