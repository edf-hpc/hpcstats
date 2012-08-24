#!/usr/bin/python
# -*- coding: utf-8 -*-

class UserImporter(object):

    def __init__(self, db, cluster_name):

        self._db = db
        self._cluster_name = cluster_name

    def _get_unknown_users(self, db):
        req = """
            SELECT distinct(uid)
              FROM jobs
             WHERE clustername = %s
               AND uid NOT IN (SELECT uid FROM users WHERE users.cluster = %s); """
        datas = (self._cluster_name, self._cluster_name)

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)

        unknown_users = []

        while (1):

            row = cur.fetchone()
            if row == None: break
            uid = int(row[0])
            unknown_users.append(uid)

        return unknown_users;
