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

class Filesystem_usage:
    def __init__(self, fs_id = "", timestamp = "", usage = ""):

        self._fs_id = fs_id
        self._timestamp = timestamp
        self._usage = usage

    def __str__(self):
        return "Usage timestamp [%s] for fs : %s, used at %s %" % \
                   ( self._timestamp,
                     self._fs_id,
                     self._usage )

    def update_usage(self, db, cluster, fs, fs_usage):
        for i in fs_usage:
            req = """
                INSERT INTO filesystem_usage (
                            fs_id,
                            timestamp,
                            usage,
			    inode)
                       VALUES (
                           (SELECT id FROM filesystem 
                            WHERE mount_point = %s and cluster = %s), %s, %s, %s ); """
            datas = (fs, cluster, i[0], i[1], i[2])
            #logging.info("Add fs %s with timestamp %s, and usage : %s", \
            #              fs, \
            #              i[0], \
            #              i[1])
            db.get_cur().execute(req, datas)
            #logging.info("req : %s", req)

