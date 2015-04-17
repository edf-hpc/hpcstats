#!/usr/bin/python
# -*- coding: utf-8 -*-

class UsageImporter(object):

    def __init__(self, db, config, cluster_name):

        self._db = db
        self._conf = config
        self._cluster_name = cluster_name
        #self._fs_type = fs_type

    def get_last_home_usage_timestamp(self):
        last_usage_timestamp = 0
        req = """
            SELECT MAX(id_usage) AS last_usage
            FROM filesystem_usage, filesystem
            WHERE filesystem_usage.fs_id=filesystem.id
            AND filesystem.clustername = %s
            AND filesystem.type = %s
              ; """
        datas = (self._cluster_name,
                 self._fs_type,)
        cur = self._db.get_cur()
        cur.execute(req, datas)
        results = cur.fetchall()
        for usage in results:
            if last_home_usage_timestamp < usage[0]:
                last_home_usage_timestamp = usage[0]
        return last_home_usage_timestamp
