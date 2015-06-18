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

"""This module contains the BusinessCodeImporterCSV class."""

import os
import csv
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Importer.BusinessCodes.BusinessCodeImporter import BusinessCodeImporter
from HPCStats.Model.Business import Business

class BusinessCodeImporterCSV(BusinessCodeImporter):

    """This class imports BusinessCodes from a CSV flat file."""

    def __init__(self, app, db, config):

        super(BusinessCodeImporterCSV, self).__init__(app, db, config)

        business_section = "business"
        self._business_file = config.get(business_section, "file")

    def check(self):
        """Check if CSV file exists and is a proper flat file."""

        if not os.path.isfile(self._business_file):
            raise HPCStatsSourceError( \
                    "business CSV file %s does not exist" \
                      % (self._business_file))

    def load(self):
        """Load BusinessCodes from CSV files in businesses attribute. Raise
           HPCStatsSourceError if error in encountered.
        """

        self.businesses = []

        self.check()

        with open(self._business_file, 'r') as csvfile:

            file_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in file_reader:
                if len(row) != 2:
                    raise HPCStatsSourceError( \
                            "business line format in CSV is invalid")
                code = row[0].strip()
                description = row[1].strip()
                if len(code) == 0:
                    raise HPCStatsSourceError( \
                            "business code in CSV is empty")
                if len(description) == 0:
                    description = None
                business = Business(code, description)
                self.businesses.append(business)

    def update(self):
        """Create or update BusinessCodes in database."""

        for business in self.businesses:
            if not business.existing(self.db):
                business.save(self.db)
            else:
                business.update(self.db)
