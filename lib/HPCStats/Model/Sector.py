#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

class Sector:
    def __init__(self, id = "", domain="", description = ""):

        self._id = id
        self._domain = domain
        self._description = description

    def __str__(self):
        if self._description == None:
           description = "unknown"
        else:
           description = self._description
        return self._id + " : " + self._domain + " - " + self._description

    """ getter accessors """
    def get_id(self):
        return self._id

    def get_domain(self):
        return self._domain

    def get_description(self):
        return self._description

    """ setter accessors """
    def set_description(self, description):
        self._description = description

    """ methodes """
    def save(self, db):
        req = """
            INSERT INTO sectors (
                              id_sectors,
                              id_domain,
                              description )
            VALUES (%s, %s, %s);"""
        datas = (
            self._id,
            self._domain,
            self._description )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE sectors SET 
                         id_domain = %s,
                         description = %s 
            WHERE id = %s;"""
        datas = (
            self._domain,
            self._description,
            self._id )
        db.get_cur().execute(req, datas)

    def already_exist(self, db):
        cur = db.get_cur()
        cur.execute("SELECT * FROM sectors WHERE id_sectors = %s AND id_domain = %s", (self._id, self._domain,))
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False

def delete_sectors(db):
    db.get_cur().execute("DELETE FROM sectors;")

 
