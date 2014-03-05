#!/usr/bin/python
# -*- coding: utf-8 -*-

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

class ContextImporter(object):

    def __init__(self, db, config, cluster_name):

        self._db = db
        self._cluster_name = cluster_name

        context_section = self._cluster_name + "/context"
        self._context_file = config.get(context_section, "file")

        if not os.path.isfile(self._context_file):
            logging.error("context file %s does not exist", self._context_file)
            raise RuntimeError

        # delete all contexts entries in databases
        logging.debug("Delete all context entries in db")
        delete_contexts(self._db)
        self._db.commit()

        p_file = open(self._context_file, 'r')
        # save point is used to considere exception and commit in database only at the end
        db.get_cur().execute("SAVEPOINT my_savepoint;")
        with p_file as csvfile:
            file_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in file_reader:
                 logging.debug("update projects and business codes for user : %s", row[0].lower())
                 # a new context is set in database for all projects attached AND for all business attached.
                 # new line is set with a project referance OR a business referance.
                 if row[6]:
                     for pareo in re.split('\|',row[6]):
                         project = Project()
                         try:
                             project.project_from_pareo(self._db, pareo)
                             context = Context(login = row[0].lower(),
                                               job = None,
                                               project = project.get_id(),
                                               business = None)
                             try:
                                 context.save(self._db)
                                 logging.debug("add context : %s", context)
                                 #self._db.commit()
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
                             business.business_from_key(self._db, code)
                             context = Context(login = row[0].lower(),
                                               job = None,
                                               project = None,
                                               business = business.get_id())
                             try:
                                 context.save(self._db)
                                 logging.debug("add context : %s", context)
                                 #self._db.commit()
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
        self._db.commit()
        p_file.close()
