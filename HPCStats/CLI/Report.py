#!/usr/bin/python
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

import sys
import locale
import os
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta # debian package: python-dateutil
from mako.template import Template # debian package: python-mako
from multiprocessing import Pool

from HPCStats.CLI.ReportOptionParser import ReportOptionParser
from HPCStats.CLI.Config import HPCStatsConfig
from HPCStats.DB.DB import HPCStatsdb
from HPCStats.Model.Cluster import Cluster
from HPCStats.Finder.JobFinder import JobFinder
from HPCStats.Finder.UserFinder import UserFinder

# templates management
def get_templates_dirname():
    return os.path.dirname(__file__) + "/../../../templates/"

def get_template_filename(name):
    return get_templates_dirname() + name + ".mako"

def check_template(name):
    if not os.path.isfile(get_template_filename(name)):
        available_templates = glob.glob(get_templates_dirname() + '*.mako')
        str_available_templates = ",".join([template.split("/")[-1].split(".")[0] for template in available_templates])
        sys.exit( "error: template %s does not exists.\navailable templates are: %s." % ( name,str_available_templates ) )

# interval management
def get_interval_begin_end(step,tmp_datetime):

    """
        This function aims to calculate the exacts beginning and end
        of the step sized interval around the specified datetime.
    """

    if step == "day":
        interval_beginning = datetime(tmp_datetime.year,tmp_datetime.month,tmp_datetime.day,0,0,0)
        interval_end = datetime(tmp_datetime.year, tmp_datetime.month,tmp_datetime.day,23,59,59)
    elif step == "month":
        interval_beginning = datetime(tmp_datetime.year,tmp_datetime.month,1,0,0,0)
        # get the last day of the month using 'timedelta'
        interval_end = datetime(tmp_datetime.year, tmp_datetime.month,(tmp_datetime + relativedelta(day=31)).day, 23, 59, 59)
    elif step == "week":
        # get the number of the day inside the week
        weekday = tmp_datetime.weekday()
        # back to the 1st day of the week
        tmp2_datetime = tmp_datetime - timedelta(days=weekday)
        interval_beginning = datetime(tmp2_datetime.year,tmp2_datetime.month,tmp2_datetime.day,0,0,0)
        # upto the last day of the week
        tmp2_datetime += timedelta(days=6)
        interval_end = datetime(tmp2_datetime.year,tmp2_datetime.month,tmp2_datetime.day,23,59,59)
    return (interval_beginning, interval_end)

def get_interval_timedelta(step):

    """
        This function return a python timedelta (difference between
        2 datetime objects) of the size of the step.
    """

    if step == "day":
        return timedelta(days=1)
    elif step == "week":
        return timedelta(weeks=1)
    elif step == "month":
        return relativedelta(months=+1)


