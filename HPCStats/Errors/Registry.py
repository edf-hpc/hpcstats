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

    E_T0001 = HPCStatsError('E_T0001', "Fake error 1 for testing purpose")
    E_T0002 = HPCStatsError('E_T0002', "Fake error 2 for testing purpose")

    def __init__(self):

        pass

    @classmethod
    def is_valid(cls, error_s):
        return error_s in [a for a in dir(cls)
                           if type(getattr(cls, a)) is HPCStatsError]

    @classmethod
    def to_error(cls, error_s):

        return getattr(cls, error_s)
