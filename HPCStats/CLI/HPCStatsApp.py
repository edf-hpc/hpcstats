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

import sys
import logging
from HPCStats.DB.HPCStatsDB import HPCStatsDB
from HPCStats.Exceptions import *

class HPCStatsApp(object):

    """Abstract HPCStats application class, parent of all real application
       classes (Importer, Reporter).
    """

    def __init__(self, conf, cluster_name):

        self.conf = conf
        self.cluster_name = cluster_name
        self.cluster = None # Cluster object created later in apps run()

        # dump configuration in debug mode
        for section in self.conf.sections():
            logging.debug("conf: %s", section)
            for option in self.conf.options(section):
                logging.debug("conf:  %s=%s",
                              option,
                              self.conf.get(section, option))

        if self.cluster_name != 'all':
            # check presence of cluster in configuration
            try:
                self.conf.check_cluster()
            except HPCStatsConfigurationException, err:
                logging.error("configuration error: %s", err)
                sys.exit(1)

    def new_db(self):
        """Returns a new HPCStatsDB object."""

        # Instantiate connexion to db
        db_section = "hpcstatsdb"
        dbhostname = self.conf.get(db_section,"hostname")
        dbport = self.conf.get(db_section,"port")
        dbname = self.conf.get(db_section,"dbname")
        dbuser = self.conf.get(db_section,"user")
        dbpass = self.conf.get(db_section,"password")
        db = HPCStatsDB(dbhostname, dbport, dbname, dbuser, dbpass)
        db.bind()
        logging.debug("db information %s %s %s %s %s" % db.infos())
        return db

    def run(self):

        raise NotImplemented
