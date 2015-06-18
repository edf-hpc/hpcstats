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

"""This module contains the base class for all Architecture importers."""

from HPCStats.Importer.Importer import Importer

class ArchitectureImporter(Importer):

    """This is the base class common to all HPCStats Architecture importers.
       It defines a common set of attributes and generic methods.
    """

    def __init__(self, app, db, config, cluster_name):

        super(ArchitectureImporter, self).__init__(app, db, config, None)

        self.cluster_name = cluster_name

        self.cluster = None
        self.nodes = None

        # The partition attribute is a dict whose keys are nodelists and
        # values are lists of job partitions. Ex:
        #
        # {
        #   'compute[001-100]': [ 'prod', 'compute' ],
        #   'bigmem[01-10]'   : [ 'bigmem' ],
        # }
        self.partitions = None

    def find_node(self, search):
        """Search for a Node over the list of Nodes loaded by importer
           in self.nodes attribute. Returns None if not found.
        """

        for node in self.nodes:
            if node == search:
                return node
        return None
