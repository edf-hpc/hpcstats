#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2015 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of HPCStats.
#
# HPCStats is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with HPCStats. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

from HPCStats.Importer.Importer import Importer
#from HPCStats.Importer.MountePoint.FilesystemImporter import FilesystemImporter
from HPCStats.Model.Cluster import Cluster
from HPCStats.Model.Filesystem import Filesystem
import os
import logging

class MountPointImporter(Importer):

    def __init__(self, app, db, config, cluster):

        super(MountPointImporter, self).__init__(app, db, config, cluster)

        self._fs_mounted = self.cluster + "/mounted"

        self._conf_mount_point = {}
        self._db_mount_point = {}

    def update_mount_point(self):
        cluster = Cluster(self.cluster)

        self._conf_mount_point = self.get_mount_point_from_config()
        logging.info("fs from conf -> %s", self._conf_mount_point)

        self._db_mount_point = self.get_mount_point_from_db()
        logging.info("fs from db -> %s", self._db_mount_point)


        for i in self._conf_mount_point:
            if i in self._db_mount_point:
                pass
                #logging.info("%s is in db", i)
            else:
                logging.info("Add %s in db", i)
                #self.add_mount_point(i, self._conf_mount_point[i])
                filesystem = Filesystem (
                    mount_point = i, 
                    cluster = self.cluster,
                    type = self._conf_mount_point[i])
                filesystem.save(self.db)

##Useful if you need to delete in casa of mount point does not exist on conf file
##Need delete on cascade : too dangerous
#        for i in self._db_mount_point:
#            if i in self._conf_mount_point:
#                pass
#                #logging.info("%s is conf file", i)
#            else:
#                #logging.info("Delete %s from db", i)
#                self.delete_mount_point(i)
#                filesystem = Filesystem (
#                    mount_point = i, 
#                    cluster = self.cluster,
#                    type = self._db_mount_point[i])
#                #filesystem.delete(self.db)

    def get_mount_point_from_config(self):
        fs_config = dict(self._conf.items(self._fs_mounted))
        return fs_config

    def get_mount_point_from_db(self):
        req = """
              SELECT mount_point, type
                FROM filesystem
              WHERE cluster = %s; """
        datas = (self.cluster,)
        cur = self.db.get_cur()
        cur.execute(req, datas)
        fs_db = {}
        while (1):
            db_row = cur.fetchone()
            if db_row == None: break
            fs_db[db_row[0]] = db_row[1]
        return fs_db




###### USE MODEL FUNCTION
    def add_mount_point(self, mount_point, type):
        logging.info("%s, type : %s",mount_point, type)
        req = """
           INSERT INTO filesystem (
                  id,
                  mount_point,
                  cluster,
                  type )
           VALUES ( DEFAULT, %s, %s, %s );"""
        datas = (
          mount_point,
          self.cluster,
          type )
        self._db.execute(req, datas)



###### USE MODEL FUNCTION
    def delete_mount_point(self, mount_point):
        cur = self.db.get_cur()
        cur.execute("DELETE FROM filesystem WHERE mount_point = %s",(mount_point,))