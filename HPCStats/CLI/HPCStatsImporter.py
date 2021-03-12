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

"""This module contains the HPCStatsImporter class."""

import logging
logger = logging.getLogger(__name__)

from HPCStats.Exceptions import HPCStatsRuntimeError, HPCStatsSourceError
from HPCStats.CLI.HPCStatsApp import HPCStatsApp
from HPCStats.Importer.Jobs.JobImporterFactory import JobImporterFactory
from HPCStats.Importer.Users.UserImporterFactory import UserImporterFactory
from HPCStats.Importer.Architectures.ArchitectureImporterFactory import ArchitectureImporterFactory
from HPCStats.Importer.Events.EventImporterFactory import EventImporterFactory
from HPCStats.Importer.FSQuota.FSQuotaImporterFactory import FSQuotaImporterFactory
from HPCStats.Importer.FSUsage.FSUsageImporterFactory import FSUsageImporterFactory
from HPCStats.Importer.BusinessCodes.BusinessCodeImporterFactory import BusinessCodeImporterFactory
from HPCStats.Importer.Projects.ProjectImporterFactory import ProjectImporterFactory

class HPCStatsImporter(HPCStatsApp):

    """HPCStats Importer application which import data from various sources
       and update the database.
    """

    def __init__(self, conf, cluster_name, params):

        super(HPCStatsImporter, self).__init__(conf, cluster_name)

        self.params = params

        # all importer objects
        self.business = None
        self.projects = None
        self.arch = None
        self.mounts = None
        self.fsusage = None
        self.events = None
        self.users = None
        self.jobs = None

    def run(self):
        """Run HPCStats Importer application."""

        self.run_check()

        db = self.new_db()

        # import projects and business code that are globals and not related
        # to a specific cluster
        logger.info("updating projects")
        self.projects = ProjectImporterFactory.factory(self, db, self.conf)
        self.projects.load()
        self.projects.update()

        logger.info("updating business codes")
        self.business = \
          BusinessCodeImporterFactory.factory(self, db, self.conf)
        self.business.load()
        self.business.update()

        if self.cluster_name == 'all':
            clusters = self.conf.get_clusters_list()
        else:
            clusters = [ self.cluster_name ]

        for cluster_name in clusters:
            try:
                self.import_cluster_data(db, cluster_name)
            except HPCStatsSourceError, err:
                logger.error("Error while importing data from cluster %s: %s",
                             cluster_name, err)

        db.commit()
        db.unbind()

    def import_cluster_data(self, db, cluster_name):
        """Import from sources all data specific to a cluster."""

        cluster = None

        #
        # Architecture Importer is both responsible for importing/updating data
        # about cluster and nodes in database and creating the Cluster object
        # for other importers.
        #
        logger.info("updating architecture for cluster %s", cluster_name)
        self.arch = \
          ArchitectureImporterFactory.factory(self, db, self.conf,
                                              cluster_name)
        self.arch.load()
        self.arch.update()

        cluster = self.arch.cluster

        # check that cluster has been properly created and initialized
        if cluster is None or cluster.cluster_id is None:
            raise HPCStatsRuntimeError("problem in DB with cluster %s"
                                         % (str(cluster)))

        logger.info("updating users for cluster %s", cluster.name)
        self.users = \
          UserImporterFactory.factory(self, db, self.conf, cluster)
        self.users.load()
        self.users.update()

        logger.info("updating filesystem usage for cluster %s", cluster.name)
        self.fsusage = \
          FSUsageImporterFactory.factory(self, db, self.conf, cluster)
        self.fsusage.load()
        self.fsusage.update()

        logger.info("updating filesystem quota for cluster %s", cluster.name)
        self.fsquota = \
          FSQuotaImporterFactory.factory(self, db, self.conf, cluster)
        self.fsquota.load()
        self.fsquota.update()

        logger.info("updating events for cluster %s", cluster.name)
        self.events = \
          EventImporterFactory.factory(self, db, self.conf, cluster)
        self.events.load()
        self.events.update()

        logger.info("updating jobs for cluster %s", cluster.name)
        self.jobs = JobImporterFactory.factory(self, db, self.conf, cluster)
        self.jobs.load_update_window()

    def cleanup(self):
        """Clean-up the application before exit."""
        pass
