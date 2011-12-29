#!/usr/bin/python
# -*- coding: utf-8 -*-

#from HPCStats.Importer.Jobs.JobImporter import JobImporter

#class JobImporterSlurm(JobImporter):
class JobImporterSlurm(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
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
        req = "SELECT id_job, id_user, id_group, time_submit, time_start, time_end, nodes_alloc, cpus_alloc, partition FROM %s_job_table where id_job > %s" % (self._cluster_name, job_id)
        jobs = []
        return jobs

    def request_job(self, job_id):
        req = "SELECT id_job, id_user, id_group, time_submit, time_start, time_end, nodes_alloc, cpus_alloc, partition FROM %s_job_table where id_job = %s" % (self._cluster_name, job_id)
        job = []
        return job

    def get_last_job_id(self):
        last_job_id = 0
        req = "SELECT MAX(id_job) FROM jobs WHERE clustername = '%s'" % (self._cluster_name)
        cur = self._db.get_cur()
        cur.execute(req)
        if cur.fetchone()[0] > last_job_id:
            last_job_id = cur.fetchone()[0]
        return last_job_id

    def get_unfinished_job_id(self):
        unfinished_job_id = 0
        return unfinished_job_id
