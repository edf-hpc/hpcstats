#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2016 EDF SA
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

from HPCStats.Errors.Error import HPCStatsError


class HPCStatsErrorsRegistry(object):

    """This class contains the full list of HPCStatsError that may occur when
       running the Importer application.

       When adding new errors in this registry, please mind to also update the
       table in doc/architecture.rst in the documentation.
    """

    # testing purpose errors
    E_T0001 = HPCStatsError('E_T0001', "Fake error 1 for testing purpose")
    E_T0002 = HPCStatsError('E_T0002', "Fake error 2 for testing purpose")

    # business codes importers errors
    E_B0001 = HPCStatsError('E_B0001', "Invalid wckey format in SlurmDBD")

    # projects importers errors
    E_P0001 = HPCStatsError('E_P0001', "Invalid wckey format in SlurmDBD")

    # jobs importers errors
    E_J0001 = HPCStatsError('E_J0001', "Job found with an unknown account")
    E_J0002 = HPCStatsError('E_J0002', "Invalid wckey format in SlurmDBD")
    E_J0003 = HPCStatsError('E_J0003', "Job found with an unknown project")
    E_J0004 = HPCStatsError('E_J0004', "Job found with an unknown business "
                                       "code")
    E_J0005 = HPCStatsError('E_J0005', "Unable to define job partition based "
                                       "on job nodes list")

    # users importers errors
    E_U0001 = HPCStatsError('E_U0001', "User is member of the users group in "
                                       "the LDAP directory but does not have "
                                       "user entry in this directory")
    E_U0002 = HPCStatsError('E_U0002', "Missing attribute in LDAP user entry")
    E_U0003 = HPCStatsError('E_U0003', "Unable to determine user department "
                                       "in LDAP directory")
    E_U0004 = HPCStatsError('E_U0004', "User found in SlurmDBD but not found "
                                       "in LDAP, probably due to user removed "
                                       "from LDAP directory")
    E_U0005 = HPCStatsError('E_U0005', "Deprecated configuration parameter")

    # events importers errors
    E_E0001 = HPCStatsError('E_E0001', "Event node is unknown in cluster "
                                       "architecture")

    def __init__(self):

        pass

    @classmethod
    def is_valid(cls, error_s):
        return error_s in [a for a in dir(cls)
                           if type(getattr(cls, a)) is HPCStatsError]

    @classmethod
    def to_error(cls, error_s):

        return getattr(cls, error_s)
