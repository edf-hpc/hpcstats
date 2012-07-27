#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Events.EventImporterSlurm import EventImporterSlurm

class EventImporterFactory(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name, "events") == "slurm": ## Slurm
            return EventImporterSlurm(db, config, cluster_name)
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
        return None
