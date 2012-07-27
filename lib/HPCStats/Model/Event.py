#!/usr/bin/python
# -*- coding: utf-8 -*-

class Event:
    def __init__(self, nodename = "", start_datetime = 0, end_datetime = 0, event_type = ""):

        self._nodename = nodename
        self._start_datetime = start_datetime
        self._end_datetime = end_datetime
        self._event_type = event_type

    def __str__(self):
        return "event on node %s (%s) : %s → %s" % \
                   ( self._nodename,
                     self._event_type,
                     self._start_datetime, 
                     self._end_datetime )

    def save(self, db):
        req = """
            INSERT INTO events (
                            node,
                            t_start,
                            t_end,
                            type )
            VALUES ( %s, %s, %s, %s); """
        datas = (
            self._nodename,
            self._start_datetime,
            self._end_datetime,
            self._event_type )
 
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
               self._start_datetime == other._start_datetime and \
               self._end_datetime == other._end_datetime and \
               self._event_type == other._event_type

    #
    # accessors
    #

    def get_nodename(self):
        return self._nodename

    def get_start_datetime(self):
        return self._start_datetime

    def get_end_datetime(self):
        return self._end_datetime

    def get_event_type(self):
        return self._event_type

    def set_end_datetime(self, end_datetime):
        self._end_datetime = end_datetime

    def set_event_type(self, event_type):
        self._event_type = event_type
