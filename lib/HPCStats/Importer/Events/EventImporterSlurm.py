#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb
import _mysql_exceptions
import logging
from datetime import datetime
from ClusterShell.NodeSet import NodeSet
from HPCStats.Importer.Events.EventImporter import EventImporter
from HPCStats.Model.Event import Event

class EventImporterSlurm(EventImporter):

    def __init__(self, db, config, cluster_name):

        EventImporter.__init__(self, db, config, cluster_name)

        slurm_section = self._cluster_name + "/slurm"

        self._dbhost = config.get(slurm_section,"host")
        self._dbport = int(config.get(slurm_section,"port"))
        self._dbname = config.get(slurm_section,"name")
        self._dbuser = config.get(slurm_section,"user")
        self._dbpass = config.get(slurm_section,"password")
        try:
            self._conn = MySQLdb.connect( host = self._dbhost,
                                          user = self._dbuser,
                                          passwd = self._dbpass,
                                          db = self._dbname,
                                          port = self._dbport )
        except _mysql_exceptions.OperationalError as e:
            logging.error("connection to Slurm DBD MySQL failed: %s", e)
            raise RuntimeError
        self._cur = self._conn.cursor(MySQLdb.cursors.DictCursor)

    def update_events(self):

        logging.debug("start updating events out of SlurmDBD")

        datetime_end_last_event = self._get_last_end_datetime()
        # if None set to 1970-01-01 the beginning of ages for SlurmDBD
        if not datetime_end_last_event:
            datetime_end_last_event = datetime.fromtimestamp(0)

        logging.debug("getting the unfinished events")
        self._get_unfinished_events()

        logging.debug("start getting the new events out of SlurmDBD since %s",
                       datetime_end_last_event )

        req = """
            SELECT time_start,
                   time_end,
                   node_name,
                   cluster_nodes,
                   state
            FROM %s_event_table
            WHERE node_name <> ''
              AND time_start >= UNIX_TIMESTAMP(%%s)
            ORDER BY time_start; """ % (self._cluster_name)
        datas = (datetime_end_last_event,)
        self._cur.execute(req, datas)

        self._new_events = []

        while (1):
            row = self._cur.fetchone()
            if row == None: break
            self._new_events.extend( self._events_from_db_row(row) )
       
        logging.debug("start detecting the multiple occurences of the same event (%d events in list)",
                       len(self._new_events) )
                
        self._delete_merge_multiple_occurences()

        logging.debug("finishing the previously known events")
        self._finish_known_events()

        logging.debug("updating the previously known events")
        self._update_unfinished_events()

        logging.debug("saving in DB all the new events")
        self._save_new_events()

    def _events_from_db_row(self, db_row):

        events = []

        if db_row["time_end"] == 0:
            end_datetime = None
        else:
            end_datetime = datetime.fromtimestamp(db_row["time_end"])

        event = Event(  nodename = db_row["node_name"],
                        start_datetime = datetime.fromtimestamp(db_row["time_start"]),
                        end_datetime = end_datetime,
                        event_type = self._txt_slurm_reason(db_row["state"]))
        events.append(event)

        return events

    def _delete_merge_multiple_occurences(self):

        event_index = 0
        nb_events = len(self._new_events)

        # iterate over the list of new events
        while event_index < nb_events:

            event = self._new_events[event_index]
            # boolean to known whether we will go at the next event
            # for the the iteration of the main loop
            goto_next_event = True

            # find the next event in the list for the same node
            next_event_index = event_index + 1

            try:
                while next_event_index < nb_events and \
                      self._new_events[next_event_index].get_nodename() != event.get_nodename():
                    next_event_index += 1
            except IndexError:
                logging.error("trying to access to index %d of list with %d items",
                               next_event_index,
                               nb_events )

            # if search index is at the end of the list, next event has not been found
            if next_event_index == nb_events:
                logging.debug("did not found the next event of %d (%s)",
                               event_index,
                               event.get_nodename() )
            else:
                #print "Debug %s: found the next event of %d (%s) at index %d" % \
                #          ( self.__class__.__name__,
                #            event_index,
                #            event.get_nodename(),
                #            next_event_index )

                next_event = self._new_events[next_event_index]

                if event.get_end_datetime() == next_event.get_start_datetime() and \
                     event.get_event_type() == next_event.get_event_type():
                    logging.debug("merging %s (%d) with %s (%d)",
                                   event,
                                   event_index,
                                   next_event,
                                   next_event_index )
                    event.set_end_datetime(next_event.get_end_datetime())
                    self._new_events.pop(next_event_index)
                    nb_events -= 1
                    goto_next_event = False

            if goto_next_event:
                event_index += 1

    def _txt_slurm_reason(self, reason_uid):

        # From slurm/slurm.h.in in v2.3.2:
        #enum node_states {
        #        NODE_STATE_UNKNOWN,     /* node's initial state, unknown */     -> 0x0000
        #        NODE_STATE_DOWN,        /* node in non-usable state */          -> 0x0001
        #        NODE_STATE_IDLE,        /* node idle and available for use */   -> 0x0002
        #        NODE_STATE_ALLOCATED,   /* node has been allocated to a job */  -> 0x0003
        #        NODE_STATE_ERROR,       /* node is in an error state */         -> 0x0004
        #        NODE_STATE_MIXED,       /* node has a mixed state */            -> 0x0005
        #        NODE_STATE_FUTURE,      /* node slot reserved for future use */ -> 0x0006
        #        NODE_STATE_END          /* last entry in table */               -> 0x0007
        #};
        ##define NODE_STATE_BASE       0x00ff
        ##define NODE_STATE_FLAGS      0xff00
        ##define NODE_RESUME           0x0100    /* Restore a DRAINED, DRAINING, DOWN
        #                                         * or FAILING node to service (e.g.
        #                                         * IDLE or ALLOCATED). Used in
        #                                         * slurm_update_node() request */
        ##define NODE_STATE_DRAIN      0x0200    /* node do not new allocated work */
        ##define NODE_STATE_COMPLETING 0x0400    /* node is completing allocated job */
        ##define NODE_STATE_NO_RESPOND 0x0800    /* node is not responding */
        ##define NODE_STATE_POWER_SAVE 0x1000    /* node in power save mode */
        ##define NODE_STATE_FAIL       0x2000    /* node is failing, do not allocate
        #                                         * new work */
        ##define NODE_STATE_POWER_UP   0x4000    /* restore power or otherwise
        #                                         * configure a node */
        ##define NODE_STATE_MAINT      0x8000    /* node in maintenance reservation */

        # Values seen in SlurmDBD:
        #mysql> SELECT DISTINCT(state) FROM ivanoe_event_table ORDER BY state;
        #+-------+
        #| state |
        #+-------+
        #|     0 | -> 0x0000 : UNKNOWN
        #|     1 | -> 0x0001 : DOWN
        #|   512 | -> 0x0200 : DRAIN
        #|   513 | -> 0x0201 : DRAIN + DOWN
        #|   514 | -> 0x0202 : DRAIN + IDLE
        #|   515 | -> 0x0203 : DRAIN + ALLOCATED
        #|  2049 | -> 0x0801 : NO_RESPOND + DOWN
        #|  2561 | -> 0x0A01 : NO_RESPOND + DRAIN + DOWN
        #|  2562 | -> 0x0A02 : NO_RESPOND + DRAIN + IDLE
        #+-------+
        slurm_node_state = {
            0:"UNKNOWN",
            1:"DOWN", 
            512:"DRAIN", 
            513:"DRAIN+DOWN", 
            514:"DRAIN+IDLE", 
            515:"DRAIN+ALLOCATED", 
            2049:"NO_RESPOND+DOWN", 
            2561:"NO_RESPOND+DRAIN+DOWN", 
            2562:"NO_RESPOND+DRAIN+IDLE", 
        }
        return slurm_node_state[reason_uid]

