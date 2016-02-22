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
import inspect

"""This module contains a class HPCStatsLogger subclass of logging.Logger
   which controls whether the warns from the importers should be logged as
   warning or debug level messages, upon error manager's ignored errors.

   Unfortunately, we could not use standard and classical logging.Filter for
   the purpose since the filter() method is simply a "yes or no" logging
   filter. There is no direct way to downgrade a warning to debug level easily.
"""

error_mgr = None

class HPCStatsLogger(logging.Logger):

    def init(self, name):

        super(HPCstatsLogger, self).__init__(name)

    def warn(self, error, *args, **kwargs):

        # Inspect the calling class name to add it in prefix. Unfortunately,
        # we cannot use classical logging formater %(name) or %(module) token
        # for this purpose because:
        # - The module is always this logger's module
        # - The name of the logger is always Importer since all importers
        #   sub-classes use their grand-parent class logger.
        stack = inspect.stack()
        calling_class = stack[1][0].f_locals["self"].__class__.__name__
        prefix = "%s: " % (calling_class)

        if error_mgr is not None:
            if error in error_mgr.ignored_errors:
                prefix += "(IGNORED) "
            prefix += "ERROR %s: " % (error.code)

        # args is a tuple and does not support assigment. So convert
        # temporarily to a list to modify it.
        xargs = list(args)
        xargs[0] = prefix + xargs[0]
        args = tuple(xargs)

        if error_mgr is not None and error in error_mgr.ignored_errors:
            self.debug(*args, **kwargs)
        else:
            self.warning(*args, **kwargs)

    @staticmethod
    def set_error_mgr(mgr):

        global error_mgr
        error_mgr = mgr
