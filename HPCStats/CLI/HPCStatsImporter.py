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

import logging

from HPCStats.CLI.HPCStatsApp import HPCStatsApp
from HPCStats.Exceptions import *

from HPCStats.Importer.Jobs.JobImporterFactory import JobImporterFactory
from HPCStats.Importer.Users.UserImporterFactory import UserImporterFactory
from HPCStats.Importer.Architectures.ArchitectureImporterFactory import ArchitectureImporterFactory
from HPCStats.Importer.Events.EventImporterFactory import EventImporterFactory
from HPCStats.Importer.Usage.UsageImporterFactory import UsageImporterFactory
from HPCStats.Importer.MountPoint.MountPointImporterFactory import MountPointImporterFactory
from HPCStats.Importer.Contexts.ContextImporterFactory import ContextImporterFactory
from HPCStats.Importer.BusinessCodes.BusinessCodeImporterFactory import BusinessCodeImporterFactory
from HPCStats.Importer.Projects.ProjectImporterFactory import ProjectImporterFactory
from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm
from HPCStats.Model.Cluster import Cluster
from HPCStats.Model.Project import Project
from HPCStats.Model.Business import Business
from HPCStats.Model.ContextAccount import ContextAccount

class HPCStatsImporter(HPCStatsApp):

    """HPCStats Importer application which import data from various sources
       and update the database.
    """

    def __init__(self, conf, cluster_name):

        super(HPCStatsImporter, self).__init__(conf, cluster_name)

        # all importer objects
        self.context = None
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

        db = self.new_db()

        # import projects and business code that are globals and not related
        # to a specific cluster
        logging.info("updating projects")
        self.projects = ProjectImporterFactory().factory(self, db, self.conf)
        self.projects.load()
        self.projects.update()

        logging.info("updating business codes")
        self.business = BusinessCodeImporterFactory().factory(self, db, self.conf)

        if self.cluster_name == 'all':
            clusters = self.conf.get_clusters_list()
        else:
            clusters = [ self.cluster_name ]

        for cluster_name in clusters:
            self.import_cluster_data(cluster_name)

        db.unbind()

    def import_cluster_data(self, cluster_name):
        """Import from sources all data specific to a cluster."""

        cluster = None

        #
        # Architecture Importer is both responsible for importing/updating data
        # about cluster and nodes in database and creating the Cluster object
        # for other importers.
        #
        logging.info("updating architecture for cluster %s" % (cluster_name))
        try:
            self.arch = ArchitectureImporterFactory().factory(self, db, self.conf, cluster_name)
            self.arch.load()
            self.arch.update()
            cluster = self.arch.cluster
        except RuntimeError:
            logging.error("error occured on %s architecture update." % (cluster_name))

        # check that cluster has been properly created and initialized
        if cluster is None or cluster.cluster_id is None:
            raise HPCStatsRuntimeError("problem in DB with cluster %s" % (str(cluster)))

        logging.info("updating context for cluster %s from stats file" % (cluster.name))
        try:
            self.context = ContextImporterFactory().factory(self, db, config, cluster)
        except RuntimeError:
            logging.error("error occured on %s context update." % (cluster.name))

        logging.info("updating mounted filesystem for cluster %s" % (cluster.name))
        try:
            self.mounts = MountPointImporterFactory().factory(self, db, config, cluster)
            if self.mounts:
                self.mounts.update_mount_point()
                db.commit()
        except RuntimeError:
            logging.error("error occured on %s mounted filesystem update." (cluster.name))

        logging.info("updating filesystem usage for cluster %s" % (cluster.name))
        try:
            self.fsusage = UsageImporterFactory().factory(self, db, config, cluster)
            db.commit()
        except RuntimeError:
            logging.error("error occured on %s filesystem usage update." % (cluster.name))

        logging.info("updating events for cluster %s" % (cluster.name))
        try:
            self.events = EventImporterFactory().factory(self, db, config, cluster)
            self.events.update_events()
            db.commit()
        except RuntimeError:
            logging.error("error occured on %s events update." % (cluster.name))

        logging.info("updating users for cluster %s" % (cluster.name))
        try:
          self.users = UserImporterFactory().factory(self, db, config, cluster)
          self.users.update_users()
          db.commit()
        except RuntimeError:
            logging.error("error occured on %s users update." % (cluster.name))

        logging.info("updating jobs for cluster %s" % (cluster.name))
        try:
            self.jobs = JobImporterFactory().factory(self, db, config, cluster)
            # The last updated job in hpcstatsdb for this cluster
            last_updated_id = self.jobs.get_last_job_id()
            # The unfinished jobs in hpcstatsdb for this cluster
            ids = self.jobs.get_unfinished_job_id()

            jobs_to_update = ['not_empty']
            new_jobs = ['not_empty']

            offset = 0
            max_jobs = 100000

            logging.debug("Get jobs to update")
            jobs_to_update = self.jobs.get_job_information_from_dbid_job_list(ids)
            for job in jobs_to_update:
                offset = offset + 1
                if not offset % 10:
                    logging.debug("update job push %d" % offset)
                job.update(db)
            offset = 0
            while new_jobs:
                logging.debug("get %d new jobs starting at offset %d" % (max_jobs, offset))
                new_jobs = self.jobs.get_job_for_id_above(last_updated_id, offset, max_jobs)
                for job in new_jobs:
                    offset = offset + 1
                    if not offset % 10000:
                        logging.debug("create job push %d" % offset)
                    job.save(db)
                    # get wckeys from job to insert in context tab.
                    wckey = self.jobs.get_wckey_from_job(job._id_job)
                    if wckey != None and wckey != '*' and wckey != '' and wckey.find(":") >= 0 :
                        logging.debug("get wc_key %s" % (wckey))
                        context = Context()
                        # get pareo and business from job
                        try:
                            pareo = wckey.split(":")[0]
                        except :
                            pareo = None
                            logging.debug("pareo value is unavailable")
                        try:
                            business = wckey.split(":")[1]
                        except:
                            business = None
                            logging.debug("business value is unavailable")
                        # verify if pareo and business exist
                        try:
                            context.set_project(get_pareo_id(db, pareo))
                        except:
                            context.set_project(None)
                            logging.debug("pareo does not exist")
                        try:
                            context.set_business(get_business_id(db, business))
                        except:
                            context.set_business(None)
                            logging.debug("business does not exist")
                        # create context if you have one or both
                        if context.get_business() or context.get_project():
                            context.set_login(job._login)
                            context.set_job(job._db_id)
                            context.set_cluster(cluster.name)
                            context.save(db)
                            logging.debug("create new context : %s" % context)
                        else:
                            logging.debug("abort creating context")
                    else:
                        logging.debug("no wc_keys available for this job")
            db.commit()
        except :
            logging.error("error occured on %s jobs update." % (cluster.name))

    def cleanup(self):
        """Clean-up the application before exit."""
        pass
