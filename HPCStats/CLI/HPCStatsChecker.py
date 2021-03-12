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

"""This module contains the HPCStatsChecker class."""

import logging
logger = logging.getLogger(__name__)

from HPCStats.CLI.HPCStatsApp import HPCStatsApp
from HPCStats.Importer.Jobs.JobImporterFactory import JobImporterFactory
from HPCStats.Importer.Users.UserImporterFactory import UserImporterFactory
from HPCStats.Importer.Architectures.ArchitectureImporterFactory import ArchitectureImporterFactory
from HPCStats.Importer.Events.EventImporterFactory import EventImporterFactory
from HPCStats.Importer.FSQuota.FSQuotaImporterFactory import FSQuotaImporterFactory
from HPCStats.Importer.FSUsage.FSUsageImporterFactory import FSUsageImporterFactory
from HPCStats.Importer.BusinessCodes.BusinessCodeImporterFactory import BusinessCodeImporterFactory
from HPCStats.Importer.Projects.ProjectImporterFactory import ProjectImporterFactory
from HPCStats.Model.Cluster import Cluster

class HPCStatsChecker(HPCStatsApp):

    """HPCStats Checker application which checks all data sources availability.
    """

    def __init__(self, conf, cluster_name):

        super(HPCStatsChecker, self).__init__(conf, cluster_name)

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
        """Run HPCStats Checker application."""

        self.run_check()

        db = self.new_db()

        # import projects and business code that are globals and not related
        # to a specific cluster
        logger.info("checking projects sources")
        self.projects = ProjectImporterFactory.factory(self, db, self.conf)
        self.projects.check()

        logger.info("checking business codes sources")
        self.business = BusinessCodeImporterFactory.factory(self, db, self.conf)
        self.business.check()

        if self.cluster_name == 'all':
            clusters = self.conf.get_clusters_list()
        else:
            clusters = [ self.cluster_name ]

        for cluster_name in clusters:
            self.check_cluster_sources(db, cluster_name)

        db.commit()
        db.unbind()

    def check_cluster_sources(self, db, cluster_name):
        """Check data sources for a cluster."""

        cluster = None

        logger.info("checking architecture source for cluster %s",
                    cluster_name)
        self.arch = \
          ArchitectureImporterFactory.factory(self, db, self.conf,
                                              cluster_name)
        self.arch.check()

        cluster = Cluster(cluster_name)

        logger.info("checking users source for cluster %s",
                    cluster.name)
        self.users = \
          UserImporterFactory.factory(self, db, self.conf, cluster)
        self.users.check()

        logger.info("checking filesystem usage source for cluster %s",
                    cluster.name)
        self.fsusage = \
          FSUsageImporterFactory.factory(self, db, self.conf, cluster)
        self.fsusage.check()

        logger.info("checking filesystem quota source for cluster %s",
                    cluster.name)
        self.fsquota = \
          FSQuotaImporterFactory.factory(self, db, self.conf, cluster)
        self.fsquota.check()

        logger.info("checking events source for cluster %s",
                    cluster.name)
        self.events = \
          EventImporterFactory.factory(self, db, self.conf, cluster)
        self.events.check()

        logger.info("checking jobs source for cluster %s",
                    cluster.name)
        self.jobs = \
          JobImporterFactory.factory(self, db, self.conf, cluster)
        self.jobs.check()

        logger.info("every sources are properly available")

    def cleanup(self):
        """Clean-up the application before exit."""
        pass
