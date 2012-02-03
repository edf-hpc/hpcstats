#!/usr/bin/python
# -*- coding: utf-8 -*-

from HPCStats.Model.User import User
import ldap
import xlrd
from datetime import date

class UserImporterXLSLdap(object):

    def __init__(self, db, config, cluster_name):
        self._db = db
        self._conf = config
        self._cluster_name = cluster_name

        ldap_section = self._cluster_name + "/ldap"
        xls_section = self._cluster_name + "/xls"

        self._ldapurl = config.get(ldap_section,"url")
        self._ldapbase = config.get(ldap_section,"basedn")
        self._ldapdn = config.get(ldap_section,"dn")
        self._ldappass = config.get(ldap_section,"password")
        self._ldapconn = ldap.initialize(self._ldapurl)
        self._ldapconn.simple_bind(self._ldapdn, self._ldappass)

        self._xlsfile = config.get(xls_section,"file")
        self._xlssheetname = config.get(xls_section,"sheet")
        self._xlsworkbook = xlrd.open_workbook(self._xlsfile)
        self._xlssheet = self._xlsworkbook.sheet_by_name(self._xlssheetname)
        
    def get_all_users(self):
        users = []
        # start from row 6 in xls file
        previous_user = None
        for rownum in range(6,self._xlssheet.nrows):
            try:
                xls_row = self._xlssheet.row_values(rownum)
                user = self.user_from_xls_row(xls_row) 
                
                if user.get_cluster() == self._cluster_name and (not previous_user or not user == previous_user):
                    
                    [uid, gid] = self.get_ids_from_ldap(user)
                    user.set_uid(uid)
                    user.set_gid(gid)
                    
                    users.append(user)
                    previous_user = user

            except TypeError as e:
                #print "Error in %s: %s" % (self.__class__.__name__, e)
                continue

        return users;

    def get_ids_from_ldap(self, user):
        r = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"uid="+user.get_login(),["uidNumber","gidNumber"])
        try:
            attrib_dict = r[0][1]
            uid = int(attrib_dict['uidNumber'][0])
            gid = int(attrib_dict['gidNumber'][0])
            return [uid, gid]
        except IndexError:
            print "Error in %s: login %s (%s) not in LDAP" % \
                   ( self.__class__.__name__,
                     user.get_login(),
                     user.get_name() )
            # loosely search for user with the same name in LDAP
            r = self._ldapconn.search_s(self._ldapbase,ldap.SCOPE_SUBTREE,"cn="+user.get_name(),["uid","uidNumber","gidNumber"])
            if len(r) > 0:
                attrib_dict = r[0][1]
                login = attrib_dict['uid'][0]
                uid = int(attrib_dict['uidNumber'][0])
                gid = int(attrib_dict['gidNumber'][0])
                print "Info in %s: login %s not in LDAP but found user %s with login %s" % \
                   ( self.__class__.__name__,
                     user.get_login(),
                     user.get_name(),
                     login )
            return [-1, -1]

    def user_from_xls_row(self, xls_row):

        login = xls_row[1].encode('utf-8').strip()
        if login == "":
            raise TypeError, "login is empty"
        # workaround for a problem on last row
        if type(xls_row[2]) == int:
            raise TypeError, "firstname box is an int instead of {str, unicode}"
        firstname = xls_row[2].encode('utf-8').strip().capitalize()
        lastname = xls_row[3].encode('utf-8').strip().upper()
        department = xls_row[4].encode('utf-8').strip().upper()
        if department == "":
            department = "UNKNOWN"
        project = xls_row[12].encode('utf-8').strip().upper()
        email = xls_row[14].encode('utf-8').strip().lower()
        cluster = xls_row[16].encode('utf-8').strip().lower()
        creation = xls_row[5]
        if type(creation) == float and creation != 1.0:
            # see: https://secure.simplistix.co.uk/svn/xlrd/trunk/xlrd/doc/xlrd.html#xldate.xldate_as_tuple-function
            (year,month,day,hour,minute,second) = xlrd.xldate_as_tuple(creation, 0)
            creation_date = date(year, month, day)
        else :
            creation_date = None
        deletion = xls_row[6]
        if type(deletion) == float and deletion != 1.0:
            (year,month,day,hour,minute,second) = xlrd.xldate_as_tuple(deletion, 0)
            deletion_date = date(year, month, day)
        else :
            deletion_date = None

        user = User( name = firstname + " " + lastname,
                     login = login,
                     cluster = cluster,
                     department = department,
                     creation_date = creation_date,
                     deletion_date = deletion_date )
        return user

