.. _configuration:

Configuration
*************

All the configuration files of the HPCStats components are formatted like an
INI file with sections between square brakets (``[]``) and parameter/value
pairs separated by an equal sign (``=``).

The various sections and parameters of these files are fully documented in the
following sub-sections.

.. _configuration_server:

HPCStats server
===============

The configuration file of the HPCStats server component is located at
:file:`/etc/hpcstats/hpcstats.conf`.

The first section is ``clusters`` (*required*). It must contain the following
parameter:

* ``clusters`` (*required*): a list of cluster name separated by commas (``,``)
  The list is then considered as the official list of clusters supported by
  HPCStats server component.

The ``hpcstatsdb`` section (*required*) contains all the parameters to access
the central PostgreSQL HPCStats database. It must contain the following
parameters:

* ``hostname`` (*required*): The network hostname and the IP address of the
  PostgreSQL server.
* ``dbname`` (*required*): The name of the database.
* ``port`` (*required*): The TCP port listened by PostgreSQL server for
  incoming connections (Note: default TCP port of PostgreSQL is 5432).
* ``user`` (*required*): The user name to authenticate to PostgreSQL server.
* ``password`` (*required*): The password to authenticate to PostgreSQL server.

The ``constraints`` section (*optional*) has several parameters that control
how HPCStats should behave when importing production data from sources that do
not strictely respect all constraints required by the HPCStats database schema.
It can contain the following parameters:

* ``strict_user_membership``: This parameter controls how HPCStats
  :py:class:`UserImporterLdap` connector should behave when a user is a member
  of the group in LDAP directory but has no account in this LDAP directory. If
  set to ``True`` (*default*), HPCStats will fail (and stop running) when such
  incoherency is encountered. If set to ``False``, HPCStats will simply just
  print a warning message, discard this user and keep running.
* ``strict_job_project_binding``: This parameter controls how HPCStats Job
  importers category should behave when a job is linked to a project that has
  not been loaded by Project importer category previously. If set to ``True``
  (*default*), HPCStats will fail (and stop running). If set to ``False``,
  HPCStats will just print a warning message and set project reference to
  ``NULL`` in the ``Job`` table of the HPCStats database.
* ``strict_job_businesscode_binding``: This parameter is basically the same as
  ``strict_job_project_binding`` but for the Business codes. The possible
  values are ``True`` (*default*) and ``False``.
* ``strict_job_account_binding``: This parameter controls how HPCStats Job
  importer category should behave when importing a job submitted by an account
  unknown by the User importer category. When set to ``True`` (*default*),
  HPCStats will fail (and stop running) when such job is encountered. If set to
  ``False``, HPCStats will just print a warning message and skip the job.
* ``strict_job_wckey_format``: This parameter controls how
  :py:class:`JobImporterSlurm` connector should behave when importing a job
  with a badly formatted *wckey*. If set to ``True`` (*default*), HPCStats will
  fail (and stop running) when such job is encountered. If set to ``False``,
  HPCStats will just print a warning message and ignore the *wckey*.
* ``ignored_errors`` (*optional*): A comma separated list of errors codes to
  ignore. If encountered during the importation process, these errors will be
  reported as debug messages instead of warnings. All possible error codes are
  available in table :ref:`architecture_error-management`.

If the ``constraints`` section is missing, default values are assumed for all
parameters.

The ``globals`` section (*optional*) defines which connectors must be used for
projects and business importer categories. It can contain the following
parameters:

* ``business`` (*optional*): Possible values are ``dummy`` (*default*), ``csv``
  and ``slurm``.
* ``projects`` (*optional*): Possible values are ``dummy`` (*default*), ``csv``
  and ``slurm``.

If the ``globals`` section is missing, default values are assumed for all
parameters.

If the ``business`` parameter is set to ``csv``, then the ``business`` section
(*optional*) must be present with this parameter:

* ``file`` (*optional*): The absolute path to the business codes CSV file.

If the ``projects`` parameter is set to ``csv`` or ``slurm``, then the
``projects`` section (*optional*) must be present with these parameters:

* ``file`` (*optional*): for :py:class:`ProjectImporterCSV` connector, it is
  the absolute path to the projects CSV file.
* ``default_domain_key`` (*optional*): for :py:class:`ProjectImporterSlurm`
  connector, the key of the default domain associated to created projects.
* ``default_domain_name`` (*optional*): for :py:class:`ProjectImporterSlurm`
  connector, the name of the default domain associated to created projects.

The configuration file must also contain one section per cluster declared in
the ``clusters`` parameter list. The section must be the cluster name. These
sections must contain the following parameters to specify which connectors must
be used by HPCStats for each importer category on these clusters:

