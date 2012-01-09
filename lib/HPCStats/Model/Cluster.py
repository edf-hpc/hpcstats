#!/usr/bin/python
# -*- coding: utf-8 -*-

class Cluster:
    def __init__(self, name = ""):

        self._name = name
    
    def __str__(self):
        return "cluster %s" % (self._name)

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

    def save(self, db):
        req = """ INSERT INTO clusters ( name ) VALUES ( %s ); """
        datas = ( self._name, )
 
        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    def update(self, db):
        # nothing to do here
        pass
