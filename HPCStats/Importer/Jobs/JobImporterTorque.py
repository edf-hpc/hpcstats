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

import re, os
import logging
from datetime import datetime
from ClusterShell.NodeSet import NodeSet
from HPCStats.Importer.Jobs.JobImporter import JobImporter
from HPCStats.Model.Job import Job

# 02/01/2012 18:56:28;E;5802977.clay1pno;user=martin group=lnhe jobname=2009_juil_dec queue=parall_64 ctime=1328114089 qtime=1328114089 etime=1328114089 start=1328114090 owner=martin@clay1pfr exec_host=cla1a184/7+cla1a184/6+cla1a184/5+cla1a184/4+cla1a184/3+cla1a184/2+cla1a184/1+cla1a184/0+cla1a185/7+cla1a185/6+cla1a185/5+cla1a185/4+cla1a185/3+cla1a185/2+cla1a185/1+cla1a185/0+cla1b003/7+cla1b003/6+cla1b003/5+cla1b003/4+cla1b003/3+cla1b003/2+cla1b003/1+cla1b003/0+cla1b004/7+cla1b004/6+cla1b004/5+cla1b004/4+cla1b004/3+cla1b004/2+cla1b004/1+cla1b004/0 Resource_List.neednodes=4:ppn=8 Resource_List.nodect=4 Resource_List.nodes=4:ppn=8 Resource_List.walltime=06:00:00 session=8351 end=1328118988 Exit_status=0 resources_used.cput=40:56:18 resources_used.mem=1270208kb resources_used.vmem=6968788kb resources_used.walltime=01:21:38

# ('02/01/2012 18:56:28', '5802977', None, 'martin', None, 'lnhe', 'parall_64', '1328114089', '1328114089', '1328114090', 'cla1a184/7+cla1a184/6+cla1a184/5+cla1a184/4+cla1a184/3+cla1a184/2+cla1a184/1+cla1a184/0+cla1a185/7+cla1a185/6+cla1a185/5+cla1a185/4+cla1a185/3+cla1a185/2+cla1a185/1+cla1a185/0+cla1b003/7+cla1b003/6+cla1b003/5+cla1b003/4+cla1b003/3+cla1b003/2+cla1b003/1+cla1b003/0+cla1b004/7+cla1b004/6+cla1b004/5+cla1b004/4+cla1b004/3+cla1b004/2+cla1b004/1+cla1b004/0', '06:00:00')

class JobImporterTorque(JobImporter):

    def __init__(self, app, db, config, cluster):

        super(JobImporterTorque, self).__init__(app, db, config, cluster)

        self._logpat = re.compile('(.{19});E;(\d+)(?:-(\d+))?\..*;user=(\S+) (?:account=(\S+))?.*group=(\S+).*queue=(\S+) ctime=\d+ qtime=(\d+) etime=(\d+) start=(\d+) .* exec_host=(\S+) .* Exit_status=(\d+) .*\n')
        self._exechostpat = re.compile('/\d+')

        db_section = self.cluster.name + "/torque"
        self._logfolder = config.get(db_section,"logdir")

    def get_job_information_from_dbid_job_list(self,ids_job):
        # No need to update with Torque
        return []

    def account_files_to_check(self, last_id_job):
#FIXME        last_filename = last_id_job
        filenames = os.listdir(self._logfolder)
        return filenames

    def get_job_for_id_above(self, last_id_job):
        jobs = []
        filenames = self.account_files_to_check(last_id_job)
        index = 0
        nbfiles = len(filenames)
        for filename in filenames:
            index =  index + 1
            logging.debug(" Filename : %s (%d / %d)",filename, index, nbfiles )
            accountfile = open( self._logfolder + "/" + filename,'r')
            for line in accountfile.readlines():
                match = self._logpat.match(line)
                if match:
                    jobinfo = match.groups()
                    jobs.append(self.job_from_information(jobinfo, filename))
        return jobs

    def job_from_information(self, res, filename):
        nbprocs, nbnodes, nodelist = self.torque_job_nodelist(res[10])
        uuid, ugid = self.get_uid_gid_from_login(res[3])
        job = Job(  id_job = int(res[1]),
                    sched_id = filename,
                    uid = uuid,
                    gid = ugid,
                    submission_datetime = datetime.fromtimestamp(int(res[7])),
                    running_datetime = datetime.fromtimestamp(int(res[8])),
                    end_datetime = datetime.fromtimestamp(int(res[9])),
                    nb_procs = nbprocs,
                    nb_hosts = nbnodes,
                    running_queue = res[6],
                    nodes = nodelist,
                    state = self.get_job_state_from_torque_state(res[11]),
                    cluster_name = self.cluster.name)
        return job

    def get_job_state_from_torque_state(self, state):
        if int(state)  == 0:
            return "COMPLETE"
        else :
            return "UNKNOWN"

    # override parent class
    def get_unfinished_job_id(self):
        # Torque always put in DB finished jobs
        return []

    # useful functions
    def torque_job_status_converter(self):
        return ""

    def torque_job_nodelist(self,nodelist):
        nodelist = self._exechostpat.sub('',nodelist)
        nodelist = nodelist.split('+')
        nbprocs = len(nodelist)
        nodelist = NodeSet.fromlist(nodelist)
        nbnodes = len(nodelist)
        nodelist = str(nodelist)
        return nbprocs, nbnodes, nodelist

    def get_uid_gid_from_login(self, login):
        req = """
            SELECT uid, gid
            FROM users
            WHERE cluster = %s AND login = %s; """
        datas = (self.cluster.name, login)
        cur = self._db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        results = cur.fetchall()
        if len(results) > 0:
            (uid, gid) = results[0]
        else :
            (uid, gid) = 0, 0
        return uid, gid
