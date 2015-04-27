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
from datetime import datetime
from HPCStats.Importer.Importer import Importer
from HPCStats.Model.Event import Event

class EventImporter(Importer):

    def __init__(self, app, db, config, cluster):

        super(EventImporter, self).__init__(app, db, config, cluster)

        self._new_events = []
        self._unfinished_events = []

    def _get_last_end_datetime(self):
        req = """
                SELECT MAX(event_end) AS last
                  FROM Event
                 WHERE cluster_name = %s
              """
        params = ( self.cluster.name, )
        cur = self.db.get_cur()
        cur.execute(req, params)

        db_row = cur.fetchone()
        return db_row[0]

    def _get_first_start_datetime_unfinished_event(self):
        req = """
                SELECT MIN(event_start)
                  FROM Event
                 WHERE cluster_name = %s
                   AND event_end IS NULL
              """
        params = ( self.cluster.name, )
        cur = self.db.get_cur()
        cur.execute(req, params)

        db_row = cur.fetchone()
        return db_row[0]

    def _get_unfinished_events(self):
        req = """
                SELECT event_id,
                       node_name,
                       event_type,
                       event_reason,
                       event_nbCpu,
                       event_start
                 FROM Events
                 WHERE cluster_name = %s
                   AND event_end IS NULL
              """
        params = ( self.cluster.name, )
        cur = self.db.get_cur()
        cur.execute(req, params)

        while (1):
            db_row = cur.fetchone()
            if db_row == None: break
            event = Event( event_id = db_row[0],
                           node = db_row[1],
                           cluster = self.cluster.name,
                           event_type = db_row[2],
                           reason = db_row[3],
                           nb_cpu = db_row[4],
                           start_datetime = db_row[5],
                           end_datetime = None )
            self._unfinished_events.append(event)

    def _finish_known_events(self):
        for unfinished_event in self._unfinished_events:
            new_event_index = 0
            nb_new_events = len(self._new_events)
            found_event = False
            while not found_event and new_event_index < nb_new_events:            
                event = self._new_events[new_event_index]
                if event.node == unfinished_event.node and \
                   event.nb_cpu == unfinished_event.nb_cpu and \
                   event.start_datetime == unfinished_event.start_datetime and \
                   event.event_type == unfinished_event.event_type:
                    # specify end_datetime in unfinished_events[]
                    # and delete event of new_events[]
                    unfinished_event.end_datetime = event.end_datetime
                    self._new_events.pop(new_event_index)
                    found_event = True
                if event.reason != unfinished_event.reason:
                    logging.debug("Update reason of %s to %s", unfinished_event, event.reason)
                    unfinished_event.reason = event.reason
                    unfinished_event.update_reason(self.db)
                new_event_index += 1

    def _update_unfinished_events(self):
        logging.debug("launching the update of %d previously known events",
                       len(self._unfinished_events) )

        for unfinished_event in self._unfinished_events:
            if unfinished_event.end_datetime:
                logging.debug("updating end datetime of event %s",
                               unfinished_event )
                unfinished_event.update_end_datetime(self.db)

    def _save_new_events(self):
        logging.debug("launching the save of %d new events",
                       len(self._new_events) )
        for new_event in self._new_events:
            logging.debug("new event %s", str(new_event))
            new_event.save(self.db)
