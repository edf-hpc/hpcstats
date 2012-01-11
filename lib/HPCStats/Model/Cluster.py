#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.Job import Job

class Cluster:
    def __init__(self, name = ""):

        self._name = name
    
    def __str__(self):
        return self._name

    def exists_in_db(self, db):
        print "db:", db, type(db)
        cur = db.get_cur()
        cur.execute("SELECT name FROM clusters WHERE name = %s;", (self._name,) )
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False
        else:
           raise UserWarning, ("incorrect number of results (%d) for cluster \
                                %s" % \
                                ( nb_rows,
                                  self._name ) )

    def get_nb_cpus(self, db):

        req = """ SELECT SUM(cpu) FROM nodes WHERE cluster = %s; """
        datas = ( self._name, )

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        return cur.fetchone()[0]

    def get_min_datetime(self, db):

        req = """ SELECT MIN(running_datetime) FROM jobs WHERE clustername = %s; """
        datas = ( self._name, )

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        return cur.fetchone()[0]

    def get_interval_jobs(self, db, begin, end):

        # get all jobs that have been running during (at least partially) during the interval
        req = """
            SELECT id_job,
                   sched_id,
                   uid,
                   gid,
                   submission_datetime,
                   running_datetime,
                   end_datetime,
                   nb_nodes,
                   nb_cpus,
                   running_queue,
                   state
              FROM jobs
             WHERE clustername = %s
                  AND ( state = 'COMPLETE' OR state = 'FAILED' )
                  AND (   (running_datetime BETWEEN %s AND %s)
                       OR (end_datetime BETWEEN %s AND %s)
                       OR (running_datetime <= %s AND end_datetime >= %s)
                      )
             ORDER BY end_datetime; """
        datas = (self._name, begin, end, begin, end, begin, end)

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)

        jobs = []

        while (1):

            row = cur.fetchone()
            if row == None: break
            
            #print "row", len(row), row
            job = Job( id_job = row[0],
                       sched_id = row[1],
                       uid = row[2],
                       gid = row[3],
                       submission_datetime = row[4],
                       running_datetime = row[5],
                       end_datetime = row[6],
                       nb_hosts = row[7],
                       nb_procs = row[8],
                       running_queue = row[9],
                       state = row[10],
                       clustername = self._name)
            jobs.append(job)

        return jobs
   
    def get_nb_accounts(self, db, creation_date):

        req = """
            SELECT COUNT (name)
              FROM users
             WHERE creation < %s
               AND cluster = %s; """
        datas = (creation_date, self._name)

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        
        return cur.fetchone()[0]

    def get_nb_active_users(self, db, start, end):
   
        req = """
            SELECT COUNT(DISTINCT uid)
              FROM jobs
            WHERE (running_datetime BETWEEN %s AND %s)
               OR (end_datetime BETWEEN %s AND %s)
               OR (running_datetime <= %s AND end_datetime >= %s); """
        datas = (start, end, start, end, start, end)
        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        
        return cur.fetchone()[0]


    def save(self, db):
        req = """ INSERT INTO clusters ( name ) VALUES ( %s ); """
        datas = ( self._name, )
 
        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    def update(self, db):
        # nothing to do here
        pass

    """ accessors """

    def get_name(self):
        return self._name
