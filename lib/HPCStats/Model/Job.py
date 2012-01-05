#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

class Job:

    def __init__(self, db_id = 0, id_job = 0, sched_id = 0, clustername = "", uid = -1, gid = -1, submission_datetime = 0, running_datetime = 0, end_datetime = 0, nb_procs = 0, nb_hosts = 0, running_queue = "", nodes = "", state = "unknown"):
        self._db_id = db_id
        self._sched_id = sched_id
        self._id_job = id_job
        self._clustername = clustername
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
        return self._id_job + " (" + self._uid+"|"+self._gid + "): " + self._submission_datetime.strftime('%Y-%m-%d %H:%M:%S') + " / " + self._running_datetime.strftime('%Y-%m-%d %H:%M:%S') + " / " + self._end_datetime.strftime('%Y-%m-%d %H:%M:%S') + " -> " + str(self._nb_hosts) + "/"  + str(self._nb_procs) + " [" + self._nodes + "]"+ self._state

    def save(self, db):
        req = "INSERT INTO jobs (id_job, sched_id, uid, gid, clustername, running_queue, submission_datetime, running_datetime, end_datetime, nb_nodes, nb_cpus, state) VALUES ('%s', '%s', %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (self._id_job, self._sched_id, self._uid, self._gid, self._clustername, self._running_queue, self._submission_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._running_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._end_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._nb_hosts, self._nb_procs, self._state)
        db.get_cur().execute(req)
        
    def update(self, db):
        req = "UPDATE jobs SET \
               id_job = '%s', \
                uid = %s, \
                gid = %s, \
                clustername = '%s', \
                running_queue = '%s', \
                submission_datetime = '%s', \
                running_datetime = '%s', \
                end_datetime = '%s', \
                nb_nodes = '%s', \
                nb_cpus = '%s', \
                state = '%s' WHERE sched_id = '%s' " % (self._id_job, self._uid, self._gid, self._clustername, self._running_queue, self._submission_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._running_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._end_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._nb_hosts, self._nb_procs, self._state, self._sched_id)
        db.get_cur().execute(req)
