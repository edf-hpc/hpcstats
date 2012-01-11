#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Architectures.ArchitectureImporterArchfile import ArchitectureImporterArchfile

class ArchitectureImporter(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name,"architecture") == "archfile":
            return ArchitectureImporterArchfile(db, config, cluster_name)
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
        return None
