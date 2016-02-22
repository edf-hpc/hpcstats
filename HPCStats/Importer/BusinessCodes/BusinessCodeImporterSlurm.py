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
   This module import business codes from wckeys in Slurm accouting database.
"""

import MySQLdb
import _mysql_exceptions
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors
from HPCStats.Importer.BusinessCodes.BusinessCodeImporter import BusinessCodeImporter
from HPCStats.Model.Business import Business
from HPCStats.Exceptions import HPCStatsSourceError

class BusinessCodeImporterSlurm(BusinessCodeImporter):

    """Main class of this module."""

    def __init__(self, app, db, config):

        super(BusinessCodeImporterSlurm, self).__init__(app, db, config)

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
        """Connects to all known Slurm databases to extract business codes
           from jobs wckeys. Raises HPCStatsSourceError in case of error.
        """

        self.businesses = []

        for cluster in self.clusters_db.keys():
            self.load_cluster(cluster)

    def load_cluster(self, cluster):
        """Connect to cluster Slurm database to extract business codes from
           jobs wckeys. Raises HPCStatsSourceError in case of error.
        """

        self.log.debug("loading business codes from %s slurm database", cluster)

        self.connect_db(cluster)

        req = """
                SELECT DISTINCT(wckey)
                  FROM %s_job_table
              """ % (cluster)

        self.cur.execute(req)

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
                        self.log.warn(Errors.E_B0001,
                                      "format of wckey %s is not valid",
                                      wckey)
                    continue
                else:
                    business_code = wckey_items[1]
                    business = Business(code=business_code,
                                        description=None)

                # check for duplicate project
                if not self.find(business):
                    self.businesses.append(business)

    def update(self):
        """Create BusinessCodes in database. It does not update BusinessCodes
           as they have no description when they are imported from Slurm and
           operators could have added description using ``hpcstats modify``.
        """

        for business in self.businesses:
            if not business.existing(self.db):
                business.save(self.db)
