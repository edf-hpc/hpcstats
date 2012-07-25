#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Importer.Jobs.JobImporter import JobImporter
from HPCStats.Model.Job import Job
import MySQLdb
from datetime import datetime
from ClusterShell.NodeSet import NodeSet

class JobImporterSlurm(JobImporter):

    def __init__(self, db, config, cluster_name):

        JobImporter.__init__(self, db, config, cluster_name)

        slurm_section = self._cluster_name + "/slurm"

        self._dbhost = config.get(slurm_section,"host")
        self._dbport = int(config.get(slurm_section,"port"))
        self._dbname = config.get(slurm_section,"name")
        self._dbuser = config.get(slurm_section,"user")
        self._dbpass = config.get(slurm_section,"password")
        self._conn = MySQLdb.connect( host = self._dbhost,
                                      user = self._dbuser,
                                      passwd = self._dbpass,
                                      db = self._dbname,
                                      port = self._dbport )
        self._cur = self._conn.cursor(MySQLdb.cursors.DictCursor)

        str_conf_partitions = config.get(slurm_section,"partitions")
        # example of value:
        # partitions=cn[0001-1382]:small,para,compute;bm|01-29]:bigmem;cg[01-34]:visu
        lst_nodes_parts = str_conf_partitions.split(";")
        self._partitions = {}
        for str_nodes_parts in lst_nodes_parts:
            str_nodeset, str_partitions_lst = str_nodes_parts.split(":")
            lst_partitions = str_partitions_lst.split(",")
            self._partitions[str_nodeset] = lst_partitions
        # As a result, we have here:
        # { "cn[0001-1382]" => ["small","para","compute"],
        #   "bm[01-29]"     => ["bigmem"],
        #   "cg[01-24]"     => ["visu"]                    }
   
    def request_jobs_since_job_id(self, job_id, offset, max_jobs):
        req = """
            SELECT id_job,
                   job_db_inx,
                   id_user,
                   id_group,
                   time_submit,
                   time_start,
                   time_end,
                   nodes_alloc,
                   cpus_alloc,
                   partition,
                   qos.name AS qos,
                   state,
                   nodelist
             FROM %s_job_table job,
                  qos_table qos
             WHERE id_job > %%s
               AND qos.id = job.id_qos
             ORDER BY job_db_inx
             LIMIT %%s, %%s; """ % (self._cluster_name)
        datas = (job_id, offset, max_jobs)
        self._cur.execute(req, datas)
        results = self._cur.fetchall()
        return results

    def request_job_from_dbid(self, job_dbid):
        req = """
            SELECT id_job,
                   job_db_inx,
                   id_user,
                   id_group,
                   time_submit,
                   time_start,
                   time_end,
                   nodes_alloc,
                   cpus_alloc,
                   partition,
                   qos.name AS qos,
                   state,
                   nodelist
            FROM %s_job_table,
                  qos_table qos
            WHERE job_db_inx = %%s
              AND qos.id = job.id_qos
            ORDER BY job_db_inx; """ % (self._cluster_name)
        datas = (job_dbid)
        self._cur.execute(req, datas)
        results = self._cur.fetchall()
        return results

    def get_job_information_from_dbid_job_list(self, ids_job):
        jobs = []
        for id_job in ids_job:
            result = self.request_job_from_dbid(id_job)
            jobs.append(self.job_from_information(result[0]))
        #self._filter(jobs)
        return jobs

    def get_job_for_id_above(self, id_job, offset, max_jobs):
        jobs = []
        results = self.request_jobs_since_job_id(id_job, offset, max_jobs)
        for result in results:
            jobs.append(self.job_from_information(result))
        #self._filter(jobs)
        return jobs
   
    def job_from_information(self, res):
        # manage a case where slurmdbd puts a weird value '(null)' in nodelist
        str_nodelist = res["nodelist"]
        if str_nodelist == "(null)" or str_nodelist == "None assigned" :
            str_nodelist = None

        # manage case where 
        str_partition = None
        str_partitions_lst = res["partition"]
        lst_partitions = str_partitions_lst.split(",")
        if len(lst_partitions) == 1:
            str_partition = lst_partitions[0]
        else:
            # if nodelist is None, arbitrary choose the first partition out of the list
            if not str_nodelist:
                str_partition = lst_partitions[0]
            else:
                # look for the actual running partition of the job
                # through self._partitions
                ns_job = NodeSet(str_nodelist)
                print "Info %s: trying to find the actual running partition for job %d with list %s and nodes %s (%d)" % \
                          ( self.__class__.__name__,
                            res["id_job"],
                            str_partitions_lst,
                            str_nodelist,
                            len(ns_job) )
                for str_part_nodeset in self._partitions.keys():
                    ns_part = NodeSet(str_part_nodeset)
                    if len(ns_job.intersection(ns_part)) == len(ns_job):
                        # iterate over job's partitions list
                        for str_tmp_partition in lst_partitions:
                            if str_tmp_partition in self._partitions[str_part_nodeset]:
                                 print "Info %s: job %d found partition %s in list %s which intersect for nodes %s" % \
                                         ( self.__class__.__name__,
                                           res["id_job"],
                                           str_tmp_partition,
                                           str_partitions_lst,
                                           str_nodelist )
                                 # partition found
                                 str_partition = str_tmp_partition
                    else:
                        print "Debug %s: job %d nodes %s do not entirely intersect with %s (%d != %d)" % \
                                  ( self.__class__.__name__,
                                    res["id_job"],
                                    str_nodelist,
                                    str_part_nodeset,
                                    len(ns_job),
                                    len(ns_job.intersection(ns_part)) )
                
            if str_partition == None:
                print "Error %s: job %d did not found partition in list %s which intersect for nodes %s" % \
                          ( self.__class__.__name__,
                            res["id_job"],
                            str_partitions_lst,
                            str_nodelist )
                str_partition = "UNKNOWN"


        job = Job(  id_job = res["id_job"],
                    sched_id = str(res["job_db_inx"]),
                    uid = int(res["id_user"]),
                    gid = int(res["id_group"]),
                    submission_datetime = datetime.fromtimestamp(res["time_submit"]),
                    running_datetime = datetime.fromtimestamp(res["time_start"]),
                    end_datetime = datetime.fromtimestamp(res["time_end"]),
                    nb_procs = res["cpus_alloc"],
                    nb_hosts =  res["nodes_alloc"],
                    running_queue = str_partition+"-"+res["qos"],
                    nodes = str_nodelist,
                    state = self.get_job_state_from_slurm_state(res["state"]),
                    cluster_name = self._cluster_name)
        return job

    """
        From slurm.h.inc
            enum job_states {
            JOB_PENDING, /* queued waiting for initiation */
            JOB_RUNNING, /* allocated resources and executing */
            JOB_SUSPENDED, /* allocated resources, execution suspended */
            JOB_COMPLETE, /* completed execution successfully */
            JOB_CANCELLED, /* cancelled by user */
            JOB_FAILED, /* completed execution unsuccessfully */
            JOB_TIMEOUT, /* terminated on reaching time limit */
            JOB_NODE_FAIL, /* terminated on node failure */
            JOB_PREEMPTED, /* terminated due to preemption */
            JOB_END /* not a real state, last entry in table */
            };
            #define JOB_RESIZING    0x2000  /* Size of job about to change, flag set
                                             * before calling accounting functions
                                             * immediately before job changes size */

    """
    def get_job_state_from_slurm_state(self, state):
        slurm_state = {
            0:"PENDING", # queued waiting for initiation 
            1:"RUNNING", # allocated resources and executing 
            2:"SUSPENDED", # allocated resources, execution suspended 
            3:"COMPLETE", # completed execution successfully 
            4:"CANCELLED", # cancelled by user 
            5:"FAILED", # completed execution unsuccessfully 
            6:"TIMEOUT", # terminated on reaching time limit 
            7:"NODE_FAIL", # terminated on node failure 
            8:"PREEMPTED", # terminated due to preemption 
            9:"END", # not a real state, last entry in table 
            8192:"RESIZING" # Size of job about to change, flag set
                            # before calling accounting functions
                            # immediately before job changes size
        }
        return slurm_state[state]            

    def _filter(self, jobs):
        job_filter = JobFilterSlurmNoStartTime(self, jobs)
        job_filter.run()

