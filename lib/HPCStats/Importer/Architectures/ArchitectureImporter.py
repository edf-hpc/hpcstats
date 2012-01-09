#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Architectures.ArchitectureImporterArchfile import ArchitectureImporterArchfile

class ArchitectureImporter(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name
        if config.get(cluster_name,"architecture") == "archfile":
            print "return ArchitectureImporterArchfile"
            self.__class__ = ArchitectureImporterArchfile
        else:
            print "FATAL : TO BE CODED"
            # Throw Exception
