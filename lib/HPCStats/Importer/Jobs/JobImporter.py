#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm

class JobImporter(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name
        if config.get(cluster_name,"jobs") == "slurm":
            print "return JobImporterSlurm"
            self.__class__ = JobImporterSlurm
            #return JobImporterSlurm(db, config, cluster_name)
        #elif ### Torque
        #    return JobImporterTorque(db, config):
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
