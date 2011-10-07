#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


VERSION='0.1'

setup(name='hpcstats',
      version=VERSION,
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      scripts=['scripts/supervision'],
      author='Stéphan Gorget',
      author_email='Stephan Gorget',
      license='EDF',
      url='http://www.edf.fr/',
      download_url='http://www.edf.fr/',
      platforms=['GNU/Linux', 'BSD', 'MacOSX'],
      keywords=['clustershell', 'hpcstats'],
      description='ClusterShell library and tools',
      classifiers=[
          "Development Status :: 5 - Production/Stable",
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

