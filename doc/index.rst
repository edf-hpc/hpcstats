.. hpcstats documentation master file, created by
   sphinx-quickstart on Thu Jun 25 15:57:06 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to HPCStats's documentation!
====================================


HPCStats is a software to help generate statistics about the usage of HPC
supercomputers.

It imports incrementally data from various sources (job schedulers, user
directories, etc) to build a coherent PostgreSQL database with all the
information. Then, this database can be interrogated to extract usefull
statistics about users, jobs and supercomputer availability.


.. toctree::
   :maxdepth: 1

   architecture
   installation
   configuration
   usage
   api/modules

==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

