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

from HPCStats.Importer.Importer import Importer

class FSUsageImporter(Importer):

    def __init__(self, app, db, config, cluster):

        super(FSUsageImporter, self).__init__(app, db, config, cluster)

    def get_last_home_usage_timestamp(self):
        last_usage_timestamp = 0
        req = """
            SELECT MAX(id_usage) AS last_usage
            FROM filesystem_usage, filesystem
            WHERE filesystem_usage.fs_id=filesystem.id
            AND filesystem.clustername = %s
            AND filesystem.type = %s
              ; """
        datas = (self.cluster.name,
                 self._fs_type,)
        cur = self.db.cur
        cur.execute(req, datas)
        results = cur.fetchall()
        for usage in results:
            if last_home_usage_timestamp < usage[0]:
                last_home_usage_timestamp = usage[0]
        return last_home_usage_timestamp
