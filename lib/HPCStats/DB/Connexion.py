#!/usr/bin/python
# -*- coding: utf-8 -*-    
import psycopg2
import MySQLdb
import ldap
import re
import csv
import glob
import time
import psycopg2
from LdapObjpkg.LdapObj import LdapObj



class Connexion():  
   
    
    def __init__(self, config) :
        self.config = config
           
    
    def build_database_mysql_conf(self):
        """recuperere les donnees de connection a
        la base de donnees type slurm a partir du conf.ini"""        
        DATABASE2 = {
            'HOST':    self.conf.SlurmDatabasehost,
            'NAME':    self.conf.SlurmDatabasename,
            'USER':    self.conf.SlurmDatabaseuser,
            'PASSWORD': self.conf.SlurmDatabasepassword}
        return DATABASE2


    def build_database_supervision(self):
        """recuperere les donnees de connection a
        la base de donnees supervision a partir du con.ini"""
        DATABASE = {
            'HOST':    self.conf.SupervisionDatabasehost ,
            'NAME':    self.conf.SupervisionDatabasename ,
            'USER':    self.conf.SupervisionDatabaseuser ,
            'PASSWORD':
            self.conf.SupervisionDatabasepassword,
            'PORT':   self.conf.SupervisionDatabaseport, }
        return DATABASE

    
    def connection_mysql(self):
        """connection a la base de donnees stockees type
        slurm a partir du conf.ini"""
        DATABASE2 = self.build_database_mysql_conf()
        try:
            conn = MySQLdb.connect(host=DATABASE2["HOST"],
            user=DATABASE2["USER"], db=DATABASE2["NAME"],
            passwd=DATABASE2['PASSWORD'] % DATABASE2)
            cur = conn.cursor(MySQLdb.cursors.DictCursor)
            print  "connection done"
            return cur, conn
        except:
            print "connection problem"


    
    def supervision_connection(self):
        """connection a la base supervision"""
        DATABASE = self.build_database_supervision()
        print DATABASE
        conn = psycopg2.connect("host = %(HOST)s dbname= %(NAME)s user= %(USER)s password= %(PASSWORD)s" % DATABASE)
        cur = conn.cursor()
        return cur, conn


    def connection_simple(self):
        """connection simple au server hote de supervision"""
        DATABASE = self.build_database_supervision()
        conn = psycopg2.connect("host = %(HOST)s  user= %(USER)s password= %(PASSWORD)s" % DATABASE)
        cur = conn.cursor()
        return cur, conn 

    
    def check_connection(self):
        try :
            self.supervision_connection()
            print "connection supervision reussi"
        except :
            "tentative de connection echoue"
            
    def database_dump(self):
        """ creation de la page"""
        conn = self.connection_simple()[1]
        cur = conn.cursor()
        data = self.conf.SupervisionDatabasename
        conn.set_isolation_level(0)
        SQL = "CREATE DATABASE " + str(data) + " ;"
        cur.execute(SQL)
        conn.commit()
        cur.close()
        conn.close()
        conn = self.supervision_connection()[1]
        cur = conn.cursor()
        filin = open("./configuration/db.psql", 'r')
        temp = ""
        for li in filin:
            print li
            try:
                if li.count(";") == 1:
                    li = li + temp
                    cur.execute(li)
                    temp = ""
                else:
                    temp = li + temp
            except:
                print "error in database"

        conn.commit()
        cur.close()
        conn.close()

    def ldap(self):
        ldapdatas = {
          "server": self.conf.Ldapserver,
          "port": self.conf.Ldapport, 
          "dn": self.conf.Ldapdn,
          "baseDN": self.conf.Ldapbasedn,
          "pw": self.conf.Ldappw,
          "retrieve_attributes": self.conf.Ldapretrieveattributes.split(','),          
          "search_filter_generic": "",                               
          "bind_mode": "",
          "anonymous_connection": int(self.conf.Ldapanonymousconnection),
          "safe_mode": int(self.conf.Ldapsafemode),          
          }
 
        h = LdapObj(**ldapdatas)
        h.connect() 
        h.bind() 
        reponse = h.searchObj() 
        print "ma reponse", reponse 
        h.unbind()    
