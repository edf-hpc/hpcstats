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
                FROM events,
                     nodes
               WHERE nodes.name = events.node
                 AND nodes.cluster = %s ; """
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)

        db_row = cur.fetchone()
        return db_row[0]

    def _get_first_start_datetime_unfinished_event(self):
        req="""
            SELECT MIN(t_start)
            FROM events,
                 nodes
            WHERE nodes.name = events.node
              AND nodes.cluster = %s
              AND t_end IS NULL;"""
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)

        db_row = cur.fetchone()
        return db_row[0]

    def _get_unfinished_events(self):
        req = """
              SELECT node,
                     nb_cpus,
                     t_start,
                     type,
                     reason,nodes
               FROM events,nodes
               WHERE nodes.name = events.node
                 AND nodes.cluster =%s
                 AND events.t_end IS NULL; """
        datas = (self._cluster_name,)
        cur = self._db.get_cur()
        cur.execute(req, datas)

        while (1):
            db_row = cur.fetchone()
            if db_row == None: break
            event = Event(  nodename = db_row[0],
                            nb_cpu = db_row[1],
                            start_datetime = db_row[2],
                            end_datetime = None,
                            event_type = db_row[3],
                            reason = db_row[4])
            self._unfinished_events.append(event)

    def _finish_known_events(self):
        for unfinished_event in self._unfinished_events:
            new_event_index = 0
            nb_new_events = len(self._new_events)
            found_event = False
            while not found_event and new_event_index < nb_new_events:            
                event = self._new_events[new_event_index]
                if event.get_nodename() == unfinished_event.get_nodename() and \
                   event.get_nb_cpu() == unfinished_event.get_nb_cpu() and \
                   event.get_start_datetime() == unfinished_event.get_start_datetime() and \
                   event.get_event_type() == unfinished_event.get_event_type():
                    # specify end_datetime in unfinished_events[]
                    # and delete event of new_events[]
                    unfinished_event.set_end_datetime(event.get_end_datetime())
                    self._new_events.pop(new_event_index)
                    found_event = True
                if event.get_reason() != unfinished_event.get_reason():
                    logging.debug("Update reason of %s to %s", unfinished_event, event.get_reason())
                    unfinished_event.set_reason(event.get_reason())
                    unfinished_event.update_reason(self._db)
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
            logging.debug("had new event from node %s, start %s -> end %s",
                           new_event.get_nodename(),
                           new_event.get_start_datetime(),
                           new_event.get_end_datetime() )
            new_event.save(self._db)