def run_interval(process_info):

    """
       Process has an array of 4 args:
         - configuration options
         - nb cpus in cluster
         - beginning interval
         - end interval
    """
    options = process_info[0]
    config = process_info[1]
    interval_beginning = process_info[2]
    interval_end = process_info[3]
    cluster = process_info[4]
    # get parameters
    step = options.interval
    template = options.template

    # Instantiate connexion to db
    db_section = "hpcstatsdb"
    dbhostname = config.get(db_section,"hostname")
    dbport = config.get(db_section,"port")
    dbname = config.get(db_section,"dbname")
    dbuser = config.get(db_section,"user")
    dbpass = config.get(db_section,"password")
    db = HPCStatsdb(dbhostname, dbport, dbname, dbuser, dbpass)
    db.bind()

    cluster = Cluster(options.cluster)
    if cluster.find() is None:
        print("cluster %s not found in DB, exiting." % (cluster.name))
        sys.exit(1)

    if options.debug:
        print "getting nb cpus on cluster %s" % (cluster.name)

    nb_cpus_cluster = cluster.get_nb_cpus(db)
    
    if options.debug:
        print "nb cpus on cluster %s: %d" % (cluster.name, nb_cpus_cluster)

    userstats = {} 
    groupstats = {}

    if options.debug:
        print "%s -> %s" % (interval_beginning, interval_end)
    
    # calculate the number of hours during the interval
    nb_hours_interval = ((interval_end - interval_beginning).days + 1) * 24

    job_finder = JobFinder(db)
    interval_jobs = job_finder.find_jobs_in_interval(cluster.name, interval_beginning, interval_end)

    cpu_time_interval = 0
    nb_jobs = 0
    #row = None

    for job in interval_jobs:

        try:
            running_datetime = job.get_running_datetime()
            if job.get_state() == 'RUNNING':
                end_datetime = datetime.now()
            else:
                end_datetime = job.get_end_datetime()
            nb_cpus = job.get_nb_procs()
            uid = job.get_uid()
            user_finder = UserFinder(db)
            user = user_finder.find(cluster.name, uid)
            username = user.get_name()
            group = user.get_department()

            # TODO: put all these mechanism into Job class
            if running_datetime < interval_beginning:
                running_datetime = interval_beginning
            if end_datetime > interval_end:
                end_datetime = interval_end
            time_job = (end_datetime - running_datetime)
            cpu_time_job_seconds = ((time_job.days * 24 * 3600) + time_job.seconds) * nb_cpus
            cpu_time_interval += cpu_time_job_seconds
            nb_jobs += 1
            # initialize user and group dicts.
            if not username in userstats:
                userstats[username] = {}
            if not group in groupstats:
                groupstats[group] = {}
            # user's group
            if 'group' not in userstats[username]:
                userstats[username]['group'] = group
            # user's jobs
            if 'jobs' in userstats[username]:
                userstats[username]['jobs'] += 1
            else:
                userstats[username]['jobs'] = 1
            # group's jobs
            if 'jobs' in groupstats[group]:
                groupstats[group]['jobs'] += 1
            else:
                groupstats[group]['jobs'] = 1
            # user's time
            if 'time' in userstats[username]:
                userstats[username]['time'] += cpu_time_job_seconds
            else:
                userstats[username]['time'] = cpu_time_job_seconds
            # group's time
            if 'time' in groupstats[group]:
                groupstats[group]['time'] += cpu_time_job_seconds
            else:
                groupstats[group]['time'] = cpu_time_job_seconds

            if options.debug:
                print "debug: (%s - %s) * %d -> %s" % (end_datetime, running_datetime, nb_cpus, cpu_time_job_seconds)

        except UserWarning as w:
            #print "Warning:", w
            continue

    # nb accounts
    nb_accounts = cluster.get_nb_accounts(db, interval_beginning)

    # active users
    nb_active_users = cluster.get_nb_active_users(db, interval_beginning, interval_end)

    cpu_time_hours = cpu_time_interval / 3600
    if options.debug:
        print "debug: nb_cpus_cluster: %d nb_hours_interval: %d" % (nb_cpus_cluster, nb_hours_interval)

    cpu_time_available = nb_cpus_cluster * nb_hours_interval
    utilisation_rate = (float(cpu_time_hours) / cpu_time_available) * 100
    if step == "day":
        str_date = interval_beginning.strftime("%d/%m/%Y")
        str_interval = "-"
    elif step == "week":
        str_date = interval_beginning.strftime("week %W %Y")
        str_interval = interval_beginning.strftime("%d/%m/%Y -> ") + interval_end.strftime("%d/%m/%Y")
    elif step =="month":
        str_date = interval_beginning.strftime("%Y/%m")
        str_interval = interval_beginning.strftime("%d/%m/%Y -> ") + interval_end.strftime("%d/%m/%Y")
    
    # append calculated results into a list
    result = [ str_date, str_interval, nb_jobs, cpu_time_hours, cpu_time_available, nb_accounts, nb_active_users, userstats, groupstats ]

    db.unbind()
    
    return result


