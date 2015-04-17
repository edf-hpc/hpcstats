#!/usr/bin/python
# -*- coding: utf-8 -*-

class JobImporter(object):

    def __init__(self, db, config, cluster_name):

        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

    def get_last_job_id(self):
        last_job_id = 0
        req = """
            SELECT MAX(id_job) AS last_id
            FROM jobs
            WHERE clustername = %s; """
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)
        results = cur.fetchall()
        for job in results:
            if last_job_id < job[0]:
                last_job_id = job[0]
        return last_job_id

    def get_unfinished_job_id(self):
        unfinished_job_dbid = []
        req = """
            SELECT sched_id
            FROM jobs
            WHERE clustername = %s
              AND (   state = 'PENDING'
                   OR state = 'RUNNING' ); """
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)
        results = cur.fetchall()
        for job in results:
            unfinished_job_dbid.append(job[0])
        return unfinished_job_dbid