class JobFilterSlurmNoStartTime:

    def __init__(self, job_importer, jobs):

        self._name = "SlurmNoStartTime"
        self._description = "Filter job imported from SlurmDBD with no time_start"   
        self._slurmdbd_cur = job_importer._cur
        self._jobs = jobs
        
    def __str__(self):
        return "JobFilter %s (%d jobs)" % (self._name, len(self._jobs))

    def run(self):
        for job in self._jobs:
            if not self._filter_job(job):
                self._jobs.remove(job)
                print "Info %s: job %s removed from import" % \
                         ( self,
                           job )

    def _filter_job(self, job):

        if job.get_state() != 'PENDING' and \
           job.get_running_datetime() == datetime(1970,1,1,1,0,0):

            sql = """
                SELECT id_step,
                       time_start
                FROM %s_step_table
                WHERE job_db_inx = %%s
                ORDER BY id_step; """ % (job.get_cluster_name())
    
            data = (job.get_db_id(),)
            self._slurmdbd_cur.execute(sql, data)
            row = self._slurmdbd_cur.fetchone()
            if row == None:
                print "Info %s: job %s has no first step." % \
                         ( self,
                           job )
                return None
            else:
                step_id = row[0]
                step_start = datetime.fromtimestamp(row[1])
                print "Info %s: job %s has first step started at %s" % \
                         ( self,
                           job,
                           step_start )
                job.set_running_datetime(step_start)
                return job
        else:
            return job
