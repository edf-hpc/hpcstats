#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.Cluster import Cluster
from HPCStats.Model.User import User
from HPCStats.Importer.Users.UserImporterXLSLdapSlurm import UserImporterXLSLdapSlurm
from HPCStats.Importer.Users.UserImporterLdap import UserImporterLdap

class UserImporter(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name,"users") == "xls+ldap+slurm":
            return UserImporterXLSLdapSlurm(db, config, cluster_name)
        elif config.get(cluster_name,"users") == "ldap":
            return UserImporterLdap(db, config, cluster_name)
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
        return None
