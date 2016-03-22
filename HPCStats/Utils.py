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

"""Collection of utility functions widely used accross HPCStats."""

import re

def decypher(encoded):
    """Decypher the string in parameter."""

    result = []
    for coord_i in xrange(len(encoded)):
        coord_j = ord(encoded[coord_i])
        if coord_j >= 33 and coord_j <= 126:
            result.append(chr(33 + ((coord_j + 14) % 94)))
        else:
            result.append(encoded[coord_i])
    return ''.join(result)

def match_bg_nodelist(nodelist):
    """Returns the match object as returned by the match() method
       after the regext and the nodelist in parameter.
    """

    re_ns = r"(\S+)\[(\d+)x(\d+)\]"
    cp_ns = re.compile(re_ns)
    return cp_ns.match(nodelist)

def is_bg_nodelist(nodelist):
    """Returns True if the nodelist in parameter is a valid BG/Q nodelist
       as formatted by Slurm.
    """

    return match_bg_nodelist(nodelist) is not None

def compute_bg_nodelist(nodelist):
    """Returns the list of nodes in a BG/Q nodelist as formatted by Slurm.
       Ex: bgq[001x011] -> [ bgq001, bgq010, bgq011].
    """

    def is_over(idxs, idx_values):

        for i in range(len(idxs)):
            if idxs[i] < len(idx_values[i])-1:
                return False
        return True

    def increment_idxs(idxs, idx_values):

        for i in range(len(idxs)-1, -1, -1):
            if idxs[i] >= len(idx_values[i])-1:
                idxs[i] = 0
            elif idxs[i] < len(idx_values[i])-1:
                idxs[i] += 1
                break

    def compute_nodes_inter(pfx, start, end):

        idx_values = list()
        idxs = list()
        nodes = list()

        for i in range(len(start)):
           idx_values.append(list())
           idxs.append(0)
           idx_values[i] = range(int(start[i]), int(end[i])+1)

        while(True):

            new_node_name = pfx
            for i in range(len(idxs)):
                new_node_name += str(idx_values[i][idxs[i]])
            nodes.append(new_node_name)
            if is_over(idxs, idx_values):
                break
            increment_idxs(idxs, idx_values)

        return nodes

    match_ns = match_bg_nodelist(nodelist)

    if match_ns is not None:
        pfx = match_ns.group(1)
        start_inter = match_ns.group(2)
        end_inter = match_ns.group(3)
        nodes = compute_nodes_inter(pfx, start_inter, end_inter)
        return nodes

    return None

def extract_tres_cpu(tres_s):
    """Extract cpu_count from new generic Slurm TRES text field. TRES field is
       a string containing a comma-separated list of <id>=<value> pairs. CPU
       count has ID 1 according to this enum found in
       src/common/slurmdb_defs.h:

       typedef enum {
               TRES_CPU = 1,
               TRES_MEM,
               TRES_ENERGY,
               TRES_NODE,
       } tres_types_t;

       ex: 1=288,2=1160770,3=0,4=12
           -> cpu_count = 288


       Returns CPU count as an integer or -1 if unable to extract it. There is
       a special case for pending jobs that have an empty tres. In this case,
       returns 0. It will be updated at the next hpcstats run once resources
       will be allocated to the job.
    """

    if len(tres_s.strip()) == 0:
        return 0

    tres_list = tres_s.split(',')
    for tres in tres_list:
        (key, value) = tres.split('=')
        if int(key) == 1:
            return int(value)
    return -1
