#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2015 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of HPCStats.
#
# HPCStats is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with HPCStats. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

import mock
import re

# the requests and results are then defined by tests themselves.
PG_REQS = dict()

class PgReq(object):

    """Class for easy manipulation of fake PostgreSQL requests use by following
       Mock Psycopg2 classes, for testing purpose only.
    """

    def __init__(self, req):

        self.req = req

        # The assoc attribute is a list of tuples, each tuple being composed
        # of a tuple of params and a list of results. Each result is also a
        # list of fields. Ex:
        #
        # [
        #   (
        #     ( param1, param2 ),
        #     [ [ res1_field1, res1_field2 ], [ res2_field1, res2_field2 ] ]
        #   ),
        #   (
        #     ( param1, param2 ),
        #     [ [ res1_field1, res1_field2 ], [ res2_field1, res2_field2 ] ]
        #   )
        # ]
        self.assocs = []

    def set_assoc(self, params, result):
        """Set an association params/result to the PgReq."""

        if self.assocs is None:
            self.assocs = []
        id_assoc = 0
        # If there is already an assoc with the same params, remove it first.
        for assoc in self.assocs:
            if params == assoc[0]:
                self.assocs.pop(id_assoc)
                break
            id_assoc += 1
        self.assocs.append( ( params, result ) )

def init_reqs():

    #
    # User
    #

    req = "SELECT userhpc_id " \
          "FROM Userhpc " \
          "WHERE userhpc_login = %s"

    PG_REQS['find_user'] = PgReq(req)

    req = "INSERT INTO Userhpc \( userhpc_login, " \
                                 "userhpc_firstname, " \
                                 "userhpc_name, " \
                                 "userhpc_department\) " \
                       "VALUES \( %s, %s, %s, %s\) " \
                    "RETURNING userhpc_id"

    PG_REQS['insert_user'] = PgReq(req)

    #
    # Account
    #

    req = "SELECT account_uid " \
            "FROM Account " \
           "WHERE userhpc_id = %s " \
             "AND cluster_id = %s"

    PG_REQS['existing_account'] = PgReq(req)

    req = "SELECT account_uid, " \
                 "account_gid, " \
                 "account_creation, " \
                 "account_deletion " \
            "FROM Account " \
           "WHERE userhpc_id = %s " \
             "AND cluster_id = %s"

    PG_REQS['load_account'] = PgReq(req)

    req = "SELECT Userhpc.userhpc_id, " \
                 "userhpc_login, " \
                 "userhpc_name, " \
                 "userhpc_firstname, " \
                 "userhpc_department, " \
                 "account_uid, " \
                 "account_gid, " \
                 "account_creation " \
            "FROM Userhpc, " \
                 "Account " \
           "WHERE Account.cluster_id = %s " \
             "AND Account.userhpc_id = Userhpc.userhpc_id " \
             "AND Account.account_deletion = NULL"

    PG_REQS['get_unclosed_accounts'] = PgReq(req)

    req = "SELECT account_uid " \
            "FROM Account " \
           "WHERE cluster_id = %s"

    PG_REQS['nb_existing_accounts'] = PgReq(req)

    #
    # Cluster
    #

    req = "INSERT INTO Cluster \( cluster_name \) " \
          "VALUES \( %s \) "\
          "RETURNING cluster_id"

    PG_REQS['save_cluster'] = PgReq(req)


    req = "SELECT cluster_id " \
            "FROM Cluster " \
           "WHERE cluster_name = %s"

    PG_REQS['find_cluster'] = PgReq(req)

    #
    # Node
    #

    req = "INSERT INTO Node \( node_name, " \
                              "cluster_id, " \
                              "node_model, " \
                              "node_partition, " \
                              "node_nbCpu, " \
                              "node_memory, " \
                              "node_flops \) " \
           "VALUES \( %s, %s, %s, %s, %s, %s, %s \) " \
           "RETURNING node_id"

    PG_REQS['save_node'] = PgReq(req)

    req = "SELECT node_id " \
          "FROM Node " \
          "WHERE node_name = %s " \
            "AND cluster_id = %s"

    PG_REQS['find_node'] = PgReq(req)

    #
    # Business
    #

    req = "SELECT business_code " \
            "FROM Business "\
           "WHERE business_code = %s"

    PG_REQS['existing_business'] = PgReq(req)

    #
    # Event
    #
    req = "SELECT MAX\(event_end\) AS last " \
            "FROM Event " \
           "WHERE cluster_id = %s"

    PG_REQS['get_end_last_event'] = PgReq(req)

    req = "SELECT MIN\(event_start\) " \
            "FROM Event " \
           "WHERE cluster_id = %s " \
             "AND event_end IS NULL"

    PG_REQS['get_start_oldest_unfinised_event'] = PgReq(req)

    #
    # Job
    #
    req = "SELECT MIN\(job_batch_id::integer\) AS last_id " \
            "FROM Job " \
           "WHERE cluster_id = %s " \
             "AND \(job_start IS NULL " \
              "OR job_end IS NULL\)"

    PG_REQS['get_batchid_oldest_unfinished'] = PgReq(req)

    req = "SELECT MAX\(job_batch_id::integer\) AS last_id " \
            "FROM Job "  \
           "WHERE cluster_id = %s"

    PG_REQS['get_batchid_last'] = PgReq(req)

    #
    # Domain
    #

    req = "SELECT domain_id FROM Domain WHERE domain_id = %s"

    PG_REQS['exist_domain'] = PgReq(req)

    req = "INSERT INTO Domain \( domain_id, domain_name \) " \
          "VALUES \( %s, %s \)"

    PG_REQS['save_domain'] = PgReq(req)

    #
    # Project
    #

    req = "SELECT project_id FROM Project WHERE project_code = %s"

    PG_REQS['find_project'] = PgReq(req)

    req = "SELECT project_code, " \
                 "project_description, " \
                 "domain_id " \
             "FROM Project " \
             "WHERE project_id = %s"

    PG_REQS['load_project'] = PgReq(req)

    req = "INSERT INTO Project \( project_code, " \
                                 "project_description, "\
                                 "domain_id \) "\
          "VALUES \( %s, %s, %s \) "\
          "RETURNING project_id"

    PG_REQS['save_project'] = PgReq(req)


