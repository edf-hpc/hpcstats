#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

class Event:
    def __init__(self, nodename = "", nb_cpu = 0, start_datetime = 0, end_datetime = 0, event_type = "", reason = ""):

        self._nodename = nodename
        self._nb_cpu = nb_cpu
        self._start_datetime = start_datetime
        self._end_datetime = end_datetime
        self._event_type = event_type
        self._reason = reason

    def __str__(self):
        return "event on node %s/%d (%s) : %s → %s" % \
                   ( self._nodename,
                     self._nb_cpu,
                     self._event_type,
                     self._start_datetime, 
                     self._end_datetime )

    def save(self, db):
	cur = db.get_cur()
        cur.execute("SELECT * FROM events WHERE node = %s AND t_start = %s AND t_end = %s",
                     (self._nodename,
                      self._start_datetime,
                      self._end_datetime) )
        nb_rows = cur.rowcount

        if nb_rows == 0:
          req = """
            INSERT INTO events (
                            node,
                            nb_cpus,
                            t_start,
                            t_end,
                            type,
                            reason )
            VALUES ( %s, %s, %s, %s, %s, %s); """
          datas = (
            self._nodename,
            self._nb_cpu,
            self._start_datetime,
            self._end_datetime,
            self._event_type,
            self._reason )
 
          #print db.get_cur().mogrify(req, datas)
          db.execute(req, datas)
    
    def update_end_datetime(self, db):
        req = """
            UPDATE events
               SET t_end = %s
             WHERE node = %s
               AND t_start = %s
               AND type = %s; """
        datas = (
            self._end_datetime,
            self._nodename,
            self._start_datetime,
            self._event_type )
 
        #print db.get_cur().mogrify(req, datas)
        db.execute(req, datas)

    def update_reason(self, db):
        req = """
            UPDATE events
               SET reason = %s
            WHERE node = %s
               AND t_start = %s
               AND type = %s; """
        datas = (
            self._reason,
            self._nodename,
            self._start_datetime,
            self._event_type )
        db.execute(req, datas)

    #
    # utilities
    #

    def merge_event(self, event):
        self._end_datetime = event._end_datetime

    #
    # operators
    #

    def __eq__(self, other):
        return self._nodename == other._nodename and \
               self._nb_cpu == other._nb_cpu and \
               self._start_datetime == other._start_datetime and \
               self._end_datetime == other._end_datetime and \
               self._event_type == other._event_type and \
               self._reason == other._reason

    #
    # accessors
    #

    def get_nodename(self):
        return self._nodename

    def get_nb_cpu(self):
        return self._nb_cpu

    def get_start_datetime(self):
        return self._start_datetime

    def get_end_datetime(self):
        return self._end_datetime

    def get_event_type(self):
        return self._event_type

    def get_reason(self):
        return self._reason

    def set_end_datetime(self, end_datetime):
        self._end_datetime = end_datetime

    def set_event_type(self, event_type):
        self._event_type = event_type

    def set_reason(self, reason):
        self._reason = reason

