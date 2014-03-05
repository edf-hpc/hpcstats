#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from HPCStats.Importer.MountPoint.MountPointImporter import MountPointImporter

class MountPointImporterFactory(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
#        try:
            config.items(cluster_name + "/mounted")
            logging.debug("Mounted section exist on config file for cluster %s", cluster_name)
            return MountPointImporter(db, config, cluster_name)
#        except:
            logging.error("No mounted section exist on config file for cluster %s", cluster_name)

