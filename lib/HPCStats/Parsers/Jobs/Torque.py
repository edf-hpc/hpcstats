#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import jobs ##### FIXME
from datetime import datetime

class Torque:
   
    def __init__(self, config):
        """
        example of torque line parsed 
        Parse the line for the end of jobs in accounting files
        ex:
        #    09/13/2010 07:30:18;E;1698368.cla11pno;user=warin group=osiris jobname=Mariva_Scen_2RES_484traj queue=parall_128 ctime=1284355807 qtime=1284355807 etime=1284355807 start=1284355808 owner=warin@cla11pfr exec_host=cla1a090/7+cla1a090/6+cla1a090/5+cla1a090/4+cla1a090/3+cla1a090/2+cla1a090/1+cla1a090/0+cla1a091/7+cla1a091/6+cla1a091/5+cla1a091/4+cla1a091/3+cla1a091/2+cla1a091/1+cla1a091/0 Resource_List.neednodes=2:ppn=8 Resource_List.nodect=2 Resource_List.nodes=2:ppn=8 Resource_List.walltime=60:00:00 session=27046 end=1284355818 Exit_status=139 resources_used.cput=00:00:45 resources_used.mem=438096kb resources_used.vmem=878572kb resources_used.walltime=00:00:10 session_id=27046
        """
        self.config = config
        self.regex_jobrun = re.compile('^\d{2,2}/\d{2,2}/\d{4,4} \d{2,2}:\d{2,2}:\d{2,2};E;(\d+\.\S+);user=(\S+) group=(\S+) .* ctime=(\d+) .* start=(\d+) .* exec_host=(\S+) Resource_List.* end=(\d+) .*$')

    def parse(self):
        # FIXME filename from config
        ofi = open(filename, 'r')
        jobs = []
        print "parsing file ", filename
        while 1:
            line = ofi.readline()
            # if EOF end loop
            if line == '':
                break
            else:
                results = regex_jobrun.search(line)
                if results:
                    # get the variables out of the parsed line
                    number = results.group(1)
                    new_job = Job(number)
                    user = results.group(2)
                    new_job.user = user
                    group = results.group(3)
                    new_job.group = group
                    
                    # creating datetime with parsed timestamps
                    new_job.submission_datetime = datetime.fromtimestamp(int(results.group(4)))
                    new_job.running_datetime = datetime.fromtimestamp(int(results.group(5)))
                    new_job.end_datetime = datetime.fromtimestamp(int(results.group(7)))
                    
                    # creating a list of job's ressources
                    job_exec_hosts = results.group(6).rsplit('+')
                    new_job.nb_procs = len(job_exec_hosts)
                    # build a list with job's hosts
                    hosts = []
                    for host in job_exec_hosts:
                        hostname = host.split('/')[0]
                        if hostname not in hosts:
                            hosts.append(hostname)
                    new_job.hosts = hosts
                    new_job.nb_hosts = len(hosts)

                    # adding the new job in jobs list
                    jobs.append(new_job)
            ofi.close()

        return jobs




    

