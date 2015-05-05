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
Set of Exceptions for HPCStats application.
"""

__all__ = [ "HPCStatsException",
            "HPCStatsRuntimeError",
            "HPCStatsDBIntegrityError",
            "HPCStatsSourceError",
            "HPCStatsArgumentException",
            "HPCStatsConfigurationException" ]

class HPCStatsException(Exception):

    """Base class for exceptions in HPCStats"""

    def __init__(self, msg):

        super(HPCStatsException, self).__init__(msg)
        self.msg = msg

    def __str__(self):

        return self.msg

class HPCStatsRuntimeError(HPCStatsException):

    """Class for runtime errors exceptions in HPCStats"""

    def __init__(self, msg):

        super(HPCStatsRuntimeError, self).__init__(msg)

class HPCStatsDBIntegrityError(HPCStatsException):

    """Class for DB intregrity errors exceptions in HPCStats"""

    def __init__(self, msg):

        super(HPCStatsDBIntegrityError, self).__init__(msg)

class HPCStatsSourceError(HPCStatsException):

    """Class for source errors exceptions in HPCStats"""

    def __init__(self, msg):

        super(HPCStatsSourceError, self).__init__(msg)

class HPCStatsArgumentException(HPCStatsException):

    """Class for argument parsing exceptions in HPCStats"""

    def __init__(self, msg):

        super(HPCStatsArgumentException, self).__init__(msg)

class HPCStatsConfigurationException(HPCStatsException):

    """Class for configuration file exceptions in HPCStats"""

    def __init__(self, msg):

        super(HPCStatsConfigurationException, self).__init__(msg)
