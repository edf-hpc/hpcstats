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
from HPCStats.CLI.StatsOptionParser import StatsOptionParser
from HPCStats.CLI.Config import HPCStatsConfig
from HPCStats.DB.DB import HPCStatsdb
from HPCStats.Model.Cluster import Cluster
from HPCStats.Importer.Jobs.JobImporter import JobImporter
from HPCStats.Importer.Users.UserImporter import UserImporter
from HPCStats.Importer.Architectures.ArchitectureImporter import ArchitectureImporter

def main(args=sys.argv):

    # Command line argument parser
    usage = "%prog [options] command"
    parser = StatsOptionParser(usage)
    (options, args) = parser.parse_args(args[1:])

    if ( not options.clustername ):
        print "Le nom du cluster de travail n'est pas défini"
        print "ALERTE A FAIRE !"

    # Config file argument parser
    config = HPCStatsConfig(options)

    if (options.debug):
        # dump entire config file
        for section in config.sections():
            print section
            for option in config.options(section):
                print " ", option, "=", config.get(section, option)

    # Instantiate connexion to db
    db_section = "hpcstatsdb"
    dbhostname = config.get(db_section,"hostname")
    dbport = config.get(db_section,"port")
    dbname = config.get(db_section,"dbname")
    dbuser = config.get(db_section,"user")
    dbpass = config.get(db_section,"password")
    db = HPCStatsdb(dbhostname, dbport, dbname, dbuser, dbpass)
    db.bind()
    
    if (options.debug):
        print "db information %s %s %s %s %s" % db.infos()

    if (options.arch):
        if (options.debug):
            print "=> Updating architecture for cluster %s" % (options.clustername)
        arch_importer = ArchitectureImporter().factory(db, config, options.clustername)
        (cluster, nodes) = arch_importer.get_cluster_nodes()
        # insert or update cluster
        if cluster.exists_in_db(db):
            if (options.debug):
                print "updating cluster", cluster
            cluster.update(db)
        else:
            if (options.debug):
                print "creating cluster", cluster
            cluster.save(db)

        # insert or update nodes
        for node in nodes:
            if node.exists_in_db(db):
                if (options.debug):
                    print "updating node", node
                node.update(db)
            else:
                if (options.debug):
                    print "creating node", node
                node.save(db)
        db.commit()

    if (options.users):
        if (options.debug):
            print "=> Mise à jour des utilisateurs pour %s" % (options.clustername)
        user_importer = UserImporter().factory(db, config, options.clustername)
        users = user_importer.get_all_users()
        for user in users:
            if user.exists_in_db(db):
                if (options.debug):
                    print "updating user", user
                user.update(db)
            else:
                if (options.debug):
                    print "creating user", user
                user.save(db)
        
        if (options.debug):
            print "=> Trying to find missing users for cluster %s" % (options.clustername)
        cluster = Cluster(options.clustername)
        uids = cluster.get_unknown_users(db)
        for unknown_uid in uids:
            user = user_importer.find_with_uid(unknown_uid)
            if user:
                if user.exists_in_db(db):
                    if (options.debug):
                        print "updating user", user
                    user.update(db)
                else:
                    if (options.debug):
                        print "creating user", user
                    user.save(db)
            else:
                print "WARNING: unknown user with uid %d" % (unknown_uid) 

        db.commit()

    if (options.jobs):
        job_importer = JobImporter().factory(db, config, options.clustername)
        # The last updated job in hpcstatsdb for this cluster
        last_updated_id = job_importer.get_last_job_id()
        # The unfinished jobs in hpcstatsdb for this cluster
        ids = job_importer.get_unfinished_job_id()

        jobs_to_update = job_importer.get_job_information_from_dbid_job_list(ids)
        new_jobs = job_importer.get_job_for_id_above(last_updated_id)
        index = 0
        for job in jobs_to_update:
            index = index + 1
            if not index % 10 and options.debug:
                print "update job push %d" % index
            job.update(db)
        for job in new_jobs:
            index = index + 1
            if not index % 100000 and options.debug:
                print "create job push %d" % index
            job.save(db)
        db.commit()
        
    db.unbind()

