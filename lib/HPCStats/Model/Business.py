#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

class Business:
    def __init__(self, id = "", key="", description = ""):

        self._id = id
        self._key = key
        self._description = description

    def __str__(self):
        if self._description == None:
           description = "unknown"
        else:
           description = self._description
        return self._id + " : " + self._key + " - " + self._description

    """ getter accessors """
    def get_id(self):
        return self._id

    def get_key(self):
        return self._key

    def get_description(self):
        return self._description

    """ setter accessors """
    def set_description(self, description):
        self._description = description


    """ methodes """
    def save(self, db):
        req = """
            INSERT INTO business (
                              key,
                              description )
            VALUES (%s, %s);"""
        datas = (
            self._key,
            self._description )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE business SET 
                         key = %s,
                         description = %s 
            WHERE id = %s;"""
        datas = (
            self._key,
            self._description, 
            self._id )
        db.get_cur().execute(req, datas)

    def already_exist(self, db):
        cur = db.get_cur()
        cur.execute("SELECT * FROM business WHERE key = %s", (self._key,))
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False

    def business_from_key(self, db, key):
        cur = db.get_cur()
        cur.execute("SELECT * FROM business WHERE key = %s", (key,))
        res = cur.fetchone()
        self._id = res[0]
        self._key = res[1]
        self._description = res[2]

def delete_business(db):
    db.get_cur().execute("ALTER SEQUENCE business_id_seq RESTART WITH 1;")  
    db.get_cur().execute("DELETE FROM business;")  

def get_business_id(db, business):
    cur = db.get_cur()
    cur.execute("SELECT id_business FROM business WHERE lower(key) = lower(%s)", (business,))
    results = cur.fetchone()
    return results[0]
