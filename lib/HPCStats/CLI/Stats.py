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

import sys
import logging

from HPCStats.CLI.StatsOptionParser import StatsOptionParser
from HPCStats.CLI.Config import HPCStatsConfig
from HPCStats.DB.DB import HPCStatsdb
from HPCStats.Finder.ClusterFinder import ClusterFinder
from HPCStats.Importer.Jobs.JobImporterFactory import JobImporterFactory
from HPCStats.Importer.Users.UserImporterFactory import UserImporterFactory
from HPCStats.Importer.Architectures.ArchitectureImporterFactory import ArchitectureImporterFactory
from HPCStats.Importer.Events.EventImporterFactory import EventImporterFactory
from HPCStats.Importer.Usage.UsageImporterFactory import UsageImporterFactory
from HPCStats.Importer.MountPoint.MountPointImporterFactory import MountPointImporterFactory
from HPCStats.Importer.Contexts.ContextImporterFactory import ContextImporterFactory
from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm
from HPCStats.Model.Project import Project, get_pareo_id
from HPCStats.Model.Business import Business, get_business_id
from HPCStats.Model.Context import Context

def HPCStatsUpdater(object):

    def __init__(self, args=sys.argv)

        self.args = args

        # all importer objects
        self.context = None
        self.arch = None
        self.mounts = None
        self.fsusage = None
        self.events = None
        self.users = None
        self.jobs = None

    def run(self):

        # Command line argument parser
        usage = "%prog [options] command"
        parser = StatsOptionParser(usage)
        (options, args) = parser.parse_args(self.args[1:])

        # validate options
        parser.validate(options)

        # configure logging
        # logging_level = logging.INFO
        logging_level = logging.DEBUG
        if options.debug:
            logging_level = logging.DEBUG
        logging.basicConfig(format = '%(levelname)s: %(filename)s: %(message)s',
                            level  = logging_level,
                            stream  = sys.stdout)

        # Config file argument parser
        config = HPCStatsConfig(options)

        # dump entire config file
        for section in config.sections():
            logging.debug(section)
            for option in config.options(section):
                logging.debug(" %s = %s", option, config.get(section, option))

        # Instantiate connexion to db
        db_section = "hpcstatsdb"
        dbhostname = config.get(db_section,"hostname")
        dbport = config.get(db_section,"port")
        dbname = config.get(db_section,"dbname")
        dbuser = config.get(db_section,"user")
        dbpass = config.get(db_section,"password")
        db = HPCStatsdb(dbhostname, dbport, dbname, dbuser, dbpass)
        db.bind()

        logging.debug("db information %s %s %s %s %s" % db.infos())

        cluster_finder = ClusterFinder(db)
        cluster = cluster_finder.find(options.clustername)

        if (options.context):
            logging.info("=> Updating context for cluster %s from stats file" % (options.clustername))
            try:
                self.context = ContextImporterFactory().factory(db, config, cluster.get_name())
            except RuntimeError:
                logging.error("error occured on %s context update." % (options.clustername))

        if (options.arch):
            logging.info("=> Updating architecture for cluster %s" % (options.clustername))
            try:
                self.arch = ArchitectureImporterFactory().factory(db, config, cluster.get_name())
                self.arch.update_architecture()
                db.commit()
            except RuntimeError:
                logging.error("error occured on %s architecture update." % (options.clustername))

        if (options.mounted):
            logging.info("=> Updating mounted filesystem for cluster %s" % (options.clustername))
            try:
                self.mounts = MountPointImporterFactory().factory(db, config, cluster.get_name())
                if self.mounts:
                    self.mounts.update_mount_point()
                    db.commit()
            except RuntimeError:
                logging.error("error occured on %s mounted filesystem update." (options.clustername))

        if (options.usage):
            logging.info("=> Updating filesystem usage for cluster %s" % (options.clustername))
            try:
                self.fsusage = UsageImporterFactory().factory(db, config, cluster.get_name())
                db.commit()
            except RuntimeError:
                logging.error("error occured on %s filesystem usage update." % (options.clustername))

        if (options.events):
            logging.info("=> Updating events for cluster %s" % (options.clustername))
            try:
                self.events = EventImporterFactory().factory(db, config, cluster.get_name())
                self.events.update_events()
                db.commit()
            except RuntimeError:
                logging.error("error occured on %s events update." % (options.clustername))

        if (options.users):
            logging.info("=> Updating users for cluster %s" % (options.clustername))
            try:
              self.users = UserImporterFactory().factory(db, config, cluster.get_name())
              self.users.update_users()
              db.commit()
            except RuntimeError:
                logging.error("error occured on %s users update." % (options.clustername))

        if (options.jobs):
            logging.info("=> Update of jobs for cluster %s" % (options.clustername))
            try:
                self.jobs = JobImporterFactory().factory(db, config, cluster.get_name())
                # The last updated job in hpcstatsdb for this cluster
                last_updated_id = self.jobs.get_last_job_id()
                # The unfinished jobs in hpcstatsdb for this cluster
                ids = self.jobs.get_unfinished_job_id()

                jobs_to_update = ['not_empty']
                new_jobs = ['not_empty']

                nb_theads = 4

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
                                context.set_cluster(cluster.get_name())
                                context.save(db)
                                logging.debug("create new context : %s" % context)
                            else:
                                logging.debug("abort creating context")
                        else:
                            logging.debug("no wc_keys available for this job")
                db.commit()
            except :
                logging.error("error occured on %s jobs update." % (options.clustername))

        db.unbind()
