#!/usr/bin/python
# -*- coding: utf-8 -*-

class JobImporterSlurm(object):

    def __init__(self, db, conf, cluster_name):
        self._db = db
        self._conf = conf
        self._cluster_name = cluster_name
   
    def list_jobs(self, last_complete_job_id = 0):
        jobs_id = []
        # Find the list of the job that need to be updated or push into supervision
        return jobs_id

    def get_jobs(self, jobs_id):
        jobs = []
        for i in jobs():
            j = Job()
            self.retrieve_job_information(i)
            #retrieve all information about i
            #j.populate()
            jobs.append(j)
        return jobs

    def retrieve_job_information(self, jobid):
            # Using conf
            # Connect to SlurmDBD
            # Extract all info for jobid
            return 1

    def request_since_job(self, job_id):
        return "SELECT id_job, id_user, id_group, time_submit, time_start, time_end, nodes_alloc, cpus_alloc, partition from  ivanoe_job_table where id_job > %s" % (job_id)

    def request_job(self, job_id):
        return "SELECT id_job, id_user, id_group, time_submit, time_start, time_end, nodes_alloc, cpus_alloc, partition from  ivanoe_job_table where id_job = %s" % (job_id)
