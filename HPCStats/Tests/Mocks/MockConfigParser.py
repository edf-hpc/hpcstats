#!/usr/bin/env python
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

import mock
from ConfigParser import NoSectionError, NoOptionError

class MockConfigParser():

    def __init__(self):
        self.conf = None

    def read(self, filename):
        pass

    def get(self, section, option):
        if section not in self.conf.keys():
            raise NoSectionError(section)
        if option not in self.conf[section].keys():
            raise NoOptionError(section, option)
        return self.conf[section][option]

    def getint(self, section, option):
        value = self.get(section, option)
        if type(value) is not int:
            raise ValueError( \
              "invalid literal for int() with base 10: '%s'" \
                % (value))
        return value

    def getboolean(self, section, option):
        value = self.get(section, option)
        if type(value) is not bool:
            raise ValueError("invalid boolean: '%s'" % (value))
        return value

    def sections(self):

        return self.conf.keys()

    def options(self, section):

        return self.conf[section].keys()
