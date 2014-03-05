#!/usr/bin/python
# -*- coding: utf-8 -*-

#from HPCStats.Importer.MountePoint.FilesystemImporter import FilesystemImporter
from HPCStats.Model.Cluster import Cluster
from HPCStats.Model.Filesystem import Filesystem
import os
import logging



class MountPointImporter():

    def __init__(self, db, config, cluster_name):

        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        self._fs_mounted = self._cluster_name + "/mounted"

        self._conf_mount_point = {}
        self._db_mount_point = {}

    def update_mount_point(self):
        cluster = Cluster(self._cluster_name)

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
                    cluster = self._cluster_name, 
                    type = self._conf_mount_point[i])
                filesystem.save(self._db)

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
#                    cluster = self._cluster_name, 
#                    type = self._db_mount_point[i])
#                #filesystem.delete(self._db)

    def get_mount_point_from_config(self):
        fs_config = dict(self._conf.items(self._fs_mounted))
        return fs_config

    def get_mount_point_from_db(self):
        req = """
              SELECT mount_point, type
                FROM filesystem
              WHERE cluster = %s; """
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)
        fs_db = {}
        while (1):
            db_row = cur.fetchone()
            if db_row == None: break
            fs_db[db_row[0]] = db_row[1]
        return fs_db




###### USE MODEL FUNCTION
    def add_mount_point(self, mount_point, type):
        logging.info("ADD JB => %s, type : %s",mount_point, type)
        req = """
           INSERT INTO filesystem (
                  id,
                  mount_point,
                  cluster,
                  type )
           VALUES ( DEFAULT, %s, %s, %s );"""
        datas = (
          mount_point,
          self._cluster_name,
          type )
        self._db.execute(req, datas)



###### USE MODEL FUNCTION
    def delete_mount_point(self, mount_point):
        cur = self._db.get_cur()
        cur.execute("DELETE FROM filesystem WHERE mount_point = %s",(mount_point,))

