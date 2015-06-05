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

import ConfigParser
import os
import logging
import csv
import psycopg2
import codecs
import re
import string
from HPCStats.Exceptions import *
from HPCStats.Importer.Contexts.ContextImporter import ContextImporter
from HPCStats.Model.ContextAccount import ContextAccount
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Sector import Sector
from HPCStats.Model.Project import Project
from HPCStats.Model.Business import Business
from HPCStats.Model.User import User
from HPCStats.Model.Account import Account

class ContextImporterCSV(ContextImporter):

    def __init__(self, app, db, config, cluster):

        super(ContextImporterCSV, self).__init__(app, db, config, cluster)

        section = self.cluster.name + "/context"
        self.ctx_fpath = config.get(section, "file")

        self.contexts = None # loaded contexts

    def load(self):
        """Load the ContextAccounts from a CSV file.
           The CSV file must be formatted like the following:

           <login>;<firstname>;<lastname>;<department>;<date>;<date>; \
           <projects_list>;<businesses_list>

           Columns numbers are:
           0       1           2          3            4      5      \
           6               7

           The project codes and business codes in the lists are separated by
           '|' character.

           The importer does not actually care about columns 1-5. They were
           present in original file so we have to deal with them.
        """

        self.contexts = []

        if not os.path.isfile(self.ctx_fpath):
            raise HPCStatsSourceError( \
                    "CSV context file %s does not exist" % (self.ctx_fpath))

        with open(self.ctx_fpath, 'r') as csvfile:

            csvreader = csv.reader(csvfile, delimiter=';')
            for row in csvreader:

                if len(row) != 8:
                    raise HPCStatsSourceError( \
                            "context line format in CSV is invalid")

                login = row[0]
                projects_s = row[6]
                businesses_s = row[7]

                if len(login) == 0:
                    raise HPCStatsSourceError( \
                            "login CSV is empty")

                if len(projects_s) == 0:
                    raise HPCStatsSourceError( \
                            "projects list in CSV is empty")

                if len(businesses_s) == 0:
                    raise HPCStatsSourceError( \
                            "business codes list in CSV is empty")

                projects = projects_s.split('|')
                businesses = businesses_s.split('|')

                searched_user = User(login, None, None, None)
                searched_account = Account(searched_user, self.cluster, None, None, None, None)
                account = self.app.users.find_account(searched_account)

                if account is None:
                    raise HPCStatsSourceError( \
                            "account for login %s on cluster %s not found " \
                            "in loaded accounts" \
                              % (login, self.cluster.name) )

                for project_code in projects:

                    if len(project_code) == 0:
                        raise HPCStatsSourceError( \
                                "empty project code in list %s from" \
                                  % (projects_s) )

                    searched_project = Project(None, project_code, None)
                    project = self.app.projects.find_project(searched_project)

                    if project is None:
                        raise HPCStatsSourceError( \
                                "project code %s not found in loaded " \
                                "projects" \
                                  % (project_code) )

                    for business_code in businesses:

                        if len(business_code) == 0:
                            raise HPCStatsSourceError( \
                                    "empty business code in list %s from CSV" \
                                      % (business_s) )

                        searched_business = Business(business_code, None)
                        business = self.app.business.find(searched_business)

                        if business is None:
                            raise HPCStatsSourceError( \
                                    "business code %s not found in loaded " \
                                    "business codes" \
                                      % (business_code) )

                        context = ContextAccount(account, business, project)
                        self.contexts.append(context)

    def update(self):
        """Update loaded ContextAccounts in DB."""

        for context in self.contexts:
            if not context.existing(self.db):
                context.save(self.db)
