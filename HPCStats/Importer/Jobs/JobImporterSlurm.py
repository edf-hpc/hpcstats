#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2018 EDF SA
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

"""This module contains the JobImporterSlurm class."""

import MySQLdb
import _mysql_exceptions
from datetime import datetime
from ClusterShell.NodeSet import NodeSet, NodeSetParseRangeError
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors
from HPCStats.Importer.Jobs.JobImporter import JobImporter
from HPCStats.Utils import is_bg_nodelist, compute_bg_nodelist, extract_tres_cpu
from HPCStats.Model.Job import Job, get_batchid_oldest_unfinished_job, get_batchid_last_job
from HPCStats.Model.Node import Node
from HPCStats.Model.Run import Run
from HPCStats.Model.User import User
from HPCStats.Model.Account import Account
from HPCStats.Model.Project import Project
from HPCStats.Model.Business import Business

class JobImporterSlurm(JobImporter):

    """This JobImporter imports jobs related data from Slurm accounting
       database.
    """

    def __init__(self, app, db, config, cluster):

        super(JobImporterSlurm, self).__init__(app, db, config, cluster)

        section = self.cluster.name + '/slurm'

        self._dbhost = config.get(section, 'host')
        self._dbport = int(config.get(section, 'port'))
        self._dbname = config.get(section, 'name')
        self._dbuser = config.get(section, 'user')
        self._dbpass = config.get_default(section, 'password', None)

        self.window_size = \
          config.get_default(section,
                             'window_size',
                             0, int)

        self.prefix = config.get_default(section, 'prefix', self.cluster.name)

        self.partitions = config.get_list(section, 'partitions')

        self.strict_job_account_binding = \
          config.get_default('constraints',
                             'strict_job_account_binding',
                             True, bool)
        self.strict_job_project_binding = \
          config.get_default('constraints',
                             'strict_job_project_binding',
                             True, bool)
        self.strict_job_businesscode_binding = \
          config.get_default('constraints',
                             'strict_job_businesscode_binding',
                             True, bool)
        self.strict_job_wckey_format = \
          config.get_default('constraints',
                             'strict_job_wckey_format',
                             True, bool)

        self.conn = None
        self.cur = None

        self.unknown_accounts = []
        self.invalid_wckeys = []
        self.unknown_projects = []
        self.unknown_businesses = []

        self.nb_loaded_jobs = -1
        self.nb_excluded_jobs = -1

    def connect_db(self):
        """Connect to cluster Slurm database and set conn/cur attribute
           accordingly. Raises HPCStatsSourceError in case of problem.
        """

        try:
            conn_params = {
               'host': self._dbhost,
               'user': self._dbuser,
               'db': self._dbname,
               'port': self._dbport,
            }
            if self._dbpass is not None:
                conn_params['passwd'] = self._dbpass

            self.conn = MySQLdb.connect(**conn_params)
            self.cur = self.conn.cursor()
        except _mysql_exceptions.OperationalError as error:
            raise HPCStatsSourceError( \
                    "connection to Slurm DBD MySQL failed: %s" % (error))

    def disconnect_db(self):
        """Disconnect from cluster Slurm database."""

        self.cur.close()
        self.conn.close()

    def check(self):
        """Check if cluster Slurm database is available for connection."""

        self.connect_db()
        self.disconnect_db()

    def get_search_batch_id(self):
        """Determine and return the oldest batch_id to search for update in
           Slurm database.
        """

        batchid_oldest_unfinished_job = \
          get_batchid_oldest_unfinished_job(self.db, self.cluster)
        batchid_last_job = get_batchid_last_job(self.db, self.cluster)
        if batchid_oldest_unfinished_job:
            self.log.debug("oldest unfinished job found %d",
                           batchid_oldest_unfinished_job)
            batchid_search = batchid_oldest_unfinished_job
        elif batchid_last_job:
            self.log.debug("last job found %d", batchid_last_job)
            batchid_search = batchid_last_job
        else:
            batchid_search = self.app.params['since_jobid']

        return batchid_search

    def load_update_window(self):
        """Load and update job in windowed mode until there is more job to load
           in Slurm database.
        """
        nb_loaded = -1
        self.nb_loaded_jobs = 0
        self.nb_excluded_jobs = 0

        self.connect_db()
        batch_id = self.get_search_batch_id()
        self.log.info("loading jobs starting from batch id %d", batch_id)

        while nb_loaded != 0:
            # load jobs and jump to next batch_id for next iteration
            batch_id = self.load_window(batch_id) + 1
            nb_loaded = len(self.jobs)
            self.log.info("%d loaded jobs (%d this iteration), %d excluded",
                          self.nb_loaded_jobs,
                          nb_loaded,
                          self.nb_excluded_jobs)
            self.update()

    def load_window(self, batch_id):
        """Load a limited amount of jobs (limite to the window size) starting
           from the batch_id in parameter and fill jobs list attribute
           accordingly.
        """

        self.jobs = []
        return self.get_jobs_after_batchid(batch_id, self.window_size)

    def load(self):
        """Load jobs from Slurm DB."""

        self.jobs = []
        self.connect_db()
        batch_id = self.get_search_batch_id()
        self.get_jobs_after_batchid(batch_id)

    def _is_old_schema(self):
        """Returns True if it detects the old-schema (<15.08) in the SlurmDBD
           database, False otherwise.
        """

        req = "SHOW COLUMNS FROM %s_job_table LIKE 'cpus_alloc'" \
              % (self.prefix)
        self.cur.execute(req)
        row = self.cur.fetchone()
        if row is not None:
            self.log.debug("detected old-schema <15.08 in job table")
            return True
        self.log.debug("detected new-schema >=15.08 in job table")
        return False

    def get_jobs_after_batchid(self, batchid, window_size=0):
        """Fill the jobs attribute with the list of Jobs found in Slurm DB
           whose id_job is over or equals to the batchid in parameter.
           Returns the last found batch_id.
        """

        self.jobs = []

        if window_size:
            limit = "LIMIT %d" % (window_size)
        else:
            limit = ''

        last_batch_id = -1

        old_schema = self._is_old_schema()
        if old_schema is True:
            cpu_field = 'cpus_alloc'
        else:
            cpu_field = 'tres_alloc'

        if not len(self.partitions):
            partitions_clause = ''
        else:
            partitions_clause = "AND job.partition IN (%s)" % \
                                ','.join(['%s'] * len(self.partitions))

        req = """
                SELECT job_db_inx,
                       id_job,
                       id_user,
                       id_group,
                       time_submit,
                       time_start,
                       time_end,
                       nodes_alloc,
                       %s,
                       job.partition,
                       qos.name AS qos,
                       job.account,
                       state,
                       nodelist,
                       assoc.user,
                       job_name,
                       wckey
                  FROM %s_job_table job,
                       %s_assoc_table assoc,
                       qos_table qos
                 WHERE job_db_inx >= %%s
                   %s
                   AND assoc.id_assoc = job.id_assoc
                   AND qos.id = job.id_qos
              ORDER BY job_db_inx %s
              """ % (cpu_field,
                     self.prefix,
                     self.prefix,
                     partitions_clause,
                     limit)
        params = ( batchid, ) + tuple(self.partitions)
        self.cur.execute(req, params)
        while (1):
            row = self.cur.fetchone()
            if row == None:
                break

            self.nb_loaded_jobs += 1

            batch_id = last_batch_id = row[0]
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

            # Some jobs in Slurm DBD have an end but no start. Typically, this
            # concernes the jobs that have been cancelled before starting. For
            # these jobs, we set the start equal to the end.
            if start is None and end is not None:
                start = end

            name = row[15]
            if old_schema is True:
                nbcpu = row[8]
            else:
                nbcpu = extract_tres_cpu(row[8])
                if nbcpu == -1:
                    raise HPCStatsSourceError( \
                            "unable to extract cpus_alloc from job tres")

            state = JobImporterSlurm.get_job_state_from_slurm_state(row[12])

            nodelist = row[13]
            if nodelist == "(null)" or nodelist == "None assigned" :
                nodelist = None

            partition = self.job_partition(sched_id, row[9], nodelist)
            qos = row[10]
            queue = "%s-%s" % (partition, qos)
            job_acct = row[11]

            login = row[14]

            searched_user = User(login, None, None, None)
            searched_account = Account(searched_user, self.cluster,
                                       None, None, None, None)
            account = self.app.users.find_account(searched_account)
            if account is None:
                msg = "account %s not found in loaded accounts" \
                        % (login)
                if self.strict_job_account_binding == True:
                    raise HPCStatsSourceError(msg)
                elif login not in self.unknown_accounts:
                    self.unknown_accounts.append(login)
                    self.log.warn(Errors.E_J0001, msg)
                self.nb_excluded_jobs += 1
                continue
            user = self.app.users.find_user(searched_user)
            if user is None:
                msg = "user %s not found in loaded users" % (login)
                raise HPCStatsSourceError(msg)
            job_department = user.department

            wckey = row[16]

            # empty wckey must be considered as None
            if wckey == '':
                wckey = None

            if wckey is None:
                project = None
                business = None
            else:
                wckey_items = wckey.split(':')
                if len(wckey_items) != 2:
                    msg = "format of wckey %s is not valid" % (wckey)
                    if self.strict_job_wckey_format == True:
                        raise HPCStatsSourceError(msg)
                    elif wckey not in self.invalid_wckeys:
                        self.invalid_wckeys.append(wckey)
                        self.log.warn(Errors.E_J0002, msg)
                    project = None
                    business = None
                else:
                    project_code = wckey_items[0]
                    searched_project = Project(None, project_code, None)
                    project = self.app.projects.find_project(searched_project)
                    if project is None:
                        msg = "project %s not found in loaded projects" \
                                % (project_code)
                        if self.strict_job_project_binding == True:
                            raise HPCStatsSourceError(msg)
                        elif project_code not in self.unknown_projects:
                            self.unknown_projects.append(project_code)
                            self.log.warn(Errors.E_J0003, msg)

                    business_code = wckey_items[1]
                    searched_business = Business(business_code, None)
                    business = self.app.business.find(searched_business)

                    if business is None:
                        msg = "business code %s not found in loaded " \
                              "business codes" % (business_code)
                        if self.strict_job_businesscode_binding == True:
                            raise HPCStatsSourceError(msg)
                        elif business_code not in self.unknown_businesses:
                            self.unknown_businesses.append(business_code)
                            self.log.warn(Errors.E_J0004, msg)

            job = Job(account, project, business, sched_id, str(batch_id),
                      name, nbcpu, state, queue, job_acct, job_department,
                      submission, start, end)
            self.jobs.append(job)

            if nodelist is not None:
                self.create_runs(nodelist, job)

        return last_batch_id

    def create_runs(self, nodelist, job):
        """Create all Runs objects for the job in parameter and all the nodes
           in nodelist.
        """

        if is_bg_nodelist(nodelist):
            nodeset = compute_bg_nodelist(nodelist)
        else:
            try:
                nodeset = NodeSet(nodelist)
            except NodeSetParseRangeError:
                raise HPCStatsSourceError( \
                        "could not parse nodeset %s for job %s" \
                          % (nodelist, job.batch_id))

        for nodename in nodeset:
            searched_node = Node(nodename, self.cluster,
                                 None, None, None, None, None)
            node = self.app.arch.find_node(searched_node)
            if node is None:
                self.log.warn(Errors.E_J0006,
                              "unable to find node %s for job %s in loaded " \
                              "nodes", nodename, job.batch_id)
            else:
                run = Run(self.cluster, node, job)
                job.runs.append(run)

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
                self.log.debug("trying to find the actual running partition " \
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
                                self.log.debug("job %d found partition %s " \
                                               "in list %s which intersect " \
                                               "for nodes %s",
                                               job_id,
                                               xpart,
                                               partitions,
                                               nodelist )
                                # partition found
                                partition = xpart
                    else:
                        self.log.debug("job %d nodes %s do not entirely " \
                                       "intersect with %s (%d != %d)",
                                       job_id,
                                       nodelist,
                                       nodelist_parts,
                                       len(nodeset_job),
                                       len(intersect) )

            if partition is None:
                self.log.warn(Errors.E_J0005,
                              "job %d did not found partition in list %s " \
                              "which intersect for nodes %s",
                              job_id,
                              partitions_str,
                              nodelist )
                partition = "UNKNOWN"

        return partition

    @staticmethod
    def get_job_state_from_slurm_state(state):
        """Returns the human readable job state textual representation
           corresponding to the numeric state in parameter.

           From ``slurm.h.inc``:

           .. code-block:: c

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
                   JOB_BOOT_FAIL, /* terminated due to preemption */
                   JOB_END /* not a real state, last entry in table */
               };
               #define JOB_STATE_BASE  0x00ff  /* Used for job_states above */
               #define JOB_STATE_FLAGS 0xff00  /* Used for state flags below */
               #define JOB_COMPLETING  0x8000  /* Waiting for epilog completion */
               #define JOB_CONFIGURING 0x4000  /* Allocated nodes booting */
               #define JOB_RESIZING    0x2000  /* Size of job about to change, flag set
                                                * before calling accounting functions
                                                * immediately before job changes size */
               #define JOB_SPECIAL_EXIT 0x1000 /* Requeue an exit job in hold */
               #define JOB_REQUEUE_HOLD 0x0800 /* Requeue any job in hold */
               #define JOB_REQUEUE      0x0400 /* Requeue job in completing state */
               #define JOB_STOPPED      0x0200 /* Job is stopped state (holding resources,
                                                * but sent SIGSTOP */
               #define JOB_LAUNCH_FAILED 0x0100
        """

        states = []

        slurm_base_states = [
            ( 0x0000, 'PENDING'   ),
            ( 0x0001, 'RUNNING'   ),
            ( 0x0002, 'SUSPENDED' ),
            ( 0x0003, 'COMPLETE'  ),
            ( 0x0004, 'CANCELLED' ),
            ( 0x0005, 'FAILED'    ),
            ( 0x0006, 'TIMEOUT'   ),
            ( 0x0007, 'NODE_FAIL' ),
            ( 0x0008, 'PREEMPTED' ),
            ( 0x0009, 'BOOT_FAIL' ),
            ( 0x000A, 'END'       ),
        ]

        slurm_extra_states = [
            ( 0x8000, 'COMPLETING'    ),
            ( 0x4000, 'CONFIGURING'   ),
            ( 0x2000, 'RESIZING'      ),
            ( 0x1000, 'SPECIAL_EXIT'  ),
            ( 0x0800, 'REQUEUE_HOLD'  ),
            ( 0x0400, 'REQUEUE'       ),
            ( 0x0200, 'STOPPED'       ),
            ( 0x0100, 'LAUNCH_FAILED' ),
        ]

        for hexval, txtstate in slurm_base_states:
            if (state & 0xff) == hexval:
                states.append(txtstate)

        for hexval, txtstate in slurm_extra_states:
            if state & hexval:
                states.append(txtstate)

        if not len(states):
            states.append('UNKNOWN')

        return '+'.join(states)

    def update(self):
        """Update and save loaded Jobs in HPCStats DB."""

        for job in self.jobs:
            if job.find(self.db):
                job.update(self.db)
                for run in job.runs:
                    if not run.existing(self.db):
                        run.save(self.db)
            else:
                job.save(self.db)
                for run in job.runs:
                    run.save(self.db)
