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

"""This module contains the base class for all Projects importers."""

from HPCStats.Importer.Importer import Importer

class ProjectImporter(Importer):

    """This is the base class common to all HPCStats Projects importers.
       It defines a common set of attributes and generic methods.
    """

    def __init__(self, app, db, config):

        super(ProjectImporter, self).__init__(app, db, config, None)

        self.domains = None
        self.projects = None

    def find_project(self, search):
        """Search for a Project over the list of Projects loaded by importer
           in self.projects attribute. Returns None if not found.
        """

        for project in self.projects:
            if project == search:
                return project
        return None

    def find_domain(self, search):
        """Search for a Domain over the list of Domains loaded by importer
           in self.domains attribute. Returns None if not found.
        """

        for domain in self.domains:
            if domain == search:
                return domain
        return None
