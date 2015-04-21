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

from HPCStats.Importer.Contexts.ContextImporter import ContextsImporter
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Sector import Sector
from HPCStats.Model.Project import Project
from HPCStats.Model.Business import Business
from HPCStats.Model.Context import *
import ConfigParser
import os
import logging
import csv
import psycopg2
import codecs
import re
import string

class ContextImporterCSV(ContextImporter):

    def __init__(self, app, db, config, cluster):

        super(ContextImporterCSV, self).__init__(app, db, config, cluster)

        context_section = self.cluster + "/context"
        self._context_file = config.get(context_section, "file")

        if not os.path.isfile(self._context_file):
            logging.error("context file %s does not exist", self._context_file)
            raise RuntimeError

        # delete all contexts entries in databases for cluster
        logging.debug("Delete all context entries in db for cluster %s", self.cluster)
        delete_contexts(self.db, self.cluster)
        self.db.commit()

        p_file = open(self._context_file, 'r')
        # save point is used to considere exception and commit in database only at the end
        db.get_cur().execute("SAVEPOINT my_savepoint;")
        with p_file as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in file_reader:
                # Delete BOM
                 if '\xef\xbb\xbf' in row [0]:
                     row[0] = row[0].replace('\xef\xbb\xbf','')
                 logging.debug("update projects and business codes for user : %s", row[0].lower())
                 # a new context is set in database for all projects attached AND for all business attached.
                 # new line is set with a project referance OR a business referance.
                 if row[6]:
                     for pareo in re.split('\|',row[6]):
                         project = Project()
                         try:
                             project.project_from_pareo(self.db, pareo)
                             context = Context(login = row[0].lower(),
                                               job = None,
                                               project = project.get_id(),
                                               business = None,
                                               cluster = self.cluster)
                             try:
                                 context.save(self.db)
                                 logging.debug("add context : %s", context)
                                 #self.db.commit()
                                 db.get_cur().execute("SAVEPOINT my_savepoint;")
                             except psycopg2.DataError:
                                 logging.error("impossible to add CONTEXT entry in database : (%s), du to encoding error", row)
                                 db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                                 pass
                             except psycopg2.IntegrityError:
                                 logging.error("impossible to add CONTEXT entry in database : (%s), du to relations error", row)
                                 db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                                 pass
                         except:
                             logging.error("context rejected. Project %s does not exist", pareo)
                             db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                             pass
                 if row[7]:
                     for code in re.split('\|',row[7]):
                         business = Business()
                         try:
                             business.business_from_key(self.db, code)
                             context = Context(login = row[0].lower(),
                                               job = None,
                                               project = None,
                                               business = business.get_id(),
                                               cluster = self.cluster)
                             try:
                                 context.save(self.db)
                                 logging.debug("add context : %s", context)
                                 #self.db.commit()
                                 db.get_cur().execute("SAVEPOINT my_savepoint;")
                             except psycopg2.DataError:
                                 logging.error("impossible to add CONTEXT entry in database : (%s), du to encoding error", row)
                                 db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                                 pass
                             except psycopg2.IntegrityError:
                                 logging.error("impossible to add CONTEXT entry in database : (%s), du to relations error", row)
                                 db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                                 pass
                         except:
                             logging.error("context rejected. Business %s does not exist", code)
                             db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                             pass
                 if not row[6] and not row[7]:
                     logging.error("line : %s rejected - not code or project associate", row)
        self.db.commit()
        p_file.close()
