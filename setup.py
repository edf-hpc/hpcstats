#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


VERSION='1.6.2'

setup(name='hpcstats',
      version=VERSION,
      packages=find_packages(),
      scripts=['scripts/hpcstats'],
      author='EDF CCN-HPC',
      author_email='dsp-cspite-ccn-hpc@edf.fr',
      license='GPLv2',
      url='http://edf-hpc.github.io/hpcstats',
      download_url='http://github.com/edf-hpc/hpcstats/',
      platforms=['GNU/Linux', 'BSD', 'MacOSX'],
      keywords=['hpcstats', 'hpc', 'supercomputers', 'statistics'],
      install_requires=['argparse',
                        'psycopg2',
                        'MySQL-python',
                        'clustershell',
                        'python-ldap',
                        'python-dateutil',
                        'paramiko',
                        'mako' ],
      description="HPCStats imports HPC supercomputers raw production " \
                  "data from various sources (Job schedulers, log files, " \
                  "LDAP directories, etc. and insert everything into a " \
                  "coherent and structured PostgreSQL database. All these " \
                  "structured information can be then used to compute many " \
                  "statistics and metrics about the usage of HPC " \
                  "supercomputers.",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: System Administrators",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: POSIX :: BSD",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: System :: Clustering",
          "Topic :: System :: Distributed Computing"
      ]
     )

