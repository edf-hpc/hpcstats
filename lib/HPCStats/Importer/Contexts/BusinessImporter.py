#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.Business import Business, delete_business
from HPCStats.Model.Context import *
import ConfigParser
import os
import logging
import csv
import psycopg2
import codecs

class BusinessImporter(object):

    def __init__(self, db, config, cluster_name):

        self._db = db
        self._cluster_name = cluster_name

        business_section = self._cluster_name + "/business"
        self._business_file = config.get(business_section, "file")

        if not os.path.isfile(self._business_file):
            logging.error("business file %s does not exist", self._business_file)
            raise RuntimeError

        #In first delete all entries in business table and his dependances 
        logging.debug("Delete all business entries in db")
        delete_contexts_with_business(self._db)
        delete_business(self._db)
        self._db.commit()

        b_file = open(self._business_file, 'r')
        # savepoint is used to considere exceptions and commit only at the end
        db.get_cur().execute("SAVEPOINT my_savepoint;")
        with b_file as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in file_reader:
                # Delete BOM
                if '\xef\xbb\xbf' in row [0]:
                    row[0] = row[0].replace('\xef\xbb\xbf','')
                code = Business( key = row[0],
                                 description = row[1])
                try:
                    if not code.already_exist(self._db):
                        code.save(self._db)
                        if not code.get_description():
                            logging.debug("add new business entry with key : %s, without description", code.get_key())
                        else:
                            logging.debug("add new business entry with key : %s, and description : %s", \
                                           code.get_key(), \
                                           code.get_description())
                        db.get_cur().execute("SAVEPOINT my_savepoint;")
                    else :
                        logging.debug("code %s not added, already exist", code.get_key())
                except psycopg2.DataError:
                    logging.error("impossible to add BUSINESS entry in database : (%s) du to encoding error", row)
                    db.get_cur().execute("ROLLBACK TO SAVEPOINT my_savepoint;")
                    pass
        self._db.commit()
