#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.User import User

class UserFinder():

    def __init__(self, db):

        self._db = db

    def find(self, cluster_name, uid):
        req = """
            SELECT name,
                   login,
                   department,
                   gid,
                   creation,
                   deletion
              FROM users
             WHERE uid = %s
               AND cluster = %s; """
        data = (
            uid,
            cluster_name )

        cur = self._db.get_cur()
        #print cur.mogrify(req, data)
        cur.execute(req, data)
        
        nb_rows = cur.rowcount
        if nb_rows == 1:
            row = cur.fetchone()
            return User( name = row[0],
                         login = row[1],
                         cluster_name = cluster_name,
                         department = row[2],
                         uid = uid,
                         gid = row[3],
                         creation_date = row[4],
                         deletion_date = row[5] )

        elif nb_rows == 0:
           raise UserWarning, ("no user found with uid %d \
                                on cluster %s" % \
                                ( uid,
                                  cluster_name ) )
        else:
           raise UserWarning, ("incorrect number of results (%d) for uid \
                                %s on cluster %s" % \
                                ( nb_rows,
                                  uid,
                                  cluster_name ) )