* ``architecture`` (*required*): The only possible value is ``archfile``.
* ``users`` (*required*): The possible values are ``ldap`` and ``ldap+slurm``.
* ``fsusage`` (*required*): Possible values are ``dummy`` and ``ssh``.
* ``events`` (*required*): The only possible value is ``slurm``.
* ``jobs`` (*required*): The only possible value is ``slurm``.

Then, the other sections depend on the connectors used for the cluster.

The ``<cluster>/archfile`` section (*optional*) is required by
:py:class:`ArchitectureImporterArchfile` connector. It must contains the
following parameters:

* ``file`` (*required*): The absolute path to the architecture file which
  which description the component of the cluster.

The ``<cluster>/ldap`` section (*optional*) is required by
:py:class:`UserImporterLdap` and :py:class:`UserImporterLdapSlurm` connectors.
It must contains the following parameters:

* ``url`` (*required*): the URL to connect to the LDAP server with its protocol
  and eventually the TCP port. *Ex:* ``ldaps://ldap.company.tld/`` or
  ``ldap://ldap.company.tld:636/``.
* ``dn`` (*required*): The distinguished name of the user for binding the LDAP
  server.
* ``phash`` (*required*): The hashed and salted password of ``dn`` for binding
  the LDAP server.
* ``cert`` (*optional*): The absolute path to the CA certificate to check LDAP
  server certificate. Default is ``None`` with means it checks the server
  certificate against all CA certificates available on the system.
* ``basedn`` (*required*): The base distinguished name to look for groups and
  users in the LDAP directory tree. *Ex:* ``dc=company,dc=tld``.
* ``rdn_people`` (*optional*) The relative distinguished name of the subtree to
  search users. Default is ``ou=people``.
* ``rdn_groups`` (*optional*): The relative distinguished name of the subtree
  to search groups. Default is ``ou=groups``.
* ``group`` (*DEPRECATED*): The name of the group of users of the cluster.
  Should be replaced by ``groups``.
* ``groups`` (*required*): A comma separated list of group of users of the
  cluster. For compatibility reasons, can be ommited if ``group`` is set.
* ``group_dpt_search`` (*required*): The regular expression to restrict the
  search of users secondary groups to find their department.
* ``group_dpt_regexp`` (*required*): The regular expression to extract the
  department name of the user out of a group name. *Ex:*
  ``cn=(.+)-dp-(.+),ou.*``.
* ``default_subdir`` (*optional*): The default subdirection assigned to users
  whose real department cannot be defined based on their groups memberships.
  This default subdirection is concatenated to the name of the user primary
  group. Default is ``unknown``.
* ``groups_alias_file`` (*optional*): The absolute path to a file which defines
  aliases to primary group names. With these aliases, it is possible to
  substitute the primary group name with a more appropriate direction name in
  the resulting user department name. The file must be formatted with one alias
  per line, each alias being the primary group name and the alias separated
  with a whitespace (*ex:* ``group_name alias``). If this parameter is not
  defined, there is no aliasing involved.


The ``<cluster>/slurm`` section (*optional*) is required by
:py:class:`ProjectImporterSlurm`, :py:class:`BusinessCodeImporterSlurm`,
:py:class:`UserImporterLdapSlurm`, :py:class:`EventImporterSlurm` and
:py:class:`JobImporterSlurm` connectors. It must contains the following
parameters:

* ``host`` (*required*): The network hostname or the IP address of the SlurmDBD
  MySQL (or MariaDB) server.
* ``name`` (*required*): The name of MySQL database that contains the SlurmDBD
  accounting (hint: value is probably ``slurm_acct_db``).
* ``user`` (*required*): The name of the user to authenticate on MySQL server.
* ``password`` (*optional*): The password of the user to authenticate on MySQL
  server. Default is None, *ie.* no password.
* ``window_size`` (*optional*): The size of the window of loaded jobs. When
  this parameter is set to a value ``N`` above ``0``, the new jobs will be
  loaded by :py:class:`JobImporterSlurm` in windowed mode, ``N`` jobs at a
  time, until there are no jobs to load anymore. If set to ``0`` (*default*),
  all jobs will be loaded at once and this can lead to a lot of memory
  consumption when there too many jobs. It is recommended to set this value
  to avoid memory over-consumption during jobs import.
* ``prefix`` (*optional*): The prefix in SlurmDBD database table names. Default
  value is the cluster name. This parameter might be usefull only in some
  corner-cases when someone wants the cluster name in HPCStats to be different
  from the Slurm cluster name.
