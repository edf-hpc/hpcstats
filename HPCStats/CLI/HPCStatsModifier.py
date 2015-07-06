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

"""This module contains the HPCStatsModifier class."""

import logging
logger = logging.getLogger(__name__)

from HPCStats.Exceptions import HPCStatsRuntimeError
from HPCStats.CLI.HPCStatsApp import HPCStatsApp
from HPCStats.Model.Business import Business
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Project import Project

class HPCStatsModifier(HPCStatsApp):

    """HPCStats Modifier application is used to modify BusinessCodes, Projects
       and Domains data in HPCStats DB.
    """

    def __init__(self, conf, cluster_name, params):

        super(HPCStatsModifier, self).__init__(conf, cluster_name)

        self.params = params
        self.db = None

    def run(self):
        """Run HPCStats Updater application."""

        self.run_check()
        self.db = self.new_db()

        if self.params['business'] is not None:
            self.set_business_code_description(self.params['business'],
                                               self.params['set_description'])

        elif self.params['project'] is not None:
            if self.params['set_description'] is not None:
                self.set_project_description(self.params['project'],
                                             self.params['set_description'])
            elif self.params['set_domain'] is not None:
                self.set_project_domain(self.params['project'],
                                        self.params['set_domain'])

        elif self.params['new_domain'] is not None:
            self.create_domain(self.params['new_domain'],
                               self.params['domain_name'])

        self.db.commit()
        self.db.unbind()

    def set_business_code_description(self, business_code, description):
        """Modify in DB the description of the Business code given in
           parameter. It raises HPCStatsRuntimeError if the Business code
           is not found in DB.
        """

        business = Business(business_code, description)

        if not business.existing(self.db):
            raise HPCStatsRuntimeError( \
                    "unable to find business code %s in database" \
                      % (business_code))

        logger.info("updating business code %s with new description",
                    business_code)
        business.update(self.db)

    def set_project_description(self, project_code, description):
        """Modify in DB the description of the Project given in parameter. It
           raises HPCStatsRuntimeError if the Project is not found in DB.
        """

        project = Project(None, project_code, None)
        if not project.find(self.db):
            raise HPCStatsRuntimeError( \
                    "unable to find project %s in database" \
                      % (project_code))

        # Load the Project from DB to get its domain key
        project.load(self.db)

        project.description = description

        logger.info("updating project %s with new description",
                    project_code)
        project.update(self.db)

    def set_project_domain(self, project_code, domain_key):
        """Modify the Domain of the Project whose code is given in parameter.
           It raises HPCStatsRuntimeError if either the Project code or the
           Domain key are not found in DB.
        """

        domain = Domain(domain_key, None)
        if not domain.existing(self.db):
            raise HPCStatsRuntimeError( \
                    "unable to find domain %s in database" \
                      % (domain_key))

        project = Project(None, project_code, None)
        if not project.find(self.db):
            raise HPCStatsRuntimeError( \
                   "unable to find project %s in database" \
                     % (project_code))

        # Load the Project in DB to get its description
        project.load(self.db)

        project.domain = domain

        logger.info("updating project %s with new domain %s",
                    project_code, domain_key)
        project.update(self.db)

    def create_domain(self, domain_key, domain_name):
        """Creates the domain whose key and name are given in parameters. It
           raises HPCStatsRuntimeError if another Domain with the same key
           already exists in DB.
        """
        domain = Domain(domain_key, domain_name)
        if domain.existing(self.db):
            raise HPCStatsRuntimeError("domain %s already exists in database" % (domain_key))

        logger.info("creating domain %s in database", domain_key)
        domain.save(self.db)

    def cleanup(self):
        """Clean-up the application before exit."""
        pass
