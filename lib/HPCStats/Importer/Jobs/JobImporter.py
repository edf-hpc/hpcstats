#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm

class JobImporter(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name,"jobs") == "slurm": ## Slurm
            return JobImporterSlurm(db, config, cluster_name)
        elif config.get(cluster_name, "jobs") == "torque": ## Torque
            print "FATAL : TO BE CODED"
#            return JobImporterTorque(db, config, cluster_name):
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
        return None
