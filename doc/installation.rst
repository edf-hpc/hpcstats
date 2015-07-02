Installation Guide
******************

HPCStats is only supported on GNU/Linux systems. The installation must be
performed with ``root`` user.

From sources
============

HPCStats server
---------------

First, install Python packaging system ``setuptools`` on the system. It is
probably available through the packaging system of your distribution. For
example, on Debian/Ubuntu::

    apt-get install python-setuptools

Then, download the source of HPCStats from the Git source code repository::

    wget https://github.com/edf-hpc/hpcstats/archive/master.tar.gz

Then, extract the sources and run the following command to install HPCStats
with all its dependencies::

    python setup.py install

The command actually installs both HPCStats server component itself and all its
Python modules dependencies.

Install PostgreSQL server. It is probably available through the packaging
system of your distribution. For example, on Debian/Ubuntu::

    apt-get install postgresql-server

Please note that HPCStats requires PostgreSQL version >= 9.0.

Create ``hpcstats`` system user. For example, on Debian/Ubuntu::

    adduser --system hpcstats --no-create-home --shell=/bin/sh

The ``--shell=/bin/sh`` parameter is needed to run shell commands easily using
this system user account.

Create the ``hpcstats`` PostgreSQL user/role and set its password::

    su postgres -c 'createuser --no-createdb --no-superuser --no-createrole hpcstats'
    su postgres -c "psql -c \"ALTER ROLE hpcstats WITH PASSWORD 'hpcstats';\""

Then, create the PostgreSQL database and set ``hpcstats`` as its owner::

    su postgres -c 'createdb -O hpcstats hpcstatsdb'

Finally, create the tables and constraints of this database using the SQL
script distributed with HPCStats source code::

    su hpcstats -c "psql hpcstatsdb < db/hpcstats.psql"

HPCStats is then ready to be configured and run! Please refer to the dedicated
:ref:`configuration` section for all information about the configuration files
of HPCStats.

For regular and automatic update of production data in HPCStats database, you
may want to create a cronjob for automatically running HPCStats importer
application for all clusters. Here is an example of such cronjob, in file
:file:`/etc/cron.d/hpcstats`:

.. include:: ../debian/cron.d
   :literal:

To receive the complete output of the cronjob runs by email, you can also set
the ``MAILTO`` variable. You may need to configure the local MTA to relay
emails to a external *smart* relay. For example, on Debian/Ubuntu, run::

    dpkg-reconfigure exim4-config

HPCStats agents
---------------

FSUsage agent
^^^^^^^^^^^^^

To install the ``fsusage`` agent on a supercomputer login node, install the
script::

    install contribs/fsusage /usr/local/bin/fsusage

Install the configuration file::

    mkdir /etc/hpcstats
    install conf/fsusage.conf /etc/hpcstats/fsusage.conf

Install the cronjob, in file :file:`/etc/cron.d/hpcstats-fsusage`, for example
to run every nights at 1AM::

    0 1 * * * hpcstats /usr/local/bin/fsusage

Finally, proceed with the :ref:`configuration_fsusage-agent` configuration.

Jobstats agent
^^^^^^^^^^^^^^

To install the ``jobstats`` agent on a supercomputer login node, install the
script::

    install contribs/jobstats /usr/local/bin/jobstats

Install the configuration file::

    mkdir /etc/hpcstats
    install conf/jobstats.conf /etc/hpcstats/jobstats.conf

Finally, proceed with the :ref:`configuration_jobstats-agent` configuration.

Jobstats launcher
^^^^^^^^^^^^^^^^^

To install the ``jobstats`` launcher on a supercomputer login node, install the
script::

    install contribs/launch-jobstats /usr/local/bin/launch-jobstats

Install the configuration file::

    mkdir /etc/hpcstats
    install conf/launcher.conf /etc/hpcstats/launcher.conf

Install the cronjob, in file :file:`/etc/cron.d/hpcstats-launcher`, for example
to run every nights at 1AM::

    0 1 * * * hpcstats /usr/local/bin/launch-jobstats

Finally, proceed with the :ref:`configuration_jobstats-launcher` configuration.

From Debian packages
====================

HPCStats server
---------------

Once the HPCStats packages are hosted in your internal Debian repositories,
installing HPCStats server is only a matter of::

    apt-get install hpcstats

The package automatically creates the system user, the cronjob, the PostgreSQL
user and the database. HPCStats is then ready to be configured and run! Please
refer to the dedicated :ref:`configuration` section for all information about
the configuration files of HPCStats.

HPCStats agents
---------------

To install the ``fsusage`` agent on a supercomputer login node, just run::

    apt-get install hpcstats-fsusage-agent

Then, you just have to proceed to the :ref:`configuration_fsusage-agent`
configuration.

To install the ``jobstat`` agent on a supercomputer login node, just run::

    apt-get install hpcstats-jobstat-agent

Then, you just have to proceed to the :ref:`configuration_jobstats-agent`
configuration.

To install the ``jobstat`` launcher on the HPCStats server, just run::

    apt-get install hpcstats-jobstat-launcher

Then, you just have to proceed to the :ref:`configuration_jobstats-launcher`
configuration.
