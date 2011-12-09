#!/usr/bin/python
# -*- coding: utf-8 -*-

import JobImporter
# ADD MYSQL Connector for Slurm

class JobImporterSlurm(JobImporter):

    def __init__(self, db, conf)
        self._db = db
        self._conf = conf
   
    def list_jobs(self, last_complete_job_id = 0):
        jobs_id = []
        # Find the list of the job that need to be updated or push into supervision
        return jobs_id[]

    def get_jobs(self, jobs_id):
        jobs = []
        for i in jobs():
            j = Job()
            self.retrieve_job_information(i)
            #retrieve all information about i
            #j.populate()
            jobs.append(j)
        return jobs

    def retrieve_job_information(jobid)
            # Using conf
            # Connect to SlurmDBD
            # Extract all info for jobid
            return Job(#All infos)
