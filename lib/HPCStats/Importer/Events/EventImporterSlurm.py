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
        self._datetime_end_last_event = ""
        self._date_from_last_event = ""
        self._date_from_unfinished_event = ""
        self._datetime_start_first_unfinished_event = ""
        self._new_events =[]
        try:
            self._conn = MySQLdb.connect( host = self._dbhost,
                                          user = self._dbuser,
                                          passwd = self._dbpass,
                                          db = self._dbname,
                                          port = self._dbport )
            self._cur = self._conn.cursor(MySQLdb.cursors.DictCursor)
        except _mysql_exceptions.OperationalError as error:
            logging.error("connection to Slurm DBD MySQL failed (%s) : %s", \
		    cluster_name, \
		    error)

    def update_events(self):

        logging.debug("start updating events out of SlurmDBD")

        #Deteminate which date is more efficient to be sure to don't forget unfinished event
        logging.debug("detect which date to use to import events")
        self._get_event_date()
	
        logging.debug("getting the unfinished events")
        self._get_unfinished_events()

        logging.debug("start getting the new events out of SlurmDBD since %s",
                       self._datetime_end_last_event )
        self._get_new_events(self._datetime_end_last_event) 
        
        logging.debug("start detecting the multiple occurences of the same event (%d events in list)",
                       len(self._new_events) )
        self._delete_merge_multiple_occurences()

        #La methode save du Model Event ne permet pas d'inserer les doublons.
        #Toutefois, il est plus rigoureux d'éviter ce genre de situation, en utilisant la methode
        #self._pop_double_events.
        logging.debug("finishing the previously known events")
        self._finish_known_events()

        logging.debug("pop existing event from new event list if necessary")
        self._pop_double_events()

        logging.debug("updating the previously known events")
        self._update_unfinished_events()

        logging.debug("saving in DB all new events")
        self._save_new_events()

    def _get_event_date(self):
        self._date_from_last_event = self._get_last_end_datetime()
        self._date_from_unfinished_event = self._get_first_start_datetime_unfinished_event()

        if not self._date_from_last_event:
             self._date_from_last_event = datetime.fromtimestamp(0)
        logging.debug("get the last date of last event list = %s", self._date_from_last_event )

        if not self._date_from_unfinished_event:
             self._date_from_unfinished_event = datetime.fromtimestamp(0)
        logging.debug("get the first date of unfinished event list = %s", self._date_from_unfinished_event )

        if self._date_from_unfinished_event < self._date_from_last_event and \
           self._date_from_unfinished_event != datetime.fromtimestamp(0): 
            self._datetime_end_last_event = self._date_from_unfinished_event
            logging.debug("first date of unfinished events list is more efficient")
        else:
            self._datetime_end_last_event = self._date_from_last_event
            logging.debug("last date from finished events is more efficient")

    def _get_new_events(self, my_datetime):
        
        req = """
            SELECT time_start,
                   time_end,
                   node_name,
                   cpu_count,
                   state,
                   reason
            FROM %s_event_table
            WHERE node_name <> ''
              AND time_start >= UNIX_TIMESTAMP(%%s)
            ORDER BY time_start; """ % (self._cluster_name)
        datas = (my_datetime,)
        self._cur.execute(req, datas)

        while (1):
            row = self._cur.fetchone()
            if row == None: break
            self._new_events.extend( self._events_from_db_row(row) )

    def _events_from_db_row(self, db_row):

        events = []

        if db_row["time_end"] == 0:
            end_datetime = None
        else:
            end_datetime = datetime.fromtimestamp(db_row["time_end"])

        event = Event(  nodename = db_row["node_name"],
                        nb_cpu = db_row["cpu_count"],
                        start_datetime = datetime.fromtimestamp(db_row["time_start"]),
                        end_datetime = end_datetime,
                        event_type = self._txt_slurm_reason(db_row["state"]),
                        reason = db_row["reason"][:60])
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
		logging.debug("no event to merge : %d (%s, %s → %s)",
                               event_index,
                               event.get_nodename(),
                               event.get_start_datetime(),
                               event.get_end_datetime() )
            else:
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

    def _pop_double_events(self):
        #pop out events in double in case of using first not end event date
        if self._datetime_end_last_event == self._date_from_unfinished_event:
            event_index = 0
            for event in self._new_events:
                if event.get_end_datetime() and \
                   event.get_end_datetime() <= self._date_from_last_event:
                    self._new_events.pop(event_index)
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
# OLD STATIC METHOD
#        slurm_node_state = {
#            0:"UNKNOWN",
#            1:"DOWN",
#            4:"ERROR",
#            512:"DRAIN", 
#            513:"DRAIN+DOWN", 
#            514:"DRAIN+IDLE", 
#            515:"DRAIN+ALLOCATED", 
#            2049:"NO_RESPOND+DOWN", 
#            2492:"NODE_STATE_FAIL",
#            2561:"NO_RESPOND+DRAIN+DOWN", 
#            2562:"NO_RESPOND+DRAIN+IDLE",
#            4097:"POWER_SAVE+DOWN",
#            4609:"POWER_SAVE+DRAIN+DOWN",
#            4610:"POWER_SAVE+DRAIN+IDLE",
#            6658:"PS+NO_RES+DRAIN+IDLE",
#            18433:"PU+NO_RESPOND+DOWN",
#            18945:"PU+NO_RESPOND+DRAIN+DOWN",
#            18946:"PU+NO_RESPOND+DRAIN+IDLE",
#            32769:"MAINT+DOWN",
#            34817:"MAINT+NO_RESPOND+DOWN",
#            33280:"MAINT+DRAIN",
#            33282:"MAINT+DRAIN+IDLE",
#            33281:"MAINT+DRAIN+DOWN",
#            35329:"MAINT+NO_RESPOND+DRAIN+DOWN",
#            35330:"MAINT+NO_RESPOND+DRAIN+IDLE",
#        }
# NEW DYNAMIC METHOD
        state="";
        
        slurm_node_base={
        0x0000:"UNKNOWN",
        0x0001:"DOWN",
        0x0002:"IDLE",
        0x0003:"ALLOCATED",
        0x0004:"ERROR",
        0x0005:"MIXED",
        0x0006:"FUTURE",
        0x0007:"END"
        }
        
        slurm_node_flag1={
        0x0010:"NET",
        0x0020:"RES",
        0x0040:"UNDRAIN",
        0x0080:"CLOUD"
        }
        
        slurm_node_flag2={
        0x0100:"RESUME",
        0x0200:"DRAIN",
        0x0400:"COMPLETING",
        0x0800:"NO_RESPOND"
        }
        
        slurm_node_flag3={
        0x1000:"POWER_SAVE",
        0x2000:"FAIL",
        0x4000:"POWER_UP",
        0x8000:"MAINT"
        }
        
        base = reason_uid & 0x000F;
        
        if base==0 and reason_uid==0 :
            state=state+slurm_node_base[base];
        elif base>0 and reason_uid>0:
            state=state+slurm_node_base[base];
            
        flag1 = reason_uid & 0x00F0;
        
        if flag1/0x00F0==1 :
            flag1=flag1-0x00F0;
        
        if flag1/0x0080==1 :
            state=state+"+"+slurm_node_flag1[0x0080];
            flag1=flag1-0x0080;
            
        if flag1/0x0040==1 :
            state=state+"+"+slurm_node_flag1[0x0040];
            flag1=flag1-0x0040;
            
        if flag1/0x0020==1 :
            state=state+"+"+slurm_node_flag1[0x0020];
            flag1=flag1-0x0020;
            
        if flag1==0x0010 :
            state=state+"+"+slurm_node_flag1[0x0010];
            flag1=flag1-0x0010;
            
        flag2 = reason_uid & 0x0F00;
        
        if flag2/0x0F00==1 :
            flag2=flag2-0x0F00;
        
        if flag2/0x0800==1 :
            state=state+"+"+slurm_node_flag2[0x0800];
            flag2=flag2-0x0800;
            
        if flag2/0x0400==1 :
            state=state+"+"+slurm_node_flag2[0x0400];
            flag2=flag2-0x0400;
            
        if flag2/0x0200==1 :
            state=state+"+"+slurm_node_flag2[0x0200];
            flag2=flag2-0x0200;
            
        if flag2==0x0100 :
            state=state+"+"+slurm_node_flag2[0x0100];
            flag2=flag2-0x0100;
            
        flag3 = reason_uid & 0xF000;
        
        if flag3/0xF000==1 :
            flag3=flag3-0xF000;
        
        if flag3/0x8000==1 :
            state=state+"+"+slurm_node_flag3[0x8000];
            flag3=flag3-0x8000;
            
        if flag3/0x4000==1 :
            state=state+"+"+slurm_node_flag3[0x4000];
            flag3=flag3-0x4000;
            
        if flag3/0x2000==1 :
            state=state+"+"+slurm_node_flag3[0x2000];
            flag3=flag3-0x2000;
            
        if flag3==0x1000 :
            state=state+"+"+slurm_node_flag3[0x1000];
            flag3=flag3-0x1000;
                
        state=state.lstrip("+");
        
        if state == "":
            state = "UNASSIGNED"
            
        return state
