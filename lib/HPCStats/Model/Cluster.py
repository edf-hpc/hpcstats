#!/usr/bin/python
# -*- coding: utf-8 -*-

class Cluster:
    def __init__(self, name = ""):

        self._name = name
    
    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self._name == other._name

    def exists_in_db(self, db):
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

        req = """
            SELECT MIN(running_datetime)
              FROM jobs
             WHERE clustername = %s
               AND state NOT IN ('CANCELLED', 'NODE_FAIL', 'PENDING');
              """
        datas = ( self._name, )

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)
        return cur.fetchone()[0]

   
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

    def get_unknown_users(self, db):
        req = """
            SELECT distinct(uid)
              FROM jobs
             WHERE clustername = %s
               AND uid NOT IN (SELECT uid FROM users WHERE users.cluster = %s); """
        datas = (self._name, self._name)

        cur = db.get_cur()
        #print cur.mogrify(req, datas)
        cur.execute(req, datas)

        unknown_users = []

        while (1):

            row = cur.fetchone()
            if row == None: break
            uid = int(row[0])
            unknown_users.append(uid)

        return unknown_users;
        

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
