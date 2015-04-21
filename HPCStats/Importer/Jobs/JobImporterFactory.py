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
from HPCStats.Importer.Jobs.JobImporterSlurm import JobImporterSlurm
from HPCStats.Importer.Jobs.JobImporterTorque import JobImporterTorque

class JobImporterFactory(object):

    def __init__(self):
        pass

    def factory(self, app, db, config, cluster_name):
        if config.get(cluster_name, "jobs") == "slurm": ## Slurm
            return JobImporterSlurm(app, db, config, cluster_name)
        elif config.get(cluster_name, "jobs") == "torque": ## Torque
            return JobImporterTorque(app, db, config, cluster_name)
        else:
            logging.critical("TO BE CODED")
            # Throw Exception
        return None