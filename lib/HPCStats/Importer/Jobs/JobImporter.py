#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm

class JobImporter:

    def __init__(self, db, config, cluster_name):
        if config.get(cluster_name,"jobs") == "slurm":
            JobImporterSlurm(db, config, cluster_name)
        #elif ### Torque
        #    return JobImporterTorque(db, config):
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
