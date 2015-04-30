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

from datetime import datetime
import time
import base64
import logging
import sys
import paramiko
import errno
import socket
import csv
from HPCStats.Importer.Usage.UsageImporter import UsageImporter
from HPCStats.Model.Filesystem import Filesystem
from HPCStats.Model.Filesystem_usage import Filesystem_usage

class UsageImporterCluster(UsageImporter):

    def __init__(self, app, db, config, cluster):

        super(UsageImporter, self).__init__(app, db, config, cluster)

        usage_section = self.cluster.name + "/usage"

        self._fshost = config.get(usage_section,"host")
        self._fsname = config.get(usage_section,"name")
        # No need to set self._fspassword if you had delivered public ssh key
        #self._fspassword = config.get(usage_section,"password")
        self._fsfile = config.get(usage_section,"file")
        self._fs_usage = [] #List of usages for a fs
        self._usage = [] #Output file from ssh connection
 
        try:
            logging.info("Start ssh connection on cluster %s", self.cluster.name)
            #Paramiko is used to initiate ssh connection
            self._ssh = paramiko.SSHClient()
            #Set automatically RSA key on known_hosts file
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh.connect(self._fshost, username=self._fsname)
            # No need to use password if you had delivered public ssh key
            #self._ssh.connect(self._fshost, username=self._fsname, \
            #    password=base64.b64decode( \
            #    self.decypher(base64.b64decode(self._fspassword))))
            #Send shell command via ssh
            self._stdin, self._stdout, self._stderr = self._ssh.exec_command \
                ("cat %s*" %self._fsfile)
            self._usage = self._stdout.readlines()
            #print self._usage
            #Get filesytem from HPCStats db
            fs_list = Filesystem().get_fs_for_cluster(self.db, self.cluster)
            logging.info("Get fs for cluster %s : %s", self.cluster.name, fs_list)

            #For all files system on the cluster
            for fs in fs_list:
                #Innitiate fs_usage for new fs
                self._fs_usage = []
                #Get last fs timestamp from HPCStats db
                timestamp = self._get_last_fs_timestamp_usage(fs)
                logging.info("Get %s %s last timestamp : %s", \
                              self.cluster.name, fs, timestamp )
                if timestamp:
                    #Get usage list from cluster
                    logging.info("Get new %s %s usages", self.cluster.name, fs)
                    self._get_usage_list(fs, timestamp)
                #Update HPCStats database with new values
                if self._fs_usage:
                    logging.info("List of %s usages to add for cluster %s : %s", \
                          fs, \
                          self.cluster.name, \
                          self._fs_usage)
                    #for fs_usage in self._fs_usage:
                    Filesystem_usage().update_usage(self.db, self.cluster, fs, self._fs_usage)
                else:
                    logging.info("No new %s %s usages", self.cluster.name, fs)


        except (paramiko.AuthenticationException, socket.error ) as e:
            logging.error("ssh connection to cluster %s failed: %s", \
                           self.cluster.name, e)
            raise RuntimeError


    def _get_usage_list(self, fs, timestamp):
        for line in self._usage:
            time_from_line = line.split(',')[1]
            fs_from_line = line.split(',')[0]
            time_list = datetime.strptime(time_from_line, '%Y-%m-%d %H:%M:%S')
            if fs == fs_from_line:
                if time_list > timestamp:
                    self._fs_usage.append((line.split(',')[1], line.split(',')[2], line.split(',')[3]))

    def _get_last_fs_timestamp_usage(self, fs):
        last_usage_timestamp = 0
        req = """
            SELECT MAX(timestamp) AS last_usage
            FROM filesystem_usage, filesystem
            WHERE filesystem_usage.fs_id=filesystem.id
            AND filesystem.cluster = %s
            AND filesystem.mount_point = %s
              ; """
        datas = (self.cluster.name,
                 fs,)
        cur = self.db.cur
        cur.execute(req, datas)
        if cur.fetchone()[0] is None:
            result = datetime(1970, 1, 1, 0, 0)
        else:
            cur.execute(req, datas)
            result = cur.fetchone()[0]
        #logging.info("Get %s %s timestamp : %s", self.cluster.name, fs, result )
        return result

    def decypher(self, s):
        x = []
        for i in xrange(len(s)):
            j = ord(s[i])
            if j >= 33 and j <= 126:
                x.append(chr(33 + ((j + 14) % 94)))
            else:
                x.append(s[i])
        return ''.join(x)
