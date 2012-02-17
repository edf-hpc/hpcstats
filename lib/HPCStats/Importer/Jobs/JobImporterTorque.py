#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.Job import Job
from datetime import datetime

class JobImporterTorque(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        db_section = self._cluster_name + "/torque"
        self._logfolder = "" #FIXME
        self._dbhost = config.get(db_section,"logdir")

   
    def request_jobs_since_job_id(self, job_id):
        return []

    def request_job_from_dbid(self, job_dbid):
        return []

    def get_job_information_from_dbid_job_list(self,ids_job):
#        jobs = []
#        for id_job in ids_job:
#            result = self.request_job_from_dbid(id_job)
#            jobs.append(self.job_from_information(result[0]))
#        return jobs
        return []

    def get_job_for_id_above(self, id_job):
#        jobs = []
#        results = self.request_jobs_since_job_id(id_job)
#        for result in results:
#            jobs.append(self.job_from_information(result))
#        return jobs
        return []
   
    def job_from_information(self, res):
        return []
        job = Job(  id_job = "id_job",
                    sched_id = "job_db_inx",
                    uid = "id_user",
                    gid = "id_group",
                    submission_datetime = "time_submit",
                    running_datetime = "time_start",
                    end_datetime = "time_end",
                    nb_procs = "cpus_alloc",
                    nb_hosts =  "nodes_alloc",
                    running_queue = "partition",
                    nodes = "nodelist",
                    state = "state",
                    clustername = self._cluster_name)
        return job

# TO BE MOVED IN ABSTRACT FUNCTION
    def get_last_job_id(self):
        return []
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
        return []