def main(args=sys.argv):

    # Command line argument parser
    usage = "usage: %prog [options] (-c|--cluster) <cluster> [-i,--interval (day|week|month)] [-t,--template <template>]"
    parser = ReportOptionParser(usage)
    (options, args) = parser.parse_args(args[1:])

    if not options.cluster:
        parser.error("<cluster> should be specified")
 
    # Config file argument parser
    config = HPCStatsConfig(options)

    # locale to format numbers
    locale.setlocale(locale.LC_ALL, 'fr_FR')
    # TODO: load locale output of the environment

    if (options.debug):
        # dump entire config file
        for section in config.sections():
            print section
            for option in config.options(section):
                print " ", option, "=", config.get(section, option)

    # Instantiate connexion to db
    db_section = "hpcstatsdb"
    dbhostname = config.get(db_section,"hostname")
    dbport = config.get(db_section,"port")
    dbname = config.get(db_section,"dbname")
    dbuser = config.get(db_section,"user")
    dbpass = config.get(db_section,"password")
    db = HPCStatsdb(dbhostname, dbport, dbname, dbuser, dbpass)
    
    if (options.debug):
        print "db information %s %s %s %s %s" % db.infos()

    if (options.debug):
        print "→ running on cluster %s with interval %s" % (options.cluster, options.interval)

    # check if specified template is available
    #check_template(options.template)

    # get parameters
    step = options.interval
    template = options.template

    db.bind()
    
    cluster = Cluster(options.cluster)
      
    # check if cluster really exists
    if not cluster.exists_in_db(db):
        sys.exit("error: cluster %s does not exist in database. Available clusters are: %s."
                   % (cluster, ",".join(available_clusters)) )

    if options.debug:
        print "main: getting nb cpus on cluster %s" % (cluster.name)

    # get the total number of cpus inside the cluster
    nb_cpus_cluster = cluster.get_nb_cpus(db)

    results = []

    # get datetime of the first job
    min_datetime = cluster.get_min_datetime(db)
    #min_datetime = datetime(2011,5,1,0,0,0)
    max_datetime = datetime.now()
    tmp_datetime = min_datetime
    db.unbind()
    
    userstats_global = {}
    groupstats_global = {}
    processes_args = []

    # construct intervals with process information mapping
    while tmp_datetime < max_datetime:

        # get the exacts beginning and end of the step sized interval
        # around the tmp datetime
        (begin,end) = get_interval_begin_end(step,tmp_datetime)

        # construct an array of args for each process/interval
        process_info = []
        #process_info.append(options)
        #process_info.append(config)
        #process_info.append(cluster)
        #process_info.append(begin)
        #process_info.append(end)

        process_info.append(options)
        process_info.append(config)
        process_info.append(begin)
        process_info.append(end)
        process_info.append(cluster)

        # finally appends this append to the global array
        processes_args.append(process_info)
        
        # going to next interval
        interval = get_interval_timedelta(step)
        tmp_datetime += interval

    if options.debug:
        print processes_args

    # launch processes with their corresponding arguments
    parallel = True 
    processes_results = []
    if parallel:
        pool = Pool(4)
        processes_results = pool.map(run_interval, processes_args)
    else:
        for process_info in processes_args:
            process_results = run_interval(process_info)    
            processes_results.append(process_results)
    
    # then get results
    for result in processes_results:
        str_date = result[0]
        groupstats = result.pop()
        userstats = result.pop()
        userstats_global[str_date] = userstats
        groupstats_global[str_date] = groupstats
        results.append(result)

    if options.debug:
        print "debug: usersstats", userstats_global
        print "debug: groupsstats", groupstats_global

    # print results using template
    mytemplate = Template( filename=get_template_filename(template),
                           input_encoding='utf-8',
                           output_encoding='utf-8',
                           default_filters=['decode.utf8'],
                           encoding_errors='ignore'
                         )
    print mytemplate.render(cluster=cluster,step=step,results=results,userstats_global=userstats_global,groupstats_global=groupstats_global)

