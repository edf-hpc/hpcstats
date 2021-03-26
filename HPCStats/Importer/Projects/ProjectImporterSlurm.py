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

"""
   This module import projects from wckeys in Slurm accouting database.
"""

import logging
logger = logging.getLogger(__name__)
import MySQLdb
import _mysql_exceptions
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors
from HPCStats.Importer.Projects.ProjectImporter import ProjectImporter
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Project import Project
from HPCStats.Exceptions import HPCStatsSourceError

class ProjectImporterSlurm(ProjectImporter):

    """Main class of this module."""

    def __init__(self, app, db, config):

        super(ProjectImporterSlurm, self).__init__(app, db, config)

        section = 'projects'
        self.default_domain_key = config.get(section, 'default_domain_key')
        self.default_domain_name = config.get(section, 'default_domain_name')
        self.default_domain = None

        self.clusters_db = dict()
        clusters = config.get_clusters_list()
        for cluster in clusters:
            section = cluster + '/slurm'
            if config.has_section(section):
                self.clusters_db[cluster] = dict()
                self.clusters_db[cluster]['dbhost'] = \
                  config.get(section, 'host')
                self.clusters_db[cluster]['dbport'] = \
                  int(config.get(section, 'port'))
                self.clusters_db[cluster]['dbname'] = \
                  config.get(section, 'name')
                self.clusters_db[cluster]['dbuser'] = \
                  config.get(section, 'user')
                self.clusters_db[cluster]['dbpass'] = \
                  config.get_default(section, 'password', None)
                self.clusters_db[cluster]['prefix'] = \
                  config.get_default(section, 'prefix', cluster)
                self.clusters_db[cluster]['partitions'] = \
                  config.get_list(section, 'partitions')

        self.invalid_wckeys = []

        self.conn = None
        self.cur = None

    def connect_db(self, cluster):
        """Connect to a cluster Slurm database and set conn/cur attributes
           accordingly.
        """

        try:
            conn_params = {
               'host': self.clusters_db[cluster]['dbhost'],
               'user': self.clusters_db[cluster]['dbuser'],
               'db':   self.clusters_db[cluster]['dbname'],
               'port': self.clusters_db[cluster]['dbport'],
            }
            if self.clusters_db[cluster]['dbpass'] is not None:
                conn_params['passwd'] = self.clusters_db[cluster]['dbpass']

            self.conn = MySQLdb.connect(**conn_params)
            self.cur = self.conn.cursor()
        except _mysql_exceptions.OperationalError as error:
            raise HPCStatsSourceError( \
                    "connection to Slurm DBD MySQL failed: %s" % (error))

    def disconnect_db(self):
        """Disconnect to currently connected Slurm DB."""

        self.cur.close()
        self.conn.close()

    def check(self):
        """Check if all Slurm databases are available and if we connect to
           them.
        """

        for cluster in self.clusters_db.keys():
            self.connect_db(cluster)
            self.disconnect_db()

    def load(self):
        """Connects to all known Slurm databases to extract project codes
           in jobs wckeys. If a cluster raises a HPCStatsSourceError, it
           prints an error and continues with the next one.
        """

        self.domains = []
        self.projects = []

        self.default_domain = Domain(self.default_domain_key,
                                     self.default_domain_name)
        self.domains.append(self.default_domain)

        for cluster in self.clusters_db.keys():
            try:
                self.load_cluster(cluster)
            except HPCStatsSourceError as err:
                logger.error("Error with cluster %s: %s", cluster, err)


    def load_cluster(self, cluster):
        """Connect to cluster Slurm database to extract project codes from
           jobs wckeys. Raises HPCStatsSourceError in case of error.
        """

        self.log.debug("loading project codes from %s slurm database", cluster)

        self.connect_db(cluster)

        if not len(self.clusters_db[cluster]['partitions']):
            partitions_clause = ''
        else:
            partitions_clause = \
                "WHERE job.partition IN (%s)" % \
                ','.join(['%s'] * len(self.clusters_db[cluster]['partitions']))

        req = """
                SELECT DISTINCT(wckey)
                  FROM %s_job_table job
                  %s
              """ % (self.clusters_db[cluster]['prefix'],
                     partitions_clause)

        params = tuple(self.clusters_db[cluster]['partitions'])
        self.cur.execute(req, params)

        while (1):
            row = self.cur.fetchone()
            if row == None:
                break

            wckey = row[0]

            if wckey == '':
                continue
            else:
                wckey_items = wckey.split(':')
                if len(wckey_items) != 2:
                    if wckey not in self.invalid_wckeys:
                        self.invalid_wckeys.append(wckey)
                        self.log.warn(Errors.E_P0001,
                                      "format of wckey %s is not valid",
                                      wckey)
                    continue
                else:
                    project_code = wckey_items[0]
                    project = Project(domain=self.default_domain,
                                      code=project_code,
                                      description=None)

                # check for duplicate project
                if not self.find_project(project):
                    self.projects.append(project)

    def update(self):
        """Create loaded project (with associated domains) in database if not
           existing. It does not update domain nor project since:

             * There is only one default domain which should have created with
               its key and name in the first place, there is no point to update
               it.
             * The project are imported without description from Slurm and are
               linked to default domain. Operators have probably added a
               description to the project and linked it to another proper
               domain and we must not alter these information.
        """

        for domain in self.domains:
            if not domain.existing(self.db):
                domain.save(self.db)
        for project in self.projects:
            if not project.find(self.db):
                self.log.info("creating project %s with default domain",
                              str(project))
                project.save(self.db)
