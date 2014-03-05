#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

class Filesystem:
    def __init__(self, mount_point = "", cluster = "", type = ""):

        self._mount_point = mount_point
        self._cluster = cluster
        self._type = type

    def __str__(self):
        return "mount point : %s ,on cluster : %s, type : %s" % \
                   ( self._mount_point,
                     self._cluster,
                     self._type)

    def save(self, db):
        req = """
            INSERT INTO filesystem (
                            mount_point,
                            cluster,
                            type )
            VALUES ( %s, %s, %s); """
        datas = (
            self._mount_point,
            self._cluster,
            self._type )

        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)


    def delete(self, db):
        cur = db.get_cur()
        cur.execute("DELETE FROM filesystem WHERE mount_point = %s",(self._mount_point,))

    def get_fs_for_cluster(self, db, cluster):
        req = """
            SELECT mount_point
            FROM filesystem
            WHERE cluster = %s
              ;"""
        datas = (cluster,)
        cur = db.get_cur()
        cur.execute(req, datas)
        results = []
        while (1):
            db_row = cur.fetchone()
            if db_row == None: break
            results.append(db_row[0])
        return results

