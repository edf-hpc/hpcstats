#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from optparse import OptionParser
import ConfigParser

from HPCStats.CLI.Config import Config
from HPCStats.DB.Jobs import DBJobs
from HPCStats.DB.Connexion import DBConnexion
from HPCStats.Parsers.Jobs.Torque import Torque
from HPCStats.Parsers.Jobs.Slurm import Slurm

def main(args=sys.argv):

    parser = OptionParser()
    parser.add_option("-n", "--name", action="store", type="string", dest="clustername")
    parser.add_option("-j", "--jobs", action="store_true", dest="jobs")
    parser.add_option("-u", "--users", action="store_true", dest="users")
    (options, args) = parser.parse_args(args[1:])

    config = ConfigParser.ConfigParser()
    config.read("/home/sgorget/ccn-hpc-svn/supervision/v2/conf/hpcstats.conf")
   
    # Pour le cluster choisi 

#    user = Users
    # Recupere la liste des utilisateurs
    # Complete la bd

    # Défini le dernier job inséré
    # Va chercher tous les jobs fini depuis le dernier jobs inséré
    # Ajoute les jobs suivant dans la DB


