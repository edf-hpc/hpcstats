#!/usr/bin/python
# -*- coding: utf-8 -*-
# This file is part of HPCStats
#
# Copyright (C) 2011-2012 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
#
#Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#This program is free software; you can redistribute in and/or
#modify it under the terms of the GNU General Public License,
#version 2, as published by the Free Software Foundation.
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#On Calibre systems, the complete text of the GNU General
#Public License can be found in `/usr/share/common-licenses/GPL'.

###############################################################


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

def main(args=sys.argv):

    # Command line argument parser
    usage = "%prog [options] command"
    parser = StatsOptionParser(usage)
    (options, args) = parser.parse_args(args[1:])

    # validate options
    parser.validate(options)

    # configure logging
    logging_level = logging.INFO
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
            context_importer = ContextImporterFactory().factory(db, config, cluster.get_name())
        except RuntimeError:
            logging.error("error occured on context update.")

    if (options.arch):
        logging.info("=> Updating architecture for cluster %s" % (options.clustername))
        try:
            arch_importer = ArchitectureImporterFactory().factory(db, config, cluster.get_name())
            arch_importer.update_architecture()
            db.commit()
        except RuntimeError:
            logging.error("error occured on architecture update.")

    if (options.mounted):
        logging.info("=> Updating mounted filesystem for cluster %s" % (options.clustername))
        try:
            mounted_importer = MountPointImporterFactory().factory(db, config, cluster.get_name())
            if mounted_importer:
                mounted_importer.update_mount_point()
                db.commit()
        except RuntimeError:
            logging.error("error occured on mounted filesystem update.")
 
    if (options.usage):
        logging.info("=> Updating filesystem usage for cluster %s" % (options.clustername))
        try:
            usage_importer = UsageImporterFactory().factory(db, config, cluster.get_name())
            #usage_importer.update_usage()
            db.commit()
        except RuntimeError:
            logging.error("error occured on filesystem usage update.")

    if (options.events):
        logging.info("=> Updating events for cluster %s" % (options.clustername))
        try:
            event_importer = EventImporterFactory().factory(db, config, cluster.get_name())
            event_importer.update_events()
            db.commit()
        except RuntimeError:
            logging.error("error occured on events update.")

    if (options.users):
        logging.info("=> Updating users for cluster %s" % (options.clustername))
        try:
          user_importer = UserImporterFactory().factory(db, config, cluster.get_name())
          user_importer.update_users()
          db.commit()
        except RuntimeError:
            logging.error("error occured on users update.")

    if (options.jobs):
        logging.info("=> Update of jobs for cluster %s" % (options.clustername))
        try:
            job_importer = JobImporterFactory().factory(db, config, cluster.get_name())
            # The last updated job in hpcstatsdb for this cluster
            last_updated_id = job_importer.get_last_job_id()
            # The unfinished jobs in hpcstatsdb for this cluster
            ids = job_importer.get_unfinished_job_id()
    
            jobs_to_update = ['not_empty']
            new_jobs = ['not_empty']
    
            nb_theads = 4
    
            offset = 0
            max_jobs = 100000
    
            logging.debug("Get jobs to update")
            jobs_to_update = job_importer.get_job_information_from_dbid_job_list(ids)
            for job in jobs_to_update:
                offset = offset + 1
                if not offset % 10:
                    logging.debug("update job push %d" % offset)
                job.update(db)
    
            offset = 0
    
            while new_jobs:
                logging.debug("Get %d new jobs starting at offset %d" % (max_jobs, offset))
                new_jobs = job_importer.get_job_for_id_above(last_updated_id, offset, max_jobs)
                for job in new_jobs:
                    offset = offset + 1
                    if not offset % 10000:
                        logging.debug("create job push %d" % offset)
                    job.save(db)
    
            db.commit()
        except RuntimeError:
            logging.error("error occured on jobs update.")
        
    db.unbind()

