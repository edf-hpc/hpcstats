#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2015 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of HPCStats.
#
# HPCStats is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with HPCStats. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

import MySQLdb
import _mysql_exceptions
from datetime import datetime
from ClusterShell.NodeSet import NodeSet
import logging
import os
import ConfigParser
from HPCStats.Importer.Jobs.JobImporter import JobImporter
from HPCStats.Model.Job import Job

class JobImporterSlurm(JobImporter):

    def __init__(self, app, db, config, cluster_name):

        JobImporter.__init__(self, app, db, config, cluster_name)

        slurm_section = self._cluster_name + "/slurm"

        self._dbhost = config.get(slurm_section,"host")
        self._dbport = int(config.get(slurm_section,"port"))
        self._dbname = config.get(slurm_section,"name")
        self._dbuser = config.get(slurm_section,"user")
        self._dbpass = config.get(slurm_section,"password")
        try:
            self._conn = MySQLdb.connect( host = self._dbhost,
                                          user = self._dbuser,
                                          passwd = self._dbpass,
                                          db = self._dbname,
                                          port = self._dbport )
        except _mysql_exceptions.OperationalError as e:
            logging.error("connection to Slurm DBD MySQL failed: %s", e)
            raise RuntimeError
        self._cur = self._conn.cursor(MySQLdb.cursors.DictCursor)

        # get it from archfile
        self._partitions = {}
        archfile_section = self._cluster_name + "/archfile"
        archfile_name = config.get(archfile_section, "file")
        archfile = ConfigParser.ConfigParser()
        archfile.read(archfile_name)
        partitions_list = archfile.get(self._cluster_name,"partitions").split(',')
        for partition_name in partitions_list:
            partition_section_name = self._cluster_name + "/" + partition_name
            nodesets_list = archfile.get(partition_section_name, "nodesets").split(',')
            slurm_partitions_list = archfile.get(partition_section_name, "slurm_partitions").split(',')
            ns_nodeset = NodeSet()
            for nodeset_name in nodesets_list:
                nodeset_section_name = self._cluster_name + "/" + partition_name + "/" + nodeset_name
                str_nodenames = archfile.get(nodeset_section_name, "names")
                ns_nodeset.add(str_nodenames)
            self._partitions[str(ns_nodeset)] = slurm_partitions_list 
        # As a result, we have here:
        # { "cn[0001-1382]": ["small","para","compute"],
        #   "bm[01-29]"    : ["bigmem"],
        #   "cg[01-24]"    : ["visu"]                    }
        self._id_assoc = self.get_id_assoc()

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
                   nodelist,
                   id_assoc,
                   job_name
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
                   nodelist,
                   id_assoc,
                   job_name
            FROM %s_job_table job,
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

        # manage case where partitions is a list
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
                logging.info("trying to find the actual running partition for job %d with list %s and nodes %s (%d)",
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
                                 logging.info("job %d found partition %s in list %s which intersect for nodes %s",
                                               res["id_job"],
                                               str_tmp_partition,
                                               str_partitions_lst,
                                               str_nodelist )
                                 # partition found
                                 str_partition = str_tmp_partition
                    else:
                        logging.debug("job %d nodes %s do not entirely intersect with %s (%d != %d)",
                                       res["id_job"],
                                       str_nodelist,
                                       str_part_nodeset,
                                       len(ns_job),
                                       len(ns_job.intersection(ns_part)) )

            if str_partition == None:
                logging.error("job %d did not found partition in list %s which intersect for nodes %s",
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
                    cluster_name = self._cluster_name,
                    login = self._id_assoc[res["id_assoc"]],
                    name = res["job_name"])
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

    def get_wckey_from_job(self, id_job):
        req = """
            SELECT wckey
            FROM %s_job_table
            WHERE id_job = %%s
            """ % (self._cluster_name)
        data = (id_job)
        cur = self._conn.cursor()
        cur.execute(req, data)
        result = cur.fetchone()
        return result[0]

    def get_id_assoc(self):
        id_assoc = {}
        req = """
             SELECT id_assoc, user
             FROM %s_assoc_table
             WHERE user != '';
        """ % (self._cluster_name)
        self._cur.execute(req)
        results = self._cur.fetchall()
        for ii in results:
            id_assoc[ii['id_assoc']] = ii['user']
        return id_assoc

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
                logging.info("job %s removed from import", job)

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
                logging.info("job %s has no first step.", job)
                return None
            else:
                step_id = row[0]
                step_start = datetime.fromtimestamp(row[1])
                logging.info("job %s has first step started at %s",
                              job,
                              step_start )
                job.set_running_datetime(step_start)
                return job
        else:
            return job
