#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from HPCStats.Importer.Contexts.BusinessImporter import BusinessImporter
from HPCStats.Importer.Contexts.PareoImporter import PareoImporter
from HPCStats.Importer.Contexts.ContextImporter import ContextImporter

class ContextImporterFactory(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name, "context") == "business":
            business =  BusinessImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "pareo":
            pareo = PareoImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "context":
            context = ContextImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "business+pareo":
            business =  BusinessImporter(db, config, cluster_name)
            pareo = PareoImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "business+context":
            business =  BusinessImporter(db, config, cluster_name)
            context = ContextImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "pareo+context":
            pareo = PareoImporter(db, config, cluster_name)
            context = ContextImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "business+pareo+context":
            business =  BusinessImporter(db, config, cluster_name)
            pareo = PareoImporter(db, config, cluster_name)
            context = ContextImporter(db, config, cluster_name)
        else:
            logging.critical("TO BE CODED")
        return None
