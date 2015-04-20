#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


VERSION='0.1'

setup(name='hpcstats',
      version=VERSION,
      packages=find_packages(),
      scripts=['scripts/supervision'],
      author='Stéphan Gorget, Rémi Palancher',
      author_email='stephan.gorget@edf.fr, remi.palancher@edf.fr',
      license='GPLv2',
      url='http://www.edf.fr/',
      download_url='http://www.edf.fr/',
      platforms=['GNU/Linux', 'BSD', 'MacOSX'],
      keywords=['clustershell', 'hpcstats'],
      description='HPCStats tool',
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

