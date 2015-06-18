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

"""This module contains the EventImporterSlurm class."""

import MySQLdb
import _mysql_exceptions
import logging
import time
from datetime import datetime
from HPCStats.Exceptions import HPCStatsSourceError
from HPCStats.Importer.Events.EventImporter import EventImporter
from HPCStats.Model.Event import Event, get_datetime_end_last_event, get_datetime_start_oldest_unfinished_event
from HPCStats.Model.Node import Node

class EventImporterSlurm(EventImporter):

    """This EventImporter imports Events from a cluster Slurm accounting
       database.
    """

    def __init__(self, app, db, config, cluster):

        super(EventImporterSlurm, self).__init__(app, db, config, cluster)

        section = self.cluster.name + "/slurm"

        self._dbhost = config.get(section,"host")
        self._dbport = int(config.get(section,"port"))
        self._dbname = config.get(section,"name")
        self._dbuser = config.get(section,"user")
        self._dbpass = config.get_default(section, "password", None)
        self.conn = None
        self.cur = None

    def connect_db(self):
        """Connect to cluster Slurm database and set conn/cur attribute
           accordingly. Raises HPCStatsSourceError in case of problem.
        """

        try:
            conn_params = {
               'host': self._dbhost,
               'user': self._dbuser,
               'db': self._dbname,
               'port': self._dbport,
            }
            if self._dbpass is not None:
                conn_params['passwd'] = self._dbpass

            self.conn = MySQLdb.connect(**conn_params)
            self.cur = self.conn.cursor()
        except _mysql_exceptions.OperationalError as error:
            raise HPCStatsSourceError( \
                    "connection to Slurm DBD MySQL failed: %s" % (error))

    def disconnect_db(self):
        """Disconnect from cluster Slurm database."""

        self.cur.close()
        self.conn.close()

    def check(self):
        """Check if cluster Slurm database is available for connection."""

        self.connect_db()
        self.disconnect_db()

    def load(self):
        """Load Events from Slurm DB and store them into self.events
           list attribute.
        """

        self.connect_db()

        # Define the datetime from which the search must be done in Slurm DB.
        # Variables here are float timestamps since epoch, not Python Datetime
        # objects.
        #
        # The datetime used for search is the start datetime of the oldest
        # unfinished event if it exists. Else it is the end datetime of the
        # last finished event. Else (no event in DB) it is epoch.
        #
        # Consider the following status in HPCstats DB, where:
        #  - e1 is the last finished event
        #  - e2 is the oldest unfinised event
        #
        #     t0   t1     t2
        # e1  +-----------+
        # e2       +
        #
        # -> Result: t1 because we have to search for e2 in source to check if
        #               it finally has a end datetime as of now.
        #
        #     t0   t1     t2
        # e1       +------+
        # e2  +
        #
        # -> Result: t0 because we have to search for e2 in source to check if
        #               it finally has a end datetime as of now.
        #
        #     t0   t1     t2
        # e1  +----+
        # e2              +
        #
        # -> Result: t2 because there is no reason to find in source a new
        #               event that would have started between t1 and t2.
        #
        #     t0   t1
        # e1  +----+
        # e2  (none)
        #
        # -> Result: t1
        #
        # e1  (none)
        # e2  (none)
        #
        # -> Result: epoch

        datetime_end_last_event = \
          get_datetime_end_last_event(self.db, self.cluster)
        datetime_start_oldest_unfinished_event = \
          get_datetime_start_oldest_unfinished_event(self.db, self.cluster)

        if datetime_start_oldest_unfinished_event:
            datetime_search = datetime_start_oldest_unfinished_event
        elif datetime_end_last_event:
            datetime_search = datetime_end_last_event
        else:
            default_datetime = datetime.fromtimestamp(0)
            datetime_search = time.mktime(default_datetime.timetuple())

        # get all events since datetime_search
        self.events = self.get_new_events(datetime_search)

    def get_new_events(self, start):
        """Get all new Events from Slurm DB since start datetime. Parameter
           start must be a float timestamp since epoch. Returns a list of
           Events. The list is empty if none found.
        """

        events = []

        req = """
                SELECT time_start,
                       time_end,
                       node_name,
                       cpu_count,
                       state,
                       reason
                 FROM %s_event_table
                WHERE node_name <> ''
                  AND time_start >= UNIX_TIMESTAMP(%%s)
                ORDER BY time_start
              """ % (self.cluster.name)
        params = ( start, )
        self.cur.execute(req, params)

        while (1):
            row = self.cur.fetchone()
            if row == None:
                break

            datetime_start = datetime.fromtimestamp(row[0])

            timestamp_end = row[1]
            if timestamp_end == 0:
                datetime_end = None
            else:
                datetime_end = datetime.fromtimestamp(timestamp_end)

            node_name = row[2]
            searched_node = Node(node_name, self.cluster,
                                 None, None, None, None)
            node = self.app.arch.find_node(searched_node)
            if node is None:
                raise HPCStatsSourceError( \
                        "event node %s not found in loaded nodes" \
                          % (node_name))
            nb_cpu = row[3]
            event_type = EventImporterSlurm.txt_slurm_event_type(row[4])
            reason = row[5]

            event = Event( node=node,
                           cluster=self.cluster,
                           nb_cpu=nb_cpu,
                           start_datetime=datetime_start,
                           end_datetime=datetime_end,
                           event_type=event_type,
                           reason=reason)
            events.append(event)

        return EventImporterSlurm.merge_successive_events(events)

    @staticmethod
    def merge_successive_events(events):
        """Merge successive Events in the list. For example, if the list
           contains 2 events on node A from X to Y and from Y to Z, this method
           will merge them into one event on node A from Y to Z. Ex:
           [ { node: N1, reason: R1, start: X, end Y },
             { node: N1, reason: R1, start: Y, end Z } ]
           -> [ { node: N1, reason: R1, start: X, end: Z } ]
        """

        event_index = 0
        nb_events = len(events)
        logging.debug("merge: nb_events: %d", nb_events)

        # iterate over the list of new events
        while event_index < nb_events - 1:

            event = events[event_index]
            logging.debug("merge: current event_index: %d", event_index)
            # find the next event in the list for the same node
            next_event_index = event_index + 1

            while next_event_index < nb_events:
                next_event = events[next_event_index]
                if next_event.node == event.node and \
                   next_event.start_datetime == event.end_datetime and \
                   next_event.event_type == event.event_type:
                    break
                else:
                    next_event_index += 1

            logging.debug("merge: computed next_event_index: %d",
                          next_event_index)
            # If search index is at the end of the list, it means the next
            # event has not been found in the list..
            if next_event_index == nb_events:
                logging.debug("no event to merge: %d (%s, %s → %s)",
                               event_index,
                               event.node,
                               event.start_datetime,
                               event.end_datetime )
                # we can jump to next event in the list
                event_index += 1
            else:
                next_event = events[next_event_index]
                logging.debug("merging %s (%d) with %s (%d)",
                               event,
                               event_index,
                               next_event,
                               next_event_index )
                event.end_datetime = next_event.end_datetime
                # remove the next event out of the list
                events.pop(next_event_index)
                nb_events -= 1
        return events

    def update(self):
        """Update Events in DB."""

        for event in self.events:
            if event.find(self.db):
                event.update(self.db)
            else:
                event.save(self.db)

    @staticmethod
    def txt_slurm_event_type(reason_uid):
        """Convert reason_uid integer that holds node state in Slurm bitmap
           convention to string representing this state into human readable
           format.
        """

        states = []

        slurm_base_states = [
            ( 0x0000, 'UNKNOWN'   ),
            ( 0x0001, 'DOWN'      ),
            ( 0x0002, 'IDLE'      ),
            ( 0x0003, 'ALLOCATED' ),
            ( 0x0004, 'ERROR'     ),
            ( 0x0005, 'MIXED'     ),
            ( 0x0006, 'FUTURE'    ),
            ( 0x0007, 'END'       ),
        ]
        slurm_extra_states = [
            ( 0x0010, 'NET'       ),
            ( 0x0020, 'RES'       ),
            ( 0x0040, 'UNDRAIN'   ),
            ( 0x0100, 'RESUME'    ),
            ( 0x0200, 'DRAIN'     ),
            ( 0x0400, 'COMPLETING'),
            ( 0x0800, 'NO_RESPOND'),
            ( 0x1000, 'POWER_SAVE'),
            ( 0x2000, 'FAIL'      ),
            ( 0x4000, 'POWER_UP'  ),
            ( 0x8000, 'MAINT'     ),
        ]

        for hexval, txtstate in slurm_base_states:
            if (reason_uid & 0xf) == hexval:
                states.append(txtstate)

        for hexval, txtstate in slurm_extra_states:
            if reason_uid & hexval:
                states.append(txtstate)

        if not len(states):
            states.append('UNKNOWN')

        return '+'.join(states)
