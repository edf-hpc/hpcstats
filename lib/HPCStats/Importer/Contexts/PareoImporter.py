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

from HPCStats.Model.Domain import Domain, delete_domains
from HPCStats.Model.Sector import Sector, delete_sectors
from HPCStats.Model.Project import Project, delete_projects
from HPCStats.Model.Context import *
import ConfigParser
import os
import logging
import csv
import psycopg2
import codecs
import re

class PareoImporter(object):

    def __init__(self, db, config, cluster_name):

        self._db = db
        self._cluster_name = cluster_name

        pareo_section = self._cluster_name + "/pareo"
        self._pareo_file = config.get(pareo_section, "file")

        if not os.path.isfile(self._pareo_file):
            logging.error("pareo file %s does not exist", self._pareo_file)
            raise RuntimeError

        # delete all entries in domains and sectors tables and 
        # its dependances in contexts and projects table
        logging.debug("Delete all pareo entries in db")
        delete_contexts_with_pareo(self._db)
        delete_projects(self._db)
        delete_sectors(self._db)
        delete_domains(self._db)
        self._db.commit()

        p_file = open(self._pareo_file, 'r')
        # savepoint is used to considere exceptions and commit in database only at the end.
        db.get_cur().execute("SAVEPOINT my_savepoint;")
        # define pareo delimiters in csv file for domains and sectors values
        delimiters = '\[|]'
        with p_file as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in file_reader:
                 # Delete BOM
                 if '\xef\xbb\xbf' in row [0]:
                     row[0] = row[0].replace('\xef\xbb\xbf','')
                 # update domains table with third column of the file, only if sector exist in forth column
                 if row[2]:
                     id_domain = re.split(delimiters,row[2])[1]
                     description_domain = re.split(delimiters,row[2])[2]
                     domain = Domain(id = id_domain,
                                     description = description_domain)
                     try:
                         if not domain.already_exist(self._db):
                             domain.save(self._db)
                             if not domain.get_description():
                                 logging.debug("add domain : %s, without description", \
                                                domain.get_id())
                             else:
                                 logging.debug("add domain : %s, with description : %s", \
                                                domain.get_id(), \
                                                domain.get_description())
                             db.get_cur().execute("SAVEPOINT my_savepoint;")
                     except psycopg2.DataError:
                         logging.error("impossible to add DOMAIN entry in database : (%s), du to encoding error", row[2])
                         db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                         pass
                 else:
                     id_domain = None

                 # update sector table with forth column of the file
                 if id_domain:
                     if row[3] and row[3]!='[]':
                         id_sector = int(re.sub('[^0-9]', '', re.split(delimiters,row[3])[1]))
                         description_sector = re.split(delimiters,row[3])[2]
                     if not row[3] or row[3]=='[]':
                         id_sector = 0
                         description_sector = "default value for domain " + domain.get_id()
                     sector = Sector(id = id_sector,
                                     domain = id_domain,
                                     description = description_sector)
                     try:
                         if not sector.already_exist(self._db):
                             sector.save(self._db)
                             if not sector.get_description():
                                 logging.debug("add sector : %s, from domain : %s, without description", \
                                                sector.get_id(),\
                                                sector.get_domain())
                             else:
                                 logging.debug("add sector : %s, from domain : %s, with description : %s", \
                                                sector.get_id(), \
                                                sector.get_domain(), \
                                                sector.get_description())
                             db.get_cur().execute("SAVEPOINT my_savepoint;")
                     except psycopg2.DataError:
                         logging.error("impossible to add SECTOR entry in database : (%s) du to encoding error", row[3])
                         db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                         pass
                     except psycopg2.IntegrityError:
                         logging.error("impossible to add SECTOR entry in database : (%s), du to relations error", row[3])
                         db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                         pass
                 else:
                     id_sector = None

                 # update Project table with first and seconds columns of the file
                 # because of constrains of database, it is impossible to add project with domain reference and no sector reference. Need both or any.
                 # in case of domain reference exist but sector referance doesn't exist, None value is set for both (see first if condition). 
                 if row[0]:
                     project = Project(sector = id_sector,
                                     domain = id_domain,
                                     description = row[1],
                                     pareo = row[0])
                     try:
                         if not project.already_exist(self._db):
                             project.save(self._db)
                             if not project.get_description():
                                 logging.debug("add project : %s, from domain : %s, without description", \
                                                project.get_pareo(), \
                                                project.get_domain())
                             else:
                                 logging.debug("add project : %s, from domain : %s, and sector : %s with description : %s", \
                                                project.get_pareo(), \
                                                project.get_domain(), \
                                                project.get_sector(), \
                                                project.get_description())
                             db.get_cur().execute("SAVEPOINT my_savepoint;")
                     except psycopg2.DataError:
                         logging.error("impossible to add PAREO entry in database : (%s - %s), du to encoding error", row[0], row[1])
                         db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                         pass
                     except psycopg2.IntegrityError:
                         logging.error("impossible to add PAREO entry in database : (%s - %s), du to relations error", row[0], row[1])
                         db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                         pass
        self._db.commit()
        p_file.close()
