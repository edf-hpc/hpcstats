HPCStats
========

HPCStats is an EDF tool for retrieving, storing and centralizing information
from supercomputers. Those information retrieved are useful for the
developpement of statistical indicators.

Installation
------------

# Requirements

HPCStats is tested and validated on Debian 6.
If there are not yet installed on the HPCStats server, please install
following packages:

```
# apt-get install postgresql-8.4 \
                  postgresql-client-8.4 \
                  clustershell \
                  python-psycopg2 \
                  python-mysqldb \
                  python-ldap \
                  python-xlrd \
                  python-paramiko
```

# Quick installation from source

Create hpcstats local user:

`# adduser --disabled-password --gecos '' hpcstats`

* Create PostgreSQL user:

```
root # su - postgres
postgres $ createuser --createdb --pwprompt hpcstats
```

* Download last version of HPCStats and copy it on working directory

* Create hpcstatsdb with hpcstats role:

```
root # su - hpcstats
hpcstats $ createdb hpcstatsdb
```

* Create database scheme:

`hpcstats $ psql hpcstatsdb < ${HPCSTATS_DIR}/db/hpcstats.psql`

* Copy architecture file on working directory and modify it:

```
hpcstats $ cp ${HPCSTATS_DIR}/conf/architecture.conf ~/architecture.conf
hpcstats $ chmod 0600 ~/architecture.conf
hpcstats $ $EDITOR ~/architecture.conf
```

* Copy configuration file on working directory and modify it:

```
hpcstats $ cp ${HPCSTATS_DIR}/hpcstats/conf/hpcstats.conf ~/.hpcstats.conf
hpcstats $ chmod 0600 ~/.hpcstats.conf
hpcstats $ $EDITOR ~/.hpcstats.conf
```

Usage
-----

* To launch hpcstats script, first export pythonpath and launch supervision.py
script with correct option:

```
hpcstats $ export PYTHONPATH=${HPCSTATS_DIR}/lib
hpcstats $ ${HPCSTATS_DIR}/scripts/supervision.py --name ${CLUSTER} \
           --arch --users --jobs --events >>${HPCSTATS_DIR}/hpcstats.log
```

First launch could be very long depend of powerfull of your HPCStats server
because he need to import all datas from scheduler database.

This first quick installation doesn't provide all OCRI statistics indicators.
If you want to install files systems connectors, end-to-end disponibility
connectors or contexte connectors please see the full documentation.

Tests
-----

To run all the unit tests, simply run the following command:

```
nosetests
```

To verify integrity of datas, you can connect to hpcstatsdb and check users and
jobs tables with following command for exemple:

```
# su - hpcstats
hpcstats $ psql -d hpcstatsdb
hpcstatsdb=> select * from users limit 10;
hpcstatsdb=> select * from jobs order by submission_datetime desc limit 10;
```

Or you can install OCRI web application and test indicators.

Documentation
-------------

Full documentation is centralise on file
"procedure_technique_installation_hpcstats_v3.0.pdf"

Authors
-------

Rémi Palancher		    <remi.palancher@edf.fr>
Stéphan Gorget		    <stephan.gorget@edf.fr>

Contributors
------------

Loic Laureote
Rodrigue Nsiangani
Nali Andriana		    <nalimanaja.andrianavony@bull.net>
Gaston Samarou
Damien Balima
Jean-Baptiste Lesenne	    <jean-baptiste.lesenne@bull.net>
