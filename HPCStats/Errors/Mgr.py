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


import logging
logger = logging.getLogger(__name__)
from HPCStats.Errors.Registry import HPCStatsErrorsRegistry as Errors

class HPCStatsErrorMgr(object):

    def __init__(self, conf):

        ignored_errors_s = conf.get_default('constraints', 'ignored_errors', '')
        self.ignored_errors = set()
        for error_s in ignored_errors_s.split(','):
            error_s = error_s.strip()
            if len(error_s) and Errors.is_valid(error_s):
                error = Errors.to_error(error_s)
                if error not in self.ignored_errors:
                    logger.debug("adding error %s to set of ignored errors", error_s)
                    self.ignored_errors.add(error)
            else:
                logger.warning("error %s is not valid, skipping", error_s)
