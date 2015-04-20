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

class Node:
    def __init__(self, name = "", cluster = "", partition = "", cpu = 0, memory = 0, model = "", flops = 0):

        self._name = name
        self._cluster = cluster
        self._partition = partition
        self._cpu = cpu
        self._memory = memory
        self._model = model
        self._flops = flops

    def __str__(self):
        return "%s/%s/%s [%s]: cpu:%d Gflops:%.2f memory:%dGB" % \
                   ( self._cluster,
                     self._partition,
                     self._name,
                     self._model,
                     self._cpu,
                     self._flops / float(1000**3),
                     self._memory / 1024**3 )

    def exists_in_db(self, db):
        cur = db.get_cur()
        cur.execute("SELECT name FROM nodes WHERE name = %s AND cluster = %s;",
                     (self._name,
                      self._cluster) )
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False
        else:
           raise UserWarning, ("incorrect number of results (%d) for node \
                                %s on cluster %s" % \
                                ( nb_rows,
                                  self._name,
                                  self._cluster ) )

    def save(self, db):
        req = """
            INSERT INTO nodes (
                            name,
                            cluster,
                            partition,
                            cpu,
                            memory,
                            model,
                            flops )
            VALUES ( %s, %s, %s, %s, %s, %s, %s); """
        datas = (
            self._name,
            self._cluster,
            self._partition,
            self._cpu,
            self._memory,
            self._model,
            self._flops )
 
        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE nodes SET
                       partition = %s,
                       cpu = %s,
                       memory = %s,
                       model = %s,
                       flops = %s
            WHERE name = %s
              AND cluster = %s; """
        datas = (
            self._partition,
            self._cpu,
            self._memory,
            self._model,
            self._flops,
            self._name,
            self._cluster )

        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)
