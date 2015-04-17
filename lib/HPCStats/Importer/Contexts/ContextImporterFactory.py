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

import logging
from HPCStats.Importer.Contexts.BusinessImporter import BusinessImporter
from HPCStats.Importer.Contexts.PareoImporter import PareoImporter
from HPCStats.Importer.Contexts.ContextImporter import ContextImporter

class ContextImporterFactory(object):

    def __init__(self):
        pass

    def factory(self, db, config, cluster_name):
        if config.get(cluster_name, "context") == "business":
            business =  BusinessImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "pareo":
            pareo = PareoImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "context":
            context = ContextImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "business+pareo":
            business =  BusinessImporter(db, config, cluster_name)
            pareo = PareoImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "business+context":
            business =  BusinessImporter(db, config, cluster_name)
            context = ContextImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "pareo+context":
            pareo = PareoImporter(db, config, cluster_name)
            context = ContextImporter(db, config, cluster_name)
        elif config.get(cluster_name, "context") == "business+pareo+context":
            business =  BusinessImporter(db, config, cluster_name)
            pareo = PareoImporter(db, config, cluster_name)
            context = ContextImporter(db, config, cluster_name)
        else:
            logging.critical("TO BE CODED")
        return None
