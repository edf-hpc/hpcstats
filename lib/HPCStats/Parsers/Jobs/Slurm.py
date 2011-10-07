#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import jobs ##### FIXME
from datetime import datetime

class Slurm:
   
    def __init__(self, config):
        self.config = config


    def parse(self):
        # FIXME DB From config
        jbos = []
        maconfInfo = ManageInfo(self.conf)
        indexmax = int(maconfInfo.readPickle("sS'valeurmax'\n"))
        print 'lindexmax', indexmax
        jobs = []
        conn = Db(self.conf).connection_mysql()[1]
        cur = conn.cursor()                        
        
        #indexmax = 0
           
        cur.execute('select id_job, id_user, id_group, time_submit, time_start, time_end, nodes_alloc,cpus_alloc  from  ivanoe_job_table where id_job > %s', (indexmax))         
        response = cur
        for i in response:    
             if i[5] != 0 and i[1] != 0: 
                jobs.append(self.resultSlurm(i))
                print self.get_resultSlurm(i)

        
             else:
                pass 

        try :
            print i[0]
            maconfInfo.writePickle('init',str(i[0]))
        except:
            print "pas de jobs a selectionner"  

        return jobs

    def get_resultSlurm(self, i):
        """
        Returns a Job object from a line created from  Slurm Database, replace id_user by users.name (synchro)
        """      
        new_job = []
        liste = []       
        liste.append(datetime.fromtimestamp(int(i[3]))) 
        liste.append(datetime.fromtimestamp(int(i[4])))              
        """ job non terminee"""        
        liste.append(datetime.fromtimestamp(int(i[5])))          
        print "node alloue", i[6]
        print "cpu alloue", i[7]
        number = i[0]
        user = str(i[1])
        group = i[2]
        submission_datetime = liste[0]
        running_datetime = liste[1]
        end_datetime = liste[2]
        nb_hosts = i[6]
        nb_procs = i[7]
        conn = Db(self.conf).supervision_connection()[1]
        cur = conn.cursor()    
        cur.execute("SELECT name FROM users  WHERE users.uidnumber  = %s", (user,))
        val = cur.fetchone()
        if val:
            print val[0]
            user = val[0]  
        else:
            pass           
        new_job = Modelpkg.Job.Job(number=number, user=user, group=group, running_datetime=running_datetime, submission_datetime=submission_datetime, end_datetime=end_datetime, nb_hosts=nb_hosts, nb_procs=nb_procs)
        return new_job
        print "newjob", new_job   


    # FIXME !!!
    def get_max_job(self):         
        """ methode permettant l'update en recuperant le dernier id update"""
        conn = Db(self.conf).supervision_connection()[1]
        cur = conn.cursor()
        cur.execute("SELECT max(number) from  jobs")          
        maxval = cur.fetchone()         
        if maxval[0] == None:
            return 0
        else:
            return maxval

