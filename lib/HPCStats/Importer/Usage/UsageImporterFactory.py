#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from HPCStats.Importer.Usage.UsageImporterCluster import UsageImporterCluster

class UsageImporterFactory(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        #try:
            config.items(cluster_name + "/usage")
            #logging.info("Usage section exist on config file for cluster %s", cluster_name)
            return UsageImporterCluster(db, config, cluster_name)
        #except:
            logging.error("Error on usage section or options on %s config file", cluster_name)

