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

"""This module contains the BusinessCodeImporterDumy class."""

from HPCStats.Importer.BusinessCodes.BusinessCodeImporter import BusinessCodeImporter

class BusinessCodeImporterDummy(BusinessCodeImporter):

    """This class is dummy, it does not import any BusinessCode at all. It
       could be used as sane default when no BusinessCode have to be imported.
    """

    def __init__(self, app, db, config):

        super(BusinessCodeImporterDummy, self).__init__(app, db, config)

    def load(self):
        """Dummy BusinessCodes load."""

        self.log.debug("BusinessCodeImporterDummy load")
        self.businesses = []

    def update(self):
        """Dummy BusinessCodes update."""

        self.log.debug("BusinessCodeImporterDummy update")
