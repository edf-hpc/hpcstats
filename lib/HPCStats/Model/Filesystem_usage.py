#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

class Filesystem_usage:
    def __init__(self, fs_id = "", timestamp = "", usage = ""):

        self._fs_id = fs_id
        self._timestamp = timestamp
        self._usage = usage

    def __str__(self):
        return "Usage timestamp [%s] for fs : %s, used at %s %" % \
                   ( self._timestamp,
                     self._fs_id,
                     self._usage )

    def update_usage(self, db, cluster, fs, fs_usage):
        for i in fs_usage:
            req = """
                INSERT INTO filesystem_usage (
                            fs_id,
                            timestamp,
                            usage )
                       VALUES (
                           (SELECT id FROM filesystem 
                            WHERE mount_point = %s and cluster = %s), %s, %s ); """
            datas = (fs, cluster, i[0], i[1])
            #logging.info("Add fs %s with timestamp %s, and usage : %s", \
            #              fs, \
            #              i[0], \
            #              i[1])
            db.get_cur().execute(req, datas)
            #logging.info("req : %s", req)

