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
from HPCStats.CLI.OptionParser import OptionParser
from HPCStats.CLI.Config import HPCStatsConfig
from HPCStats.DB.DB import HPCStatsdb
from HPCStats.Importer.Jobs.JobImporter import JobImporter
from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm

def main(args=sys.argv):

    # Command line argument parser
    usage = "%prog [options] command"
    parser = OptionParser(usage)
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


    #job_importer = JobImporter(db, config, "ivanoe")
    job_importer = JobImporterSlurm(db, config, "ivanoe")
  
    if (options.jobs):
        # The last updated job in hpcstatsdb for this cluster
        last_updated_id = job_importer.get_last_job_id()
        # The unfinished jobs in hpcstatsdb for this cluster
        ids = job_importer.get_unfinished_job_id()
        # 
        jobs1 = job_importer.get_job_information_from_id_job_list(ids)
        jobs2 = job_importer.get_job_for_id_above(last_updated_id)
        for job in jobs1:
            job.save()
        for job in jobs2:
            job.save()
        
        # Découper la liste en sous liste et pour chacune de ces listes
            # Récupérer les informations sur les jobs concernés
            # Générer un objet pour chacun des jobs
            # Injecter les objets dans la base de donnée supervision

    if (options.users):
        print "=> Mise à jour des utilisateurs pour %s" % (options.clustername)

    db.unbind()
