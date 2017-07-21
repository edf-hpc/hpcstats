.. _usage:

Usage guide
***********

Synopsis
========

**hpcstats** [-h --help] [-c --conf *pathname*] [-d --debug] *action* *options* 

Description
===========

HPCStats is a software to manage a relational database which centralizes the
production usage data of various HPC supercomputers. This command can import
new production data, check data sources availability, modify the content of
the database and generate usage reports with statistics.

Actions
=======

Available actions:

  import
    Import new production data and update database incrementally.

  check
    Check production data sources availability.

  modify
    Modify the content of the database.

  report
    Generate usage report with statistics.

Global options
==============

    -h, --help      Show help message and exit.
    -c FILE, --conf=FILE
                    Alternative configuration file. Default is
                    **/etc/hpcstats/hpcstats.conf**.
    -d, --debug     Enable debug output.
    --batch-mode    Set output in batch mode. The outputs are sent to local
                    syslog server, the standard and errors outputs only get the
                    messages at the warning level and over. This mode is
                    particularly usefull for cronjobs because the warnings and
                    errors are sent by email when needed and administrators get
                    all output in syslog for further diagnosis.

Import options
==============

Required arguments for `import` action:

    --cluster=CLUSTER  The name of the cluster from which the data will be
                    imported. Special value **all** can be used to import data
                    from all configured supercomputers.

    --since-event=DATE Import events starting from this date for new clusters. The
                    date must be formatted like YYYY-MM-DD. Default is
                    **1970-01-01**.

    --since-jobid=ID   Import jobs starting from this internal job id for new
                    clusters. The job id must an integer. Default is **-1**.

Check options
=============

Required arguments for `check` action:

    --cluster=CLUSTER  The name of the cluster for which the data sources will
                    be checked. Special value **all** can be used to check
                    data sources for all configured supercomputers.

Modify options
==============

Optional arguments for `modify` action:

    --business-code=CODE  The business code to modify.
    --project-code=CODE  The project code to modify.
    --set-description=DESC  The new description of the business code or the
                    project.
    --set-domain=DOMAIN  The new domain of the project.
    --new-domain=DOMAIN  The new domain key to create in database.
    --domain-name=NAME  The new domain name to create in database.

Please refer to :ref:`examples` section to see the possible combinations of the
parameters.

Report options
==============

**Disclaimer:** This feature must be considered as very experimental!

Required arguments for `report` action:

    --cluster=CLUSTER  The name of the cluster for which the report is
                    generated.

Optional arguments for `report` action:

    --interval=ITL  The interval used in the report. Default is **day**.
    --template=TPL  The template to use for the report. Default is **csv**.

.. _examples:

Examples
========

Import production data of supercomputer HPC-A::

    hpcstats import --cluster=HPC-A

Import production data of all supercomputers::

    hpcstats import --cluster=all

Check supercomputer HPC-B data sources availablity::

    hpcstats check --cluster=HPC-B

Set new description to business code B1::

    hpcstats modify --business-code=B1 --set-description='new description B1'

Set new description to project P1::

    hpcstats modify --project-code=P1 --set-description='new description P1'

Set new domain D1 to project P1::

    hpcstats modify --project-code=P1 --set-domain=D1

Set create new domain D2::

    hpcstats modify --new-domain=D2 --domain-name='domain name D2'
