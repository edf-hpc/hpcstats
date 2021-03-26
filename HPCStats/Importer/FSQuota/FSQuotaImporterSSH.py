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

"""This module contains the FSQuotaImporterSSH class."""

from operator import attrgetter
from datetime import datetime
import os
import paramiko
import socket
import csv
import tempfile
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Importer.FSQuota.FSQuotaImporter import FSQuotaImporter
from HPCStats.Model.Filesystem import Filesystem
from HPCStats.Model.FSQuota import FSQuota, get_last_fsquota_datetime

class FSQuotaImporterSSH(FSQuotaImporter):

    """This class imports FSQuota data from a CSV file available through
       SSH on a remote server.
    """

    def __init__(self, app, db, config, cluster):

        super(FSQuotaImporterSSH, self).__init__(app, db, config, cluster)

        section = self.cluster.name + "/fsquota"

        self.ssh_host = config.get(section, 'host')
        self.ssh_user = config.get(section, 'user')
        self.ssh_pkey = config.get(section, 'pkey')
        self.fqfile = config.get(section, 'file')

        self.timestamp_fmt = config.get_default(section, 'timestamp_fmt',
                                                '%Y-%m-%dT%H:%M:%S.%fZ')

        self.filesystems = None # loaded filesystems
        self.fsquotas = None    # loaded fsquotas

    def connect_ssh(self):
        """Connect through SSH to remote server and return connection handler.
           Raises HPCStatsSourceError in case of problem.
        """

        try:
            self.log.debug("ssh connection to %s@%s",
                           self.ssh_user,
                           self.ssh_host)
            ssh = paramiko.SSHClient()
            # set automatically RSA key on known_hosts file
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ssh_host,
                        username=self.ssh_user,
                        key_filename=self.ssh_pkey)
        except (paramiko.AuthenticationException,
                paramiko.SSHException,
                socket.error) as err:
            raise HPCStatsSourceError( \
                    "unable to connect by SSH to %s@%s: %s" % \
                      (self.ssh_user, self.ssh_host, err))
        return ssh

    def check(self):
        """Check if the remote SSH server is available for connections, if
           the remote CSV file can be opened and is not empty.
           Raises HPCStatsSourceError in case of problem.
        """
        ssh = self.connect_ssh()
        try:
            sftp = ssh.open_sftp()
        except paramiko.SFTPError as err:
            raise HPCStatsSourceError( \
                    "Error while opening SFTP connection: %s" \
                      % (err))
        try:
            sftpfile = sftp.open(self.fqfile, 'r')
        except IOError as err:
            raise HPCStatsSourceError( \
                    "Error while opening file %s by SFTP: %s" \
                      % (self.fqfile, err))
        if sftpfile.readline() == "":
            raise HPCStatsSourceError( \
                    "Remote file %s is empty" \
                      % (self.fqfile))
        sftp.close()
        ssh.close()

    def load(self):
        """Load Filesystems and FSQuotas from CSV logfile read through SSH.
           Raises HPCStatsSourceError if any error is encountered.
        """

        self.filesystems = []
        self.fsquotas = []

        ssh = self.connect_ssh()

        # The remote file is accessed through SFTP. We could have used
        # Paramiko sftp.open() but iterating over a long file (line by line)
        # is quite slow. We prefer to download the full file to a local
        # temporary file and then read/parse this local file.
        try:
            sftp = ssh.open_sftp()
        except paramiko.SFTPError as err:
            raise HPCStatsSourceError( \
                    "Error while opening SFTP connection: %s" \
                      % (err))

        (tmp_fh, tmp_fpath) = tempfile.mkstemp()
        os.close(tmp_fh) # immediately close since we do not need it

        # download file through SFTP
        try:
            sftp.get(self.fqfile, tmp_fpath)
        except IOError as err:
            raise HPCStatsSourceError( \
                    "Error while downloading file %s by SFTP: %s" \
                      % (self.fqfile, err))

        # close sftp and ssh since we do not need them anymore.
        sftp.close()
        ssh.close()

        with open(tmp_fpath, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            for row in csvreader:
                mountpoint = row[2]
                if mountpoint[0] != '/':
                    mountpoint = '/'+mountpoint
                try:
                    logtime = datetime.strptime(row[0], self.timestamp_fmt)
                except ValueError as err:
                    raise HPCStatsSourceError( \
                            "error while parsing log time: %s" % (err))
#                bpercent = float(row[2])
                name = row[1]
                typeusr = row[3]
                block_KB = row[4]
                block_quota = row[5]
                block_limit = row[6]
                block_in_doubt = row[7]
                block_grace = row[8]
                file_files = row[9]
                file_quota = row[10]
                file_limit = row[11]
                file_in_doubt = row[12]
                file_grace = row[13]
#                ipercent = None
#                if len(row) >= 4:
#                    ipercent = float(row[3])
                newfs = Filesystem(mountpoint, self.cluster)
                fs = None
                # search if fs not already defined
                for xfs in self.filesystems:
                    if xfs == newfs:
                        fs = xfs
                if fs is None:
                    # newfs not found in defined fs
                    self.filesystems.append(newfs)
                    fs = newfs
                fsquota = FSQuota(fs, logtime, name, block_KB, block_quota,
                                  block_limit, block_in_doubt, block_grace,
                                  file_files, file_quota, file_limit,
                                  file_in_doubt, file_grace)
                self.fsquotas.append(fsquota)

        # sort fsquotas by datetime in asc. order
        self.fsquotas.sort(key=attrgetter('timestamp'))

    def update(self):
        """Update Filesystems and FSQuota in DB."""

        last_fs_usage_datetimes = dict()

        for fs in self.filesystems:
            # There is nothing to udpate for filesystem so just save them
            # if they do not exist in DB.
            if not fs.find(self.db):
                fs.save(self.db)
            last_fs_usage_datetimes[fs.mountpoint] = \
              get_last_fsquota_datetime(self.db, self.cluster, fs)#, self.name

        for fsquota in self.fsquotas:
            # save only new fsusage, ie. with datetime over last datetime in DB
            last = last_fs_usage_datetimes[fsquota.filesystem.mountpoint]
            if last is None or fsquota.timestamp > last:
                fsquota.save(self.db)
