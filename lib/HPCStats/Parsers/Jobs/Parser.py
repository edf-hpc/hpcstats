#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import csv
from Queue import *
from threading import Thread
import time
from datetime import date, datetime

from Modelpkg.Job import Job
from utils import logger
from Dbpkg.Db import Db
from time import gmtime, strftime



class Parser(object):
    """ boite a outil des methodes de parsing"""
    total_th = 0
    thread_nb = 0
    num_worker_threads = 1

    def __init__(self, cluster, conf, debuglevel=0, verbose=0, pushall=False):
        """
        cluster : cluster name. Ex: clamart2
        debuglevel : 0 by default
        verbose : verbosity. 0 by default
        pushall : False by default
        
        """
        
        super(ParseFile, self).__init__()
        self.debuglevel = debuglevel
        self._verbose = verbose
        self._pushall = pushall
        self._q = Queue()
        self.conf = conf
        self.cluster = conf.get_cluster_name()

    def debug(self, msg):
        """ methode de debug"""
        
        logger(msg, self.debuglevel)
   

    def process(self, files, num_worker_threads=None):
        """Docstring for process"""
        if num_worker_threads:
            self.num_worker_threads = num_worker_threads
        self.debug("> DEBUG : Function() : process")

        for logfile in files:
            self._q.put(logfile.strip())
            #if debuglevel > 0: 
                  #print">       + put in queue : %s" % q

        for i in range(self.num_worker_threads):
            t = Thread(target=self._worker)
            #if debuglevel > 0: 
            #print">       + thread # %d" % t
            t.start()
        self._q.join()

        self.debug("> DEBUG : end update")

    def _worker(self):
        """gere les threads"""        
        self.total_th += 1
        self.thread_nb = self.total_th % self.num_worker_threads + 1
        self.debug("> DEBUG : Function() : worker;\tthread #%d" % self.thread_nb)
        while not self._q.empty():
            logfile = self._q.get()
            self.debug("        + parsing file thread #%d %s" % (self.thread_nb, logfile))
            self._parse(logfile)
            self._q.task_done()

    def _parse(self, filename):
        """ parse les jobs et les concantene"""        
        jobs = []
        lines = self._read_file(filename)
        print "parsing file ", filename
        for line in lines:
            if line == '':
                continue
            else:
                new_job = self.get_result(line)
                # adding the new job in jobs list
                if new_job:
                    jobs.append(new_job)
        if self._pushall:
            self.pushall(jobs)
        else:
            self.update(jobs)

    def _read_file(self, filename):
        """ lie, stocke les lignes et les renvoie"""
        
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def add_user_of_job(self, job):
        """
        ajoute un utilisateur quand celui du job n'existe pas
        """
        self.debug("> DEBUG : Function() : add_user_of_job;")
        self.debug(">         + connect to DB")
        """A CHANGER"""
        conn = Db(self.conf).supervision_connection()[1]
        cur = conn.cursor()

        self.debug(">         + insert %s" % job.user)
        if self._verbose:
            print "Inserting missing user %s for cluster %s" % (job.user, self.cluster) 
        
        print job.user, self.cluster,  job.submission_datetime.strftime('%Y-%m-%d')
        cur.execute('INSERT INTO users (name, cluster, creation) VALUES (%s, %s, %s)', (job.user, self.cluster,  job.submission_datetime.strftime('%Y-%m-%d')))

        self.debug("> DEBUG : end transactions ")
        conn.commit()
        cur.close()
        self.debug("> DEBUG : close DB ")
        conn.close()

    def exists_user_of_job(self, job):
        """
        teste si l'utilisateur du job existe
        """
        self.debug("> DEBUG : Function() : exists_user_of_job;")
        self.debug(">         + connect to DB")

        conn = Db(self.conf).supervision_connection()[1]
        cur = conn.cursor()
        self.debug(">         + verify existence of user %s for cluster %s " % (job.user, self.cluster))
        print "self.cluster", self.cluster
        cur.execute('SELECT name FROM users WHERE name=%s AND cluster=%s', (job.user, self.cluster))
        result = False
        if cur.rowcount > 0:
            result = True

        self.debug("> DEBUG : end transactions ")
        conn.commit()
        cur.close()
        self.debug("> DEBUG : close DB ")
        conn.close()
        print result
        return result

    def update(self, jobs):
        """
        Docstring for update
        """
        self.debug("> DEBUG : Function() : update;")
        self.debug(">         + connect to DB")

        if not jobs:
            self.debug("> DEBUG : no job found")
        else:
            """ A CHANGER"""
            
            conn = Db(self.conf).supervision_connection()[1]
            cur = conn.cursor()
            for job in jobs:
                print "check", job
                self.debug(">         + insert %s @ %s" % (job.number, job.user))

                if not self.exists_user_of_job(job):
                    print "add user"
                    self.add_user_of_job(job)
                    
                print job.number, job.user, job.group, job.submission_datetime, job.running_datetime, job.end_datetime, job.nb_hosts, job.nb_procs    
                try:
                    job.number = (job.number).split('.')[0]
                    print "user exists"
                except:
                    pass
                    
                cur.execute('INSERT INTO jobs_tmp (number, username, groupname, submission_datetime, running_datetime, end_datetime, nb_nodes, nb_cpus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (job.number, job.user, job.group, job.submission_datetime, job.running_datetime, job.end_datetime, job.nb_hosts, job.nb_procs))

            self.debug("> DEBUG : end transactions ")
            conn.commit()
            cur.close()
            self.debug("> DEBUG : close DB ")
            conn.close()


