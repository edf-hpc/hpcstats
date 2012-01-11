#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

class User:
    def __init__(self, db = None, name = "", login = "", cluster = "", department = "", uid = -1, gid = -1, creation_date = None, deletion_date = None):

        if db == None:
            self._name = name
            self._login = login
            self._cluster = cluster
            self._department = department
            self._uid = uid
            self._gid = gid
            self._creation_date = creation_date
            self._deletion_date = deletion_date
        else:
            self._uid = uid
            self._cluster = cluster
            req = """
                SELECT name,
                       login,
                       gid,
                       department,
                       creation,
                       deletion
                 FROM users
                 WHERE uid = %s AND cluster = %s; """        
            datas = (self._uid, self._cluster)
            cur = db.get_cur()

            cur.execute(req, datas)
            nb_rows = cur.rowcount
        
            if nb_rows == 1:
               row = cur.fetchone()
               self._name = row[0]
               self._login = row[1]
               self._gid = row[2]
               self._department = row[3]
               self._creation_date = row[4]
               self._deletion_date = row[5]
            elif nb_rows == 0:
                raise UserWarning, ("User not found for uid %d on cluster %s" % \
                                     ( self._uid,
                                       self._cluster ) )
            else:
                raise UserWarning, ("incorrect number of results (%d) for uid %d on cluster %s" % \
                                     ( nb_rows,
                                       self._uid,
                                       self._cluster ) )

    def __str__(self):
        if self._creation_date == None:
           creation_date = "unknown"
        else:
           creation_date = self._creation_date.strftime('%Y-%m-%d')
        if self._deletion_date == None:
           deletion_date = "unknown"
        else:
           deletion_date = self._deletion_date.strftime('%Y-%m-%d')
        return self._name + " [" + self._department + "] " + self._login + " - " + self._cluster + " (" + str(self._uid) + "|" + str(self._gid) + "): " + creation_date + "/" + deletion_date

    def set_uid(self, uid):
        self._uid = uid

    def set_gid(self, gid):
        self._gid = gid

    def get_login(self):
        return self._login

    def get_cluster(self):
        return self._cluster

    def exists_in_db(self, db):
        cur = db.get_cur()
        cur.execute("SELECT login FROM users WHERE login = %s AND cluster = %s",
                     (self._login,
                      self._cluster) )
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False
        else:
           raise UserWarning, ("incorrect number of results (%d) for login \
                                %s on cluster %s" % \
                                ( nb_rows,
                                  self._login,
                                  self._cluster ) )

    def save(self, db):
        req = """
            INSERT INTO users (
                            name,
                            login,
                            cluster,
                            department,
                            creation,
                            deletion,
                            uid,
                            gid )
            VALUES ( %s, %s, %s, %s, %s, %s, %s, %s); """
        datas = (
            self._name,
            self._login,
            self._cluster,
            self._department,
            self._creation_date,
            self._deletion_date,
            self._uid,
            self._gid )
 
        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE users SET
                       name = %s,
                       cluster = %s,
                       department = %s,
                       creation = %s,
                       deletion = %s,
                       uid = %s,
                       gid = %s
            WHERE login = %s
              AND cluster = %s; """
        datas = (
            self._name,
            self._cluster,
            self._department,
            self._creation_date,
            self._deletion_date,
            self._uid,
            self._gid,
            self._login,
            self._cluster )

        #print db.get_cur().mogrify(req, datas)
        db.get_cur().execute(req, datas)

    """ accessors """

    def get_name(self):
        return self._name

    def get_department(self):
        return self._department

