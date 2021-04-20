Name:		hpcstats		
Version:	1.6.6
Release:	1%{?dist}.edf
Summary:	HPC cluster usage accounting and reporting software	

License:	Proprietary
URL:		http://github.com/edf-hpc/hpcstats
Source0:	%{name}-%{version}.tar.gz

BuildRequires:	python3-setuptools
BuildRequires:	python3-sphinx
BuildRequires:	python3-sphinx_rtd_theme
Requires: rpm-cron
Requires: postgresql

%description
HPC cluster usage accounting and reporting software 
HPCStats imports raw data from various sources (Job schedulers, log
files, LDAP directories, etc. and insert everything into a coherent
and structured PostgreSQL database. Then, all these structured
information can be used to extract statistics about the usage of the HPC clusters.

%prep
%global debug_package %{nil}
%setup -q

%build
CFLAGS="%{optflags}" python3 setup.py build

%install
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_sharedstatedir}/%{name}
install -d %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_datadir}/%{name}/bin
install -d %{buildroot}%{_datadir}/%{name}/db
install -d %{buildroot}%{_sysconfdir}/cron.d/%{name}

cp -r db/* %{buildroot}%{_datadir}/%{name}/db

cp conf/hpcstats.conf %{buildroot}%{_sysconfdir}/%{name}
cp conf/architecture.conf %{buildroot}%{_sysconfdir}/%{name}


install contribs/fsusage %{buildroot}%{_datadir}/%{name}/bin
cp conf/fsusage.conf %{buildroot}%{_sysconfdir}/%{name}

install contribs/fsquota %{buildroot}%{_datadir}/%{name}/bin
cp conf/fsquota.conf %{buildroot}%{_sysconfdir}/%{name}


install contribs/jobstats %{buildroot}%{_datadir}/%{name}/bin
install contribs/jobstats.tpl.sh %{buildroot}%{_datadir}/%{name}/bin
cp conf/jobstats.conf %{buildroot}%{_sysconfdir}/%{name}

install contribs/launch-jobstats %{buildroot}%{_datadir}/%{name}/bin
cp conf/launcher.conf %{buildroot}%{_sysconfdir}/%{name}

install contribs/encode-password %{buildroot}%{_datadir}/%{name}/bin
install contribs/sync-hpcstats-slurm-job-accounts %{buildroot}%{_datadir}/%{name}/bin

install cron/cron.d %{buildroot}%{_sysconfdir}/cron.d/%{name}
install cron/hpcstats-fsquota-agent.cron.d %{buildroot}%{_sysconfdir}/cron.d
install cron/hpcstats-fsusage-agent.cron.d %{buildroot}%{_sysconfdir}/cron.d
install cron/hpcstats-jobstats-launcher.cron.d %{buildroot}%{_sysconfdir}/cron.d


python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}

%clean

%files
%doc README.md
%{python3_sitelib}/HPCStats/*
%{python3_sitelib}/*%{name}*.egg-info
%{_bindir}/hpcstats
%{_sysconfdir}/cron.d/%{name}/cron.d
%config %{_sysconfdir}/%{name}/%{name}.conf
%config %{_sysconfdir}/%{name}/architecture.conf
%config %{_datadir}/%{name}/db/*

%post
#!/bin/sh
# postinst script for hpcstats
set -e
arg='configure'
case "$arg" in
    configure)
        # if the system user does not exist, create it
        if [ ! $(id -u hpcstats 2>/dev/null) ]; then
            adduser --system --shell=/bin/sh --no-create-home --home /nonexistent hpcstats
        fi
        # if the PostgreSQL user does not exist, create it
        if ! $(su postgres -c 'psql -c "\du"' 2>/dev/null | grep -q hpcstats); then
            su postgres -c "\
                createuser --no-createdb --no-superuser --no-createrole hpcstats && \
                psql -c \"ALTER ROLE hpcstats WITH PASSWORD 'hpcstats';\""
        fi
        # if the database does not exist, create it
        if ! $(su postgres -c 'psql -c "\l"' 2>/dev/null | grep -q hpcstatsdb); then
            su postgres -c "\
                createdb -O hpcstats hpcstatsdb"
            su hpcstats -c "\
                psql hpcstatsdb < /usr/share/hpcstats/db/hpcstats.psql"
        fi
        # test if job table must be upgraded with job_account field coming with
        # HPCStats v1.2
        if ! $(su hpcstats -c "psql hpcstatsdb -c '\d Job'" | grep -q job_account); then
            echo "Upgrading DB schema to add job account column"
            su hpcstats -c "\
                psql hpcstatsdb < /usr/share/hpcstats/db/migrations/001_add_job_account.psql"
        fi
        # test if job table must be upgraded with job_account field coming with
        # HPCStats v1.6
        if ! $(su hpcstats -c "psql hpcstatsdb -c '\d Job'" | grep -q job_department); then
            echo "Upgrading DB schema to add job department column"
            su hpcstats -c "\
                psql hpcstatsdb < /usr/share/hpcstats/db/migrations/002_add_job_department.psql"
        fi
        # test if job table must be upgraded with longer job_name field starting with
        # HPCStats v1.6.2
        if ! $(su hpcstats -c "psql hpcstatsdb -c '\d Job'" | grep job_name | grep -q text); then
            echo "Upgrading DB schema to extend job name column"
            su hpcstats -c "\
                psql hpcstatsdb < /usr/share/hpcstats/db/migrations/003_extend_job_name.psql"
        fi
        # test if job table must be upgraded with walltime field coming with
        # HPCStats v1.6.2
        if ! $(su hpcstats -c "psql hpcstatsdb -c '\d Job'" | grep -q walltime); then
            echo "Upgrading DB schema to add job walltime column"
            su hpcstats -c "\
                psql hpcstatsdb < /usr/share/hpcstats/db/migrations/004_add_walltime.psql"
        fi
        # test if fsquota table must be created for the fsquota agent coming with
        # HPCStats v1.6.3
        if ! $(su hpcstats -c "psql hpcstatsdb -c '\dt'" | grep -q fsquota); then
            echo "Upgrading DB schema to add fsquota table"
            su hpcstats -c "\
                psql hpcstatsdb < /usr/share/hpcstats/db/migrations/005_table_fsquota.psql"
        fi

    ;;

    abort-upgrade|abort-remove|abort-deconfigure)

    ;;

    *)
        echo "postinst called with unknown argument \`$1'" >&2
        exit 1
    ;;
esac
%postun
#!/bin/sh
set -e
arg='remove'
case "$arg" in
    remove)
        # if the database exists, drop  it
        if $(su postgres -c 'psql -c "\l"' 2>/dev/null | grep -q hpcstatsdb); then
            su - postgres -c 'dropdb hpcstatsdb'
        fi
        # if the PostgreSQL user exists, drop it
        if $(su postgres -c 'psql -c "\du"' 2>/dev/null | grep -q hpcstats); then
            su - postgres -c 'dropuser hpcstats'
        fi
        # delete the system user
        if [ ! -e /usr/share/hpcstats/bin/fsusage \
             -a ! -e /usr/share/hpcstats/bin/launch-jobstats ] ; then
            # delete the system user
            userdel hpcstats
        fi
        ;;

    remove|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)

        ;;

    *)
        echo "postrm called with unknown argument \`$1'" >&2
        exit 1

esac

exit 0
%package -n hpcstats-jobstats-agent
Summary: Jobstat agent of HPC cluster usage accounting software 
Requires: python3

%description -n hpcstats-jobstats-agent
This agent is typically installed on HPC cluster frontend. It provides all files required by the launcher to test end-to-end HPC cluster availability.

%files -n hpcstats-jobstats-agent
%config %{_sysconfdir}/%{name}/jobstats.conf
%{_datadir}/%{name}/bin/jobstats.tpl.sh
%{_datadir}/%{name}/bin/jobstats

%package -n hpcstats-jobstats-launcher
Summary: Jobstat launcher of HPC cluster usage accounting software 
Requires: python3
Requires: python3-paramiko

%description -n hpcstats-jobstats-launcher
The component launches the jobstats agent on all configured HPC cluster frontends.

%files -n hpcstats-jobstats-launcher
%config %{_sysconfdir}/%{name}/launcher.conf
%{_datadir}/%{name}/bin/launch-jobstats
%{_sysconfdir}/cron.d/hpcstats-jobstats-launcher.cron.d

%post -n hpcstats-jobstats-launcher
#!/bin/sh
# postinst script for hpcstats
set -e
arg='configure'
case "$arg" in
    configure)
        # if the system user does not exist, create it
        if [ ! $(id -u hpcstats 2>/dev/null) ]; then
            adduser --system --shell=/bin/sh --no-create-home --home /nonexistent hpcstats
        fi
    ;;

    abort-upgrade|abort-remove|abort-deconfigure)

    ;;

    *)
        echo "postinst called with unknown argument \`$1'" >&2
        exit 1
    ;;
esac

%postun -n hpcstats-jobstats-launcher
#!/bin/sh
set -e
arg='remove'
case "$arg" in
    remove)
        if [ ! -e /usr/bin/hpcstats \
             -a ! -e /usr/share/hpcstats/bin/fsusage ] ; then
            # delete the system user
            userdel hpcstats
        fi
        ;;

    remove|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)

        ;;

    *)
        echo "postrm called with unknown argument \`$1'" >&2
        exit 1

esac

exit 0

%package -n hpcstats-fsusage-agent
Summary: FSUsage agent of HPC cluster usage accounting software 
Requires: python3

%description -n hpcstats-fsusage-agent
This agent is typically installed on HPC cluster frontend to log in a CSV file the usage rate of file systems.

%files -n hpcstats-fsusage-agent
%config %{_sysconfdir}/%{name}/fsusage.conf
%{_datadir}/%{name}/bin/fsusage
%{_sysconfdir}/cron.d/hpcstats-fsusage-agent.cron.d
%dir %{_sharedstatedir}/%{name}

%post -n hpcstats-fsusage-agent
#!/bin/sh
set -e
arg='configure'
case "$arg" in
    configure)
        # if the system user does not exist, create it
        if [ ! $(id -u hpcstats 2>/dev/null) ]; then
            adduser --system --shell=/bin/sh --no-create-home --home /nonexistent hpcstats
        fi
	chown hpcstats /var/lib/hpcstats
    ;;

    abort-upgrade|abort-remove|abort-deconfigure)

    ;;

    *)
        echo "postinst called with unknown argument \`$1'" >&2
        exit 1
    ;;
esac

%postun -n hpcstats-fsusage-agent
#!/bin/sh
set -e
arg='remove'
case "$arg" in
    remove)
        # delete the system user
        if [ ! -e /usr/bin/hpcstats \
             -a ! -e /usr/share/hpcstats/bin/launch-jobstats ] ; then
            # delete the system user
            userdel hpcstats
            rm -rf /var/lib/hpcstats
        fi
        ;;

    remove|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)

        ;;

    *)
        echo "postrm called with unknown argument \`$1'" >&2
        exit 1

esac

exit 0

%package -n hpcstats-fsquota-agent
Summary: FSQuota agent of HPC cluster usage accounting software
Requires: python3

%description -n hpcstats-fsquota-agent
This agent is typically installed on HPC cluster frontend to log in a CSV file the detailed usage and quota per user of file systems.

%files -n hpcstats-fsquota-agent
%config %{_sysconfdir}/%{name}/fsquota.conf
%{_datadir}/%{name}/bin/fsquota
%{_sysconfdir}/cron.d/hpcstats-fsquota-agent.cron.d
%dir %{_sharedstatedir}/%{name}

%post -n hpcstats-fsquota-agent
#!/bin/sh
set -e
arg='configure'
case "$arg" in
    configure)
        # if the system user does not exist, create it
        if [ ! $(id -u hpcstats 2>/dev/null) ]; then
            adduser --system --shell=/bin/sh --no-create-home --home /nonexistent hpcstats # --uid 100-999
        fi
	    chown hpcstats /var/lib/hpcstats
    ;;

    abort-upgrade|abort-remove|abort-deconfigure)

    ;;

    *)
        echo "postinst called with unknown argument \`$1'" >&2
        exit 1
    ;;
esac

%postun -n hpcstats-fsquota-agent
#!/bin/sh
set -e
arg='remove'
case "$arg" in
    remove)
        # delete the system user
        if [ ! -e /usr/bin/hpcstats \
             -a ! -e /usr/share/hpcstats/bin/launch-jobstats ] ; then
            # delete the system user
            userdel hpcstats
            rm -rf /var/lib/hpcstats
        fi
        ;;

    remove|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)

        ;;

    *)
        echo "postrm called with unknown argument \`$1'" >&2
        exit 1

esac

exit 0

%package -n hpcstats-utils
Summary: Various utilities of HPC cluster usage accounting software 
Requires: python3
Requires: python3-psycopg2

%description -n hpcstats-utils
Set of various utilities for HPCStats accounting software:
   - script to encode passwords in configurations files.
   - script to add descriptions to BusinessCodes and Projects
   - script to add Domains

%files -n hpcstats-utils
%{_datadir}/%{name}/bin/encode-password
%{_datadir}/%{name}/bin/sync-hpcstats-slurm-job-accounts


%changelog
* Fri Apr 16 2021 Nilce BOUSSAMBA <nilce-externe.boussamba@edf.fr>
- add post-{install,rm} scripts for hpcstats
* Wed Apr 14 2021 Nilce BOUSSAMBA <nilce-externe.boussamba@edf.fr>
- add cron jobs for hpcstats agent
* Fri Apr 09 2021 Nilce BOUSSAMBA <nilce-externe.boussamba@edf.fr>
- add package hpcstats-fsquota-agent
* Thu Mar 18 2021 Nilce BOUSSAMBA <nilce-externe.boussamba@edf.fr>
- first rpm package
