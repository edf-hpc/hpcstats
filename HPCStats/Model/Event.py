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
Schema of the ``Event`` table in HPCStats database:

.. code-block:: sql

    Event(
      event_id     SERIAL,
      event_type   character varying(30) NOT NULL,
      event_reason character varying(30),
      event_nbCpu  integer NOT NULL,
      event_start  timestamp NOT NULL,
      event_end    timestamp NOT NULL,
      node_id      integer NOT NULL,
      cluster_id   integer NOT NULL,
      CONSTRAINT Event_pkey PRIMARY KEY (event_id, node_id, cluster_id),
      CONSTRAINT Event_unique UNIQUE (node_id, cluster_id, event_start)
    )

"""

import logging
logger = logging.getLogger(__name__)
from HPCStats.Exceptions import HPCStatsRuntimeError, HPCStatsDBIntegrityError

class Event(object):

    """Model class for the Event table."""

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

        return self.node == other.node and \
               self.nb_cpu == other.nb_cpu and \
               self.start_datetime == other.start_datetime and \
               self.end_datetime == other.end_datetime and \
               self.event_type == other.event_type and \
               self.reason == other.reason

    def find(self, db):
        """Search the Event in the database based on the node, the cluster,
           the start and the end datetime. If exactly one event matches in
           database, set event_id attribute properly and returns its value.
           If more than one event matches, raises HPCStatsDBIntegrityError.
           If no event is found, returns None.
        """

        req = """
                SELECT Event.event_id
                  FROM Event
                 WHERE Event.node_id = %s
                   AND Event.cluster_id = %s
                   AND Event.event_start = %s
              """
        params = ( self.node.node_id,
                   self.cluster.cluster_id,
                   self.start_datetime )
        db.execute(req, params)
        nb_events = db.cur.rowcount
        if nb_events == 0:
            logger.debug("event %s not found in DB", str(self))
            return None
        elif nb_events > 1:
            raise HPCStatsDBIntegrityError(
                    "several event_id found for event %s" \
                      % (str(self)))
        else:
            self.event_id = db.cur.fetchone()[0]
            logger.debug("event %s found in DB with id %d",
                         str(self),
                         self.event_id )
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

        req = """
                INSERT INTO Event (
                              node_id,
                              cluster_id,
                              event_type,
                              event_reason,
                              event_nbCpu,
                              event_start,
                              event_end )
                VALUES ( %s, %s, %s, %s, %s, %s, %s)
                RETURNING event_id
              """
        params = ( self.node.node_id,
                   self.cluster.cluster_id,
                   self.event_type,
                   self.reason,
                   self.nb_cpu,
                   self.start_datetime,
                   self.end_datetime )
 
        #print db.cur.mogrify(req, params)
        db.execute(req, params)
        self.event_id = db.cur.fetchone()[0]
    
    def update(self, db):
        """Update the Event in DB. The event_id attribute must be set for the
           Event, either by passing this id to __init__() or by calling
           Event.find() method previously. If event_id attribute is not set, it
           raises HPCStatsRuntimeError.
        """

        if self.event_id is None:
            raise HPCStatsRuntimeError(
                    "could not update event %s since not found in database" \
                      % (str(self)))

        req = """
                UPDATE Event
                   SET event_end = %s,
                       event_start = %s,
                       event_type = %s,
                       event_reason = %s,
                       event_nbCpu = %s
                 WHERE event_id = %s
                   AND node_id = %s
                   AND cluster_id = %s
              """
        params = ( self.end_datetime,
                   self.start_datetime,
                   self.event_type,
                   self.reason,
                   self.nb_cpu,
                   self.event_id,
                   self.node.node_id,
                   self.cluster.cluster_id )
 
        #print db.cur.mogrify(req, params)
        db.execute(req, params)

    def merge_event(self, event):
        """Set Event end datetime equals to event in parameter end datetime.
        """

        self.end_datetime = event.end_datetime

def get_datetime_end_last_event(db, cluster):
    """Returns the end datetime of the last event on the cluster in DB. Returns
       None if no event found.
    """

    req = """
            SELECT MAX(event_end) AS last
              FROM Event
             WHERE cluster_id = %s
          """
    params = ( cluster.cluster_id, )
    db.execute(req, params)
    if db.cur.rowcount == 0:
        return None
    db_row = db.cur.fetchone()
    return db_row[0]

def get_datetime_start_oldest_unfinished_event(db, cluster):
    """Returns the start datetime of the oldest event on the cluster in DB.
       Returns None if no unfinished event found.
    """

    req = """
            SELECT MIN(event_start)
              FROM Event
             WHERE cluster_id = %s
               AND event_end IS NULL
              """
    params = ( cluster.cluster_id, )
    db.execute(req, params)
    if db.cur.rowcount == 0:
        return None
    db_row = db.cur.fetchone()
    return db_row[0]

def get_unfinished_events(db, cluster):
    """Get the list of unfinished Events on the cluster out of DB. Returns None
       if no unfinished event found.
    """
    req = """
            SELECT event_id,
                   node_name,
                   event_type,
                   event_reason,
                   event_nbCpu,
                   event_start
             FROM Events
             WHERE cluster_id = %s
               AND event_end IS NULL
          """
    params = ( cluster.cluster_id, )
    db.execute(req, params)

    events = []
    while (1):
        db_row = db.cur.fetchone()
        if db_row == None:
            break
        event = Event( event_id = db_row[0],
                       node = db_row[1],
                       cluster = cluster.name,
                       event_type = db_row[2],
                       reason = db_row[3],
                       nb_cpu = db_row[4],
                       start_datetime = db_row[5],
                       end_datetime = None )
        events.append(event)

    if len(events) == 0:
        return None

    return events
