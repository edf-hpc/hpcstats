HPCStats
========

HPCStats imports HPC supercomputers raw production data from various sources
(Job schedulers, log files, LDAP directories, etc. and insert everything into
a coherent and structured PostgreSQL database. All these structured
information can be then used to compute many statistics and metrics about the
usage of HPC supercomputers.

HPCStats is a free software licensed under the GPLv2.

Documentation
-------------

The documentation is available online: http://edf-hpc.github.io/hpcstats

Developement
------------

### Syntax

The code must be pep8 and pylint compliant (with provided `pylintrc` file).
Check with:

```
pep8 HPCStats
```

And:

```
pylint HPCStats
```

### Tests

New developments must be covered by unit tests. To run all the unit tests,
simply run the following command:

```
nosetests
```

Contact and support
-------------------

For bug reports and questions, please open issues on GitHub:
http://github.com/edf-hpc/hpcstats/issues

For any other things, please contact us by email at:
dsp-cspite-ccn-hpc@edf.fr

Authors
-------

* Rémi Palancher              <remi-externe.palancher@edf.fr>

Contributors
------------

* Loic Laureote
* Rodrigue Nsiangani
* Nali Andriana            <nalimanaja.andrianavony@bull.net>
* Gaston Samarou
* Damien Balima
* Jean-Baptiste Lesenne      <jean-baptiste.lesenne@bull.net>
* Stéphan Gorget