class MockPsycopg2(object):

    """Class with static methods to mock all used functions in psycogp2
       module
    """

    def __init__(self):
        pass

    @staticmethod
    def connect(conn):
        """Mock of psycopg2.connect()"""
        return MockPsycopg2Connect()

class MockPsycopg2Connect(object):

    def __init__(self):

        self._cursor = MockPsycopg2Cursor()

    def cursor(self):

        return self._cursor

    def commit(self):

        pass

    def close(self):

        pass

class MockPsycopg2Cursor(object):

    def __init__(self):

        self.ref = None
        self.idx = 0

    def execute(self, req, params=None):

        self.ref = None
        req = req.replace('\n','').strip()
        req_clean = re.sub(' +',' ',req)
        print("clean: %s" % (req_clean))
        for reqref, req in PG_REQS.iteritems():
            print("req  : %s" % (req.req))
            result = re.match(req.req, req_clean)
            if result:
                print("match with %s!" % (reqref))
                print("params: %s" % (str(params)))
                self.id_assoc = id_assoc = 0
                self.ref = reqref
                self.idx = 0

                for assoc in req.assocs:
                    print("testing params %s" % (str(assoc[0])))
                    if assoc[0] == params:
                        print("found assoc at %s!" % (str(id_assoc)))
                        self.id_assoc = id_assoc
                        break
                    id_assoc += 1
                break

    def fetchall(self):
        if self.ref is not None and \
           len(PG_REQS[self.ref].assocs) > 0:
            return PG_REQS[self.ref].assocs[self.id_assoc][1]
        else:
            return []

    def fetchone(self):
        if self.ref is not None and \
           len(PG_REQS[self.ref].assocs) > 0:
            results = PG_REQS[self.ref].assocs[self.id_assoc][1]
            if len(results) > self.idx:
                result = results[self.idx]
                self.idx += 1
                return result
        return None

    @property
    def rowcount(self):
        if self.ref is not None and \
           len(PG_REQS[self.ref].assocs) > 0:
            return len(PG_REQS[self.ref].assocs[self.id_assoc][1])
        else:
            return 0

def mock_psycopg2():

    psycopg2_m = mock.Mock()
    psycopg2_m.connect.side_effect = MockPsycopg2.connect
    return psycopg2_m
