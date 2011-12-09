#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from HPCStats.DB.Jobs import DBJobs

class Job:

    def __init__(self, nb =0):
        self.number = nb
        self.user = ""
        self.groups = []
        self.submission_datetime = 0
        self.running_datetime = 0
        self.end_datetime = 0
        self.nb_procs = 0
        self.nb_hosts = 0
        self.running_queue = ""
        self.hosts = []

    def __str__(self):
        if self.running_datetime == 0:
           running_datetime = "notyet"
        else:
           running_datetime = self.running_datetime.strftime('%Y-%m-%d %H:%M:%S')
        if self.end_datetime == 0:
           end_datetime = "notyet"
        else:
           end_datetime = self.end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return self.number + " (" + self.user + "): " + self.submission_datetime.strftime('%Y-%m-%d %H:%M:%S') + " / " + running_datetime + " / " + end_datetime + " -> " + str(self.nb_hosts) + "/"  + str(self.nb_procs) + " [" + ",".join(self.hosts) + "]"

    def store(self, db):
        dbjob = DBJobs(db)
        dbjob.store(self)
