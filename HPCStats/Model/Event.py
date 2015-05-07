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

"""
Model class for the Event table:

Event(
  event_id     SERIAL,
  event_type   character varying(30) NOT NULL,
  event_reason character varying(30),
  event_nbCpu  integer NOT NULL,
  event_start  timestamp NOT NULL,
  event_end    timestamp NOT NULL,
  node_name    character varying(30) NOT NULL,
  cluster_name character varying(30) NOT NULL,
  CONSTRAINT Event_pkey PRIMARY KEY (event_id, node_name, cluster_name)
  CONSTRAINT FK_Event_node_name FOREIGN KEY (node_name, cluster_name)
    REFERENCES Node(node_name, cluster_name);
)

"""

import logging
from HPCStats.Exceptions import HPCStatsRuntimeError, HPCStatsDBIntegrityError

class Event(object):

    def __init__(self, cluster, node,
                 nb_cpu,
                 start_datetime,
                 end_datetime,
                 event_type,
                 reason,
                 event_id=None):

        self.event_id = event_id
        self.cluster = cluster
        self.node = node
        self.nb_cpu = nb_cpu
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.event_type = event_type
        self.reason = reason

    def __str__(self):
        return "event on node %s[%s]/%d (%s) : %s → %s" % \
                   ( self.node,
                     self.cluster,
                     self.nb_cpu,
                     self.event_type,
                     self.start_datetime,
                     self.end_datetime )

    def __eq__(self, other):
        return self.node_name == other.node_name and \
               self.nb_cpu == other.nb_cpu and \
               self.start_datetime == other.start_datetime and \
               self.end_datetime == other.end_datetime and \
               self.event_type == other.event_type and \
               self.reason == other.reason

    def find(self, db):
        """Search the Event in the database based on the node name, the cluster
           name and the start datetime. If exactly one event matches in
           database, set event_id attribute properly and returns its value.
           If more than one event matches, raises HPCStatsDBIntegrityError.
           If no event is found, returns None.
        """

        cur = db.cur
        req = """
                SELECT Event.event_id
                  FROM Event
                 WHERE Event.node_name = %s
                   AND Event.cluster_name = %s
                   AND Event.event_start = %s
              """
        params = ( self.node,
                   self.cluster,
                   self.start_datetime,
                   self.end_datetime )
        cur.execute(req, params)
        nb_events = cur.rowcount
        if nb_events == 0:
            logging.debug("event %s not found in DB" % (str(self)))
            return None
        elif nb_events > 1:
            raise HPCStatsDBIntegrityError(
                    "several event_id found for event %s" \
                      % (str(self)))
        else:
            self.event_id = cur.fetchone()[0]
            logging.debug("event %s found in DB with id %d" \
                            % (str(self),
                               self.event_id))
            return self.event_id

    def save(self, db):
        """Insert Event in database. You must make sure that the Event does not
           already exist in database yet (typically using Event.find() method
           else there is a risk of future integrity errors because of
           duplicated events. If event_id attribute is set, it raises
           HPCStatsRuntimeError.
        """

        if self.event_id is not None:
            raise HPCStatsRuntimeError(
                    "could not insert event %s since already existing in "\
                    "database" \
                      % (str(self)))

	cur = db.cur
        req = """
                INSERT INTO Event (
                              node_name,
                              cluster_name,
                              event_type,
                              event_reason,
                              event_nbCpu,
                              event_start,
                              event_end )
                VALUES ( %s, %s, %s, %s, %s, %s, %s)
              """
        params = ( self.node,
                   self.cluster,
                   self.nb_cpu,
                   self.event_type,
                   self.reason,
                   self.event_start,
                   self.event_end )
 
        cur = db.cur
        #print cur.mogrify(req, params)
        cur.execute(req, params)
    
    def update_end_datetime(self, db):
        """Update the end datetime of the Event. The event_id attribute must be
           set for the Event, either by passing this id to __init__() or by
           calling Event.find() method previously. If event_id attribute is
           not set, it raises HPCStatsRuntimeError.
        """

        if self.event_id is None:
            raise HPCStatsRuntimeError(
                    "could not update event %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Event
                   SET event_end = %s
                 WHERE event_id = %s
                   AND node_name = %s
                   AND cluster_name = %s
              """
        params = ( self.end_datetime,
                   self.event_id,
                   self.node,
                   self.cluster )
 
        cur = db.cur
        #print cur.mogrify(req, params)
        cur.execute(req, params)

    def update_reason(self, db):
        """Update the reason of the Event. The event_id attribute must be set
           for the Event, either by passing this id to __init__() or by calling
           Event.find() method previously. If event_id attribute is not set, it
           raises HPCStatsRuntimeError.
        """

        if self.event_id is None:
            raise HPCStatsRuntimeError(
                    "could not update event %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Event
                   SET event_reason = %s
                 WHERE event_id = %s
                   AND node_name = %s
                   AND cluster_name = %s
              """
        params = (
            self.reason,
            self.event_id,
            self.node,
            self.cluster )

        cur = db.cur
        #print cur.mogrify(req, params)
        cur.execute(req, params)

    def merge_event(self, event):
        """Set Event end datetime equals to event in parameter end datetime.
        """

        self.end_datetime = event.end_datetime
