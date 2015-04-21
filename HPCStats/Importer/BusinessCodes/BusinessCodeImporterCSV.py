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

from HPCStats.Importer.BusinessCodes.BusinessCodeImporter import BusinessCodesImporter
from HPCStats.Model.Business import Business, delete_business
from HPCStats.Model.Context import *
import ConfigParser
import os
import logging
import csv
import psycopg2
import codecs

class BusinessCodeImporterCSV(BusinessCodeImporter):

    def __init__(self, app, db, config, cluster):

        super(BusinessCodeImporterCSV, self).__init__(app, db, config, cluster)

        business_section = self.cluster + "/business"
        self._business_file = config.get(business_section, "file")

        if not os.path.isfile(self._business_file):
            logging.error("business file %s does not exist", self._business_file)
            raise RuntimeError

        #In first delete all entries in business table and his dependances 
        logging.debug("Delete all business entries in db")
        delete_contexts_with_business(self.db)
        delete_business(self.db)
        self.db.commit()

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
                    if not code.already_exist(self.db):
                        code.save(self.db)
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
        self.db.commit()