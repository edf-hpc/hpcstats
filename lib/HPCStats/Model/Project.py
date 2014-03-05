#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

class Project:
    def __init__(self, id = "", sector = "", domain = "", description = "", pareo = ""):

        self._id = id
        self._sector = sector
        self._domain = domain
        self._description = description
        self._pareo = pareo

    def __str__(self):
        if self._sector == None:
           sector = "unknown"
        else:
           sector = self._sector
        if self._domain == None:
           domain = "unknown"
        else:
           domain = self._domain
        if self._description == None:
           description = "unknown"
        else:
           description = self._description
        return self._id + " : " + self._pareo + " : " + self._sector + " - " + self._domain + " - " + self._description

    """ getter accessors """
    def get_id(self):
        return self._id

    def get_sector(self):
        return self._sector

    def get_domain(self):
        return self._domain

    def get_description(self):
        return self._description

    def get_pareo(self):
        return self._pareo

    """ setter accessors """
    def set_description(self, description):
        self._description = description

    def set_pareo(self, pareo):
        self._pareo = pareo

    """ methodes """
    def save(self, db):
        req = """
            INSERT INTO projects (
                              id_sector,
                              id_domain,
                              description,
                              pareo )
            VALUES (%s, %s, %s, %s);"""
        datas = (
            self._sector,
            self._domain,
            self._description,
            self._pareo )
        db.get_cur().execute(req, datas)

    def update(self, db):
        req = """
            UPDATE projects SET 
                         sector = %s,
                         domain = %s,
                         description = %s 
                         pareo = %s 
            WHERE id = %s;"""
        datas = (
            self._sector,
            self._domain, 
            self._description, 
            self._pareo, 
            self._id )
        db.get_cur().execute(req, datas)

    def already_exist(self, db):
        cur = db.get_cur()
        cur.execute("SELECT * FROM projects WHERE pareo = %s", (self._pareo,))
        nb_rows = cur.rowcount
        if nb_rows == 1:
           return True
        elif nb_rows == 0:
           return False

    def project_from_pareo(self, db, pareo):
        cur = db.get_cur()
        cur.execute("SELECT * FROM projects WHERE pareo = %s", (pareo,))
        res = cur.fetchone()
        self._id = res[0]
        self._sector = res[1]
        self._domain = res[2]
        self._description = res[3]

def delete_projects(db):
    db.get_cur().execute("ALTER SEQUENCE projects_id_seq RESTART WITH 1;")   
    db.get_cur().execute("DELETE FROM projects;")


