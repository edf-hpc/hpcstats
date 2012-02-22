#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.Cluster import Cluster

class ClusterFinder():

    def __init__(self, db):

        self._db = db

    def find(self, name):
        # nothing more to do here
        return Cluster(name)
