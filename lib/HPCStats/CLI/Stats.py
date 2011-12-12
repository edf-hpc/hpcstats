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

DEBUG=1

def main(args=sys.argv):

    # Command line argument parser
    usage = "%prog [options] command"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args(args[1:])

    # Config file argument parser
    config = HPCStatsConfig(options)

    if DEBUG:
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
    
    if DEBUG:
        print "db information %s %s %s %s %s" % db.infos()


    job_importer = JobImporter(db, config, "ivanoe")
    
    #if (# JOB)
    # Should define what is the last complete job inserted for this 
    # Should retrieve how many jobs have to be forwaded/updated from log to db and the job list
    # Should split it in multiple job list
    # Iterate over the job list
    # Populate the DB

    #if (# USER)
        # TO BE DEFINED

    db.unbind()
