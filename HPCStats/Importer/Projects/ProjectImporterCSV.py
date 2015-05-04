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

"""
   This module import projects from CSV file. The CSV file must be formatted
   like this:

   <project_code>;<project_description>; \
     [<domain_id>] <domain_description>; \
     [<sector_id>] <sector_description>

   The project_code is a mandatory string
   The project_description is an optional string
   The domain_id is an optional string
   The domain_description is an optional string
   The sector_id is an optional string
   The sector_description is an optional string

   A domain has both an ID and a description.

   However, a sector could have an ID but not description. The reverse is not
   true: there could not be a sector w/ a description w/o ID.

   A project could have a domain and no sector. But the reverse is not true:
   there could not be project w/ a sector and w/o domain.
"""

from HPCStats.Importer.Projects.ProjectImporter import ProjectImporter
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Sector import Sector
from HPCStats.Model.Project import Project
from HPCStats.Model.ContextAccount import ContextAccount
import ConfigParser
import os
import logging
import csv
import psycopg2
import codecs
import re

class ProjectImporterCSV(ProjectImporter):
    """Main class of this module."""

    def __init__(self, app, db, config, cluster):

        super(ProjectImporter, self).__init__(app, db, config, cluster)

        projects_section = self.cluster.name + "/projects"
        self.csv_file = config.get(projects_section, "file")

        self.domains = None
        self.sectors = None
        self.projects = None

    def load(self):
        """Open CSV file and load project out of it.
           Raises Exceptions if error is found in the file.
           Returns the list of Projects with their Domains and Sectors.
        """

        if not os.path.isfile(self.csv_file):
            raise RuntimeError("CSV file %s does not exist" % (self.csv_file))

        p_file = open(self.csv_file, 'r')
        # define projects delimiters in csv file for domains and sectors values
        delimiters = '\[|]'

        self.domains = []
        self.sectors = []
        self.projects = []

        with p_file as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in file_reader:
                 # Delete BOM
                 if '\xef\xbb\xbf' in row [0]:
                     row[0] = row[0].replace('\xef\xbb\xbf','')
                 # update domains table with third column of the file, only if
                 # sector exist in 4th column
                 if row[2]:
                     id_domain = re.split(delimiters,row[2])[1]
                     description_domain = re.split(delimiters,row[2])[2]
                     domain = Domain(id = id_domain,
                                     description = description_domain)
                     self.domains.append(domain)
                 else:
                     id_domain = None

                 # update sector table with forth column of the file
                 if id_domain:
                     if row[3] and row[3]!='[]':
                         id_sector = int(re.sub('[^0-9]', '',
                                                re.split(delimiters,row[3])[1]))
                         description_sector = re.split(delimiters,row[3])[2]
                     if not row[3] or row[3]=='[]':
                         id_sector = 0
                         description_sector = "default value for domain " \
                                              + domain.get_id()
                     sector = Sector(id = id_sector,
                                     domain = id_domain,
                                     description = description_sector)
                     self.sectors.append(sector)
                 else:
                     id_sector = None

                 # update Project table with first and seconds columns of the
                 # file because of constrains of database, it is impossible to
                 # add project with domain reference and no sector reference.
                 # Need both or any.in case of domain reference exist but sector
                 # referance doesn't exist, None value is set for both (see
                 # first if condition).
                 if row[0]:
                     project = Project(sector = id_sector,
                                       domain = id_domain,
                                       description = row[1],
                                       pareo = row[0])
                     self.projects.append(project)
        p_file.close()
        return projects

    def delete(self):
        """Delete all projects, sectors, and domains from database and remove
           the contexts linked to these projects.
        """
        logging.debug("Delete all projects entries in db")
        delete_contexts_with_pareo(self.db)
        delete_projects(self.db)
        delete_sectors(self.db)
        delete_domains(self.db)
        self.db.commit()

    def update(self):
        """Update loaded project (with associated sectors and domains) in
           database.
        """

        self.delete_projects()

        # savepoint is used to considere exceptions and commit in database only at the end.
        db.cur.execute("SAVEPOINT my_savepoint;")
        for domain in domains:
            try:
                 if not domain.already_exist(self.db):
                     domain.save(self.db)
                     if not domain.get_description():
                         logging.debug("add domain : %s, without description", \
                                        domain.get_id())
                     else:
                         logging.debug("add domain : %s, with description : %s", \
                                        domain.get_id(), \
                                        domain.get_description())
                     db.cur.execute("SAVEPOINT my_savepoint;")
            except psycopg2.DataError:
                logging.error("impossible to add DOMAIN entry in database : (%s), du to encoding error", domain.get_description())
                db.cur.execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                pass
        for sector in sectors:
            try:
                if not sector.already_exist(self.db):
                    sector.save(self.db)
                    if not sector.get_description():
                        logging.debug("add sector : %s, from domain : %s, without description", \
                                       sector.get_id(),\
                                       sector.get_domain())
                    else:
                        logging.debug("add sector : %s, from domain : %s, with description : %s", \
                                       sector.get_id(), \
                                       sector.get_domain(), \
                                       sector.get_description())
                    db.cur.execute("SAVEPOINT my_savepoint;")
            except psycopg2.DataError:
                logging.error("impossible to add SECTOR entry in database : (%s) du to encoding error", sector.get_description())
                db.cur.execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                pass
            except psycopg2.IntegrityError:
                logging.error("impossible to add SECTOR entry in database : (%s), du to relations error", sector.get_description())
                db.cur.execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                pass
        for project in projects:
            try:
                if not project.already_exist(self.db):
                    project.save(self.db)
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
                    db.cur.execute("SAVEPOINT my_savepoint;")
            except psycopg2.DataError:
                logging.error("impossible to add PAREO entry in database : (%s - %s), du to encoding error", project.get_pareo(), project.get_description())
                db.cur.execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                pass
            except psycopg2.IntegrityError:
                logging.error("impossible to add PAREO entry in database : (%s - %s), du to relations error", project.get_pareo(), projet.get_description())
                db.cur.execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                pass
        self.db.commit()