* ``partitions`` (*optional*): List of comma separated Slurm partitions whose
  imported data (jobs, projects, business codes, etc) are restricted to. Data
  on other partitions are ignored by HPCStats for this cluster. By default,
  HPCStats imports data from all Slurm partitions of the cluster without any
  restriction.

The ``<cluster>/fsusage`` section (*optional*) is required by
:py:class:`FSUsageImporterSSH` connector. It must contains the following
parameters:

* ``host`` (*required*): The network hostname or the IP address of the cluster
  node on which the ``fsusage`` runs and where the HPCStats should connect to.
* ``name`` (*required*): The user name to authenticate on the remote cluster
  node.
* ``privkey`` (*required*): The absolute path to the SSH private key file to
  authenticate on the remote cluster node.
* ``file`` (*required*): The absolute path of the remote CSV file to read and
  parse for new filesystem usage metrics.
* ``timestamp_fmt`` (*optional*): The format of the timestamps written in the
  CSV file.  Default value is ``%Y-%m-%dT%H:%M:%S.%fZ``.

All sections and parameters on the HPCStats server component configuration file
have been covered. Here is complete annoted configuration file example with 2
clusters *cluster1* and *cluster2*:

.. include:: ../conf/hpcstats.conf
   :literal:

Agents and launcher
===================

.. _configuration_fsusage-agent:

FSUsage agent
-------------

The configuration file of the :command:`fsusage` agent is located at
:file:`/etc/hpcstats/fsusage.conf`.

This file contains only one ``global`` section (*required*) with the following
parameters:

* ``fs`` (*required*): The list separated by commas (``,``) of the mount points
  of the filesystem to monitor.
* ``csv`` (*required*): The absolute path of the CSV file where the file system
  usage rates are recorded.
* ``maxsize`` (*required*): the maximum size in MB of the CSV file. When this
  size is reached, the :command:`fsusage` agent remove the first two third of
  the file to significantly reduce its size.

Here is complete annoted HPCStats :command:`fsusage` agent configuration file
example:

.. include:: ../conf/fsusage.conf
   :literal:

.. _configuration_jobstats-agent:

JobStats agent
--------------

The configuration file of the :command:`jobstats` agent is located at
:file:`/etc/hpcstats/jobstats.conf`. 

This file contains a ``global`` section (*required*) with the following
parameters:

* ``tpl`` (*required*): The absolute path of the source template job submission
  script.
* ``script`` (*required*): The absolute path of the output generated job
  submission script.
* ``subcmd`` (*required*): The command to use for submitting the jobs. *Ex:*
  :command:`sbatch`.

Then, the file must also contain a ``vars`` section (*required*). This section
contains all the variables used in the template job submission script:

* ``name`` (*required*): The name of the jobs.
* ``ntasks`` (*required*): The number of CPU allocated for the jobs.
* ``error`` (*required*): The absolute path of the error output logging file.
* ``output`` (*required*): The absolute path of the standard output logging
  file.
* ``time`` (*required*): The maximum running time of the jobs (in minutes).
* ``partition`` (*required*): The name of the partition in which the jobs will be
  submitted.
* ``qos`` (*required*): The name of the QOS in which the jobs will be submitted.
* ``wckey`` (*required*): The wckey of the jobs.
* ``fs`` (*required*): The list of separated by white spaces of filesystems
  mountpoints to check in the jobs.
* ``log`` (*required*): The absolute path of the file where all check results
  will be recorded.

Here is complete annoted HPCStats :command:`jobstats` agent configuration file
example:

.. include:: ../conf/jobstats.conf
   :literal:

.. _configuration_jobstats-launcher:

JobStats launcher
-----------------

The configuration file of the :command:`jobstats` launcher is located at
:file:`/etc/hpcstats/launcher.conf`.

This file contains a ``global`` section (*required*) with the following
parameter:

* ``clusters`` (*required*): a list of cluster name separated by commas
  (``,``).

Then, for each cluster present in the list, a dedicated section must be
present, named after the cluster name. These sections must contain the
following parameters:


* ``frontend`` (*required*): The network hostname or the IP address of the
  cluster frontend on which the launcher should connect to launch the
  :command:`jobstats` agent.
* ``user`` (*required*): The user name to authenticate on the remote cluster
  frontend node.
* ``privkey`` (*required*): The absolute path to the SSH private key file to
  authenticate on the remote cluster frontend node.
* ``script`` (*required*): The absolute path to the :command:`jobstats` agent.

Here is complete annoted HPCStats :command:`jobstats` launcher configuration
file example:

.. include:: ../conf/launcher.conf
   :literal:
