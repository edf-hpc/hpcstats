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

"""This module contains the base class for all User importers."""

from HPCStats.Importer.Importer import Importer

class UserImporter(Importer):

    """This is the base class common to all HPCStats User importers.
       It defines a common set of attributes and generic methods.
    """

    def __init__(self, app, db, config, cluster):

        super(UserImporter, self).__init__(app, db, config, cluster)

        self.users = None
        self.accounts = None

    def find_user(self, search):
        """Search for a User over the list of Users loaded by importer
           in self.users attribute. Returns None if not found.
        """

        for user in self.users:
            if user == search:
                return user
        return None

    def find_account(self, search):
        """Search for an Account over the list of Accounts loaded by importer
           in self.accounts attribute. Returns None if not found.
        """

        for account in self.accounts:
            if account == search:
                return account
        return None
