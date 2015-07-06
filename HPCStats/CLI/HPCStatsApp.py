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

"""This module contains the HPCStatsApp class."""

import logging
logger = logging.getLogger(__name__)
from HPCStats.DB.HPCStatsDB import HPCStatsDB

class HPCStatsApp(object):

    """Abstract HPCStats application class, parent of all real application
       classes (Importer, Reporter).
    """

    def __init__(self, conf, cluster_name):

        self.conf = conf
        self.cluster_name = cluster_name
        self.cluster = None # Cluster object created later in apps run()

    def new_db(self):
        """Returns a new HPCStatsDB object."""

        # Instantiate connexion to db
        db = HPCStatsDB(self.conf)
        db.bind()
        return db

    def run_check(self):
        """Pre-run checks"""

        # dump configuration in debug mode
        for section in self.conf.sections():
            logger.debug("conf: %s", section)
            for option in self.conf.options(section):
                logger.debug("conf:  %s=%s",
                             option,
                             self.conf.get(section, option))

        if self.cluster_name != 'all':
            # check presence of cluster in configuration
            self.conf.check_cluster()

    def run(self):
        """Run method that should be implemented by all real App classes.
           For this abstract class, it raises NotImplementedError.
        """
        raise NotImplementedError
