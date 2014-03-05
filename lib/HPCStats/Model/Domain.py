#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

class Domain:
    def __init__(self, id = "", description = ""):
       
        self._id = id #id est ici un chaine de caractère
        self._description = description

    def __str__(self):
        if self._description == None:
           description = "unknown"
        else:
           description = self._description
        return self._id + " : " + self._description

    """ getter accessors """
    def get_id(self):
        return self._id

    def get_description(self):
        return self._description

    """ setter accessors """
    def set_description(self, description):
        self._description = description

    """ methodes """
    def save(self, db):
        req = """
            INSERT INTO domains (
                              id_domain,
                              description )
            VALUES (%s, %s);"""
        datas = (
            self._id,
            self._description )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE domains SET 
                         id_domain = %s,
                         description = %s 
            WHERE id_domain = %s;"""
        datas = (
            self._id,
            self._description,
            self._id )
        db.get_cur().execute(req, datas)

    def already_exist(self, db):
        cur = db.get_cur()
        cur.execute("SELECT * FROM domains WHERE id_domain = %s", (self._id,))
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False

def delete_domains(db):
    db.get_cur().execute("DELETE FROM domains;")

 
