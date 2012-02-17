#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.Job import Job
from datetime import datetime
import re

# 02/01/2012 18:56:28;E;5802977.clay1pno;user=martin group=lnhe jobname=2009_juil_dec queue=parall_64 ctime=1328114089 qtime=1328114089 etime=1328114089 start=1328114090 owner=martin@clay1pfr exec_host=cla1a184/7+cla1a184/6+cla1a184/5+cla1a184/4+cla1a184/3+cla1a184/2+cla1a184/1+cla1a184/0+cla1a185/7+cla1a185/6+cla1a185/5+cla1a185/4+cla1a185/3+cla1a185/2+cla1a185/1+cla1a185/0+cla1b003/7+cla1b003/6+cla1b003/5+cla1b003/4+cla1b003/3+cla1b003/2+cla1b003/1+cla1b003/0+cla1b004/7+cla1b004/6+cla1b004/5+cla1b004/4+cla1b004/3+cla1b004/2+cla1b004/1+cla1b004/0 Resource_List.neednodes=4:ppn=8 Resource_List.nodect=4 Resource_List.nodes=4:ppn=8 Resource_List.walltime=06:00:00 session=8351 end=1328118988 Exit_status=0 resources_used.cput=40:56:18 resources_used.mem=1270208kb resources_used.vmem=6968788kb resources_used.walltime=01:21:38

# ('02/01/2012 18:56:28', '5802977', None, 'martin', None, 'lnhe', 'parall_64', '1328114089', '1328114089', '1328114090', 'cla1a184/7+cla1a184/6+cla1a184/5+cla1a184/4+cla1a184/3+cla1a184/2+cla1a184/1+cla1a184/0+cla1a185/7+cla1a185/6+cla1a185/5+cla1a185/4+cla1a185/3+cla1a185/2+cla1a185/1+cla1a185/0+cla1b003/7+cla1b003/6+cla1b003/5+cla1b003/4+cla1b003/3+cla1b003/2+cla1b003/1+cla1b003/0+cla1b004/7+cla1b004/6+cla1b004/5+cla1b004/4+cla1b004/3+cla1b004/2+cla1b004/1+cla1b004/0', '06:00:00')

"""
        job = Job(  id_job = tab[1]
                    sched_id = file:number
                    uid = uid(tab[3])
                    gid = gid(tab[4])
                    submission_datetime = datetime.fromtimestamp(tab[7]),
                    running_datetime = datetime.fromtimestamp(tab[8]),
                    end_datetime = datetime.fromtimestamp(tab[9]),
                    nb_procs = calc()
                    nb_hosts = calc()
                    running_queue = tab[6]
                    nodes = tab[10],
                    state = "Exit
                    clustername = self._cluster_name)
"""

class JobImporterTorque(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        self._logpat = re.compile('(.{19});E;(\d+)(?:-(\d+))?\..*;user=(\S+) (?:account=(\S+))?.*group=(\S+).*queue=(\S+) ctime=\d+ qtime=(\d+) etime=(\d+) start=(\d+) .* exec_host=(\S+) .* Resource_List.walltime=(\d+:\d+:\d+) .*\n')

        db_section = self._cluster_name + "/torque"
        self._logfolder = config.get(db_section,"logdir")

   
    def get_job_information_from_dbid_job_list(self,ids_job):
        # No need to update with Torque
        return []

    def get_job_for_id_above(self, id_job):
        # BETA TEST !!
        filenames = ["/home/sgorget/clamart2/torque/20120215",]
        for filename in filenames:
            accountfile = open(filename,'r')
            for line in accountfile.readlines():
                match = self._logpat.match(line)
                if match:
                    jobinfo = match.groups()
                    print jobinfo[0],jobinfo[3]


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
        return 0
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

