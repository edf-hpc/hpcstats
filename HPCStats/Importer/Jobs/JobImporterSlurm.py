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
from ClusterShell.NodeSet import NodeSet, NodeSetParseRangeError
import logging
import os
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Importer.Jobs.JobImporter import JobImporter
from HPCStats.Model.Job import Job, get_batchid_oldest_unfinished_job, get_batchid_last_job
from HPCStats.Model.Node import Node
from HPCStats.Model.Run import Run
from HPCStats.Model.User import User
from HPCStats.Model.Account import Account
from HPCStats.Model.Project import Project
from HPCStats.Model.Business import Business

class JobImporterSlurm(JobImporter):

    def __init__(self, app, db, config, cluster):

        super(JobImporterSlurm, self).__init__(app, db, config, cluster)

        section = self.cluster.name + '/slurm'

        self._dbhost = config.get(section, 'host')
        self._dbport = int(config.get(section, 'port'))
        self._dbname = config.get(section, 'name')
        self._dbuser = config.get(section, 'user')
        self._dbpass = config.get(section, 'password')

        self.conn = None
        self.cur = None

    def load(self):
        """Load jobs from Slurm DB."""

        self.jobs = []

        try:
            self.conn = MySQLdb.connect( host=self._dbhost,
                                         user=self._dbuser,
                                         passwd=self._dbpass,
                                         db=self._dbname,
                                         port=self._dbport )
            self.cur = self.conn.cursor()
        except _mysql_exceptions.OperationalError as error:
            raise HPCStatsSourceError( \
                    "connection to Slurm DBD MySQL failed: %s" % (error))


        # Determine the batchid_search
        batchid_oldest_unfinished_job = get_batchid_oldest_unfinished_job(self.db, self.cluster)
        batchid_last_job = get_batchid_last_job(self.db, self.cluster)
        if batchid_oldest_unfinished_job:
            batchid_search = batchid_oldest_unfinished_job
        elif batchid_last_job:
            batchid_search = batchid_last_job
        else:
            batchid_search = -1

        self.get_jobs_after_batchid(batchid_search)

    def get_jobs_after_batchid(self, batchid):
        """Fill the jobs attribute with the list of Jobs found in Slurm DB
           whose id_job is over or equals to the batchid in parameter.
        """

        self.jobs = []
        self.runs = []

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
                       assoc.user,
                       job_name,
                       wckey
                  FROM %s_job_table job,
                       %s_assoc_table assoc,
                       qos_table qos
                 WHERE id_job >= %%s
                   AND assoc.id_assoc = job.id_assoc
                   AND qos.id = job.id_qos
              ORDER BY id_job
              """ % (self.cluster.name, self.cluster.name)
        params = ( batchid, )
        self.cur.execute(req, params)
        while (1):
            row = self.cur.fetchone()
            if row == None: break

            batch_id = row[0]
            sched_id = row[1]

            submission_t = row[4]
            if submission_t == 0:
                submission = None
            else:
                submission = datetime.fromtimestamp(submission_t)

            start_t = row[5]
            if start_t == 0:
                start = None
            else:
                start = datetime.fromtimestamp(start_t)

            end_t = row[6]
            if end_t == 0:
                end = None
            else:
                end = datetime.fromtimestamp(end_t)

            name = row[14]
            nbcpu = row[8]
            state = self.get_job_state_from_slurm_state(row[11])

            nodelist = row[12]
            if nodelist == "(null)" or nodelist == "None assigned" :
                nodelist = None

            partition = self.job_partition(sched_id, row[9], nodelist)
            qos = row[10]
            queue = "%s-%s" % (partition, qos)

            login = row[13]
            searched_user = User(login, None, None, None)
            searched_account = Account(searched_user, self.cluster, None, None, None, None)
            account = self.app.users.find_account(searched_account)
            if account is None:
                raise HPCStatsSourceError( \
                        "account %s not found in loaded accounts" \
                          % (login))

            wckey = row[15]
            wckey_items = wckey.split(':')
            if len(wckey_items) != 2:
                raise HPCStatsSourceError( \
                        "format of wckey %s is not valid" \
                          % (wckey))

            project_code = wckey_items[0]
            searched_project = Project(None, project_code, None)
            project = self.app.projects.find_project(searched_project)
            if project is None:
                raise HPCStatsSourceError( \
                        "project %s not found in loaded projects" \
                          % (project_code))

            business_code = wckey_items[1]
            searched_business = Business(business_code, None)
            business = self.app.business.find(searched_business)
            if business is None:
                raise HPCStatsSourceError( \
                        "business code %s not found in loaded business codes" \
                          % (business_code))

            job = Job(account, project, business, sched_id, batch_id, name,
                      nbcpu, state, queue, submission, start, end)
            self.jobs.append(job)

            if nodelist is not None:
                try:
                    nodeset = NodeSet(nodelist)
                except NodeSetParseRangeError as e:
                    raise HPCStatsSourceError( \
                            "could not parse nodeset %s for job %s" \
                              % (nodelist, batch_id))

                for nodename in nodeset:
                    searched_node = Node(nodename, self.cluster, None, None, None, None)
                    node = self.app.arch.find_node(searched_node)
                    if node is None:
                        raise HPCStatsSourceError(
                                "unable to find node %s for job %s in loaded nodes" \
                                  % (nodename, batch_id))

                    run = Run(self.cluster, node, job)
                    self.runs.append(run)

    def job_partition(self, job_id, partitions_str, nodelist):
        """Return one partition name depending on the partition field and the
           nodelist job record in Slurm DB.

           The partitions_str parameter is the partition field from Slurm DB
           job table. It is a string that represents a comma-separated list of
           partitions. Ex: 'partition1,partition2'

           The nodelist parameter is the nodelist field from Slurm DB job
           table. It a string that represents the nodeset allocated to the job.
           Ex: 'node[001-100]'

           If this partition list has only one element, this element is the
           resulting partition to record in HPCStatsDB. If this list has
           multiple elements, the function looks through the nodelist to find
           the coresponding partition loaded by ArchitectureImporter.

           If the nodelist is not specified, the function arbitrary select the
           first element of the partition list.

           Else, it searches through the job partitions loaded by
           ArchitectureImporter to find the list of job partitions whose
           nodelist totally intersects with job's nodelist. Once found, it
           searches the partition over the list and returns it if found.
        """

        partition = None

        # get partitions list for nodes from ArchitectureImporter
        arch_partitions = self.app.arch.partitions

        # manage case where partitions is a list
        job_partitions = partitions_str.split(',')
        if len(job_partitions) == 1:
            partition = job_partitions[0]
        else:
            # If nodelist is None, arbitrary choose the first partition out of
            # the list
            if nodelist is None:
                partition = job_partitions[0]
            else:
                # look for the actual running partition of the job
                # through self._partitions
                nodeset_job = NodeSet(nodelist)
                logging.debug("trying to find the actual running partition " \
                              "for job %d with list %s and nodes %s (%d)",
                              job_id,
                              job_partitions,
                              nodelist,
                              len(nodeset_job) )

                for nodelist_parts, partitions in arch_partitions.iteritems():
                    nodeset_parts = NodeSet(nodelist_parts)
                    intersect = nodeset_job.intersection(nodeset_parts)
                    if len(intersect) == len(nodeset_job):
                        # iterate over job's partitions list
                        for xpart in job_partitions:
                            if xpart in partitions:
                                 logging.debug("job %d found partition %s " \
                                               "in list %s which intersect " \
                                               "for nodes %s",
                                               job_id,
                                               xpart,
                                               partitions,
                                               nodelist )
                                 # partition found
                                 partition = xpart
                    else:
                        logging.debug("job %d nodes %s do not entirely " \
                                      "intersect with %s (%d != %d)",
                                       job_id,
                                       nodelist,
                                       nodelist_parts,
                                       len(nodeset_job),
                                       len(intersect) )

            if partition is None:
                logging.error("job %d did not found partition in list %s " \
                              "which intersect for nodes %s",
                               job_id,
                               partitions_str,
                               str_nodelist )
                partition = "UNKNOWN"

        return partition

    def get_job_state_from_slurm_state(self, state):
        """Returns the human readable job state textual representation
           corresponding to the numeric state in parameter.

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

    def update(self):
        """Update and save loaded Jobs in HPCStats DB."""

        for job in self.jobs:
            if job.find(self.db):
                job.update(self.db)
            else:
                job.save(self.db)

        for run in self.runs:
            if not run.existing(self.db):
                run.save(self.db)
