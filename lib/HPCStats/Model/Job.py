#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

class Job:

    def __init__(self, id_job = 0, uid = "", gid = "", submission_datetime = 0, running_datetime = 0, end_datetime = 0, nb_procs = 0, nb_hosts = 0, running_queue = "", nodes = "", state = "unknown"):
        self._id_job = id_job
        self._uid = uid
        self._gid = gid
        self._submission_datetime = submission_datetime
        self._running_datetime = running_datetime
        self._end_datetime = end_datetime
        self._nb_procs = nb_procs
        self._nb_hosts = nb_hosts
        self._running_queue = running_queue
        self._nodes = nodes
        self._state = state

    def __str__(self):
        if self._running_datetime == 0:
           running_datetime = "notyet"
        else:
           running_datetime = self._running_datetime.strftime('%Y-%m-%d %H:%M:%S')
        if self._end_datetime == 0:
           end_datetime = "notyet"
        else:
           end_datetime = self._end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return self._id_job
#        return self._id_job + " (" + self._uid+"|"+self._gid + "): " + self._submission_datetime.strftime('%Y-%m-%d %H:%M:%S') + " / " + running_datetime + " / " + end_datetime + " -> " + str(self._nb_hosts) + "/"  + str(self._nb_procs) + " [" + ",".self._nodes + "]"+.self._state

    def jobs_query(self):
        return "INSERT INTO jobs (id_job, uid, gid, running_queue, submission_datetime, running_datetime, end_datetime, nb_nodes, nb_cpus, state) VALUES ('%s', '%s', '%s', '%s', %s, %s, %s, '%s', '%s', '%s')" % (self._id_job, self._uid, self._gid, self._running_queue, self._submission_datetime, self._running_datetime, self._end_datetime, self._nb_procs, self._nb_hosts, self._state)

    def save(self, db):
        db._cur.execute(self.jobs_query())
        
