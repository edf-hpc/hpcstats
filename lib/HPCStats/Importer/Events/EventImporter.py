#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from HPCStats.Model.Event import Event

class EventImporter(object):

    def __init__(self, db, config, cluster_name):

        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        self._new_events = []
        self._unfinished_events = []

    def _get_last_end_datetime(self):
        req = """
              SELECT MAX(t_end) AS last
                FROM events; """
        datas = ()
        cur = self._db.get_cur()
        cur.execute(req, datas)

        db_row = cur.fetchone()
        return db_row[0]

    def _get_unfinished_events(self):
        req = """
              SELECT node,
                     t_start,
                     type
                FROM events
               WHERE t_end IS NULL; """
        datas = ()
        cur = self._db.get_cur()
        cur.execute(req, datas)

        while (1):
            db_row = cur.fetchone()
            if db_row == None: break
            event = Event(  nodename = db_row[0],
                            start_datetime = db_row[1],
                            end_datetime = None,
                            event_type = db_row[2] )
            self._unfinished_events.append(event)

    def _finish_known_events(self):
        for unfinished_event in self._unfinished_events:
            new_event_index = 0
            nb_new_events = len(self._new_events)
            found_event = False
            while not found_event and new_event_index < nb_new_events:            
                event = self._new_events[new_event_index]
                if event.get_nodename() == unfinished_event.get_nodename() and \
                   event.get_start_datetime() == unfinished_event.get_start_datetime() and \
                   event.get_event_type() == unfinished_event.get_event_type():
                    # specify end_datetime in unfinished_events[]
                    # and delete event of new_events[]
                    unfinished_event.set_end_datetime(event.get_end_datetime())
                    self._new_events.pop(new_event_index)
                    found_event = True
                new_event_index += 1

    def _update_unfinished_events(self):
        logging.debug("launching the update of %d previously known events",
                       len(self._unfinished_events) )

        for unfinished_event in self._unfinished_events:
            if unfinished_event.get_end_datetime():
                logging.debug("updating end datetime of event %s",
                               unfinished_event )
                unfinished_event.update_end_datetime(self._db)

    def _save_new_events(self):
        logging.debug("launching the save of %d new events",
                       len(self._new_events) )
        for new_event in self._new_events:
            new_event.save(self._db)
