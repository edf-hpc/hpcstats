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
like this::

   <project_code>;<project_description>; \
[<domain_id>] <domain_description>; \
[<sector_id>] <sector_description>

Where:

* The ``project_code`` is a mandatory string
* The ``project_description`` is an optional string
* The ``domain_id`` is an optional string
* The ``domain_description`` is an optional string
* The ``sector_id`` is an optional string
* The ``sector_description`` is an optional string

A domain has both an ID and a description. However, a sector could have an ID
but not description. The reverse is not true: there could not be a sector w/ a
description w/o ID.

A project could have a domain and no sector. But the reverse is not true:
there could not be project w/ a sector and w/o domain.
"""

from HPCStats.Importer.Projects.ProjectImporter import ProjectImporter
from HPCStats.Model.Domain import Domain
from HPCStats.Model.Project import Project
from HPCStats.Exceptions import HPCStatsRuntimeError, HPCStatsSourceError
import os
import csv
import re

class ProjectImporterCSV(ProjectImporter):
    """Main class of this module."""

    def __init__(self, app, db, config):

        super(ProjectImporterCSV, self).__init__(app, db, config)

        projects_section = "projects"
        self.csv_file = config.get(projects_section, "file")

    def check(self):
        """Check if CSV file exists and is a proper flat file."""

        if not os.path.isfile(self.csv_file):
            raise HPCStatsRuntimeError("CSV file %s does not exist" \
                                       % (self.csv_file))

    def load(self):
        """Open CSV file and load project out of it.
           Raises Exceptions if error is found in the file.
           Returns the list of Projects with their Domains.
        """

        self.check()

        self.domains = []
        self.projects = []

        with open(self.csv_file, 'r') as csvfile:

            file_reader = csv.reader(csvfile, delimiter=';', quotechar='|')

            for row in file_reader:

                project_code = row[0]
                project_name = row[1]

                # domains
                domain_str = row[2]
                domain_m = re.match(r"\[(.*)\](.*)", domain_str)
                if domain_m:
                    domain_key = domain_m.group(1)
                    domain_name = domain_m.group(2)
                else:
                    raise HPCStatsSourceError( \
                            "Project CSV %s domain format is invalid" \
                              % (project_code))

                domain_key = domain_key.strip()
                domain_name = domain_name.strip()
                if len(domain_key) == 0:
                    raise HPCStatsSourceError( \
                            "Project CSV %s domain key is empty" \
                              % (project_code))
                if len(domain_name) == 0:
                    raise HPCStatsSourceError( \
                            "Project CSV %s domain name is empty" \
                              % (project_code))

                # Create the Domain and search for it among the already
                # existing ones. If not found, append to the list of Domains.
                new_domain = Domain(key=domain_key,
                                    name=domain_name)
                domain = self.find_domain(new_domain)
                if domain is None:
                    domain = new_domain
                    self.domains.append(domain)

                # Create the Project and search for it among the already
                # existing ones. If found, raise HPCStatsSourceError
                project = Project(domain=domain,
                                  code=project_code,
                                  description=project_name)
                # check for duplicate project and raise error if found
                if self.find_project(project):
                    raise HPCStatsSourceError( \
                              "duplicated project code %s in CSV file" \
                                  % (project_code))

                self.projects.append(project)

        return self.projects

    def update(self):
        """Update loaded project (with associated domains) in database.
        """

        for domain in self.domains:
            if domain.existing(self.db):
                domain.update(self.db)
            else:
                domain.save(self.db)
        for project in self.projects:
            if project.find(self.db):
                project.update(self.db)
            else:
                project.save(self.db)
