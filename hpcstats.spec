Name:		hpcstats		
Version:	1.6.3	
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
install -d %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_datadir}/%{name}/bin
install -d %{buildroot}/%{_datadir}/%{name}/db

cp -r db/* %{buildroot}/%{_datadir}/%{name}/db

cp conf/hpcstats.conf %{buildroot}%{_sysconfdir}/%{name}
cp conf/architecture.conf %{buildroot}%{_sysconfdir}/%{name}


install contribs/fsusage %{buildroot}%{_datadir}/%{name}/bin
cp conf/fsusage.conf %{buildroot}%{_sysconfdir}/%{name}


install contribs/jobstats %{buildroot}%{_datadir}/%{name}/bin
install contribs/jobstats.tpl.sh %{buildroot}%{_datadir}/%{name}/bin
cp conf/jobstats.conf %{buildroot}%{_sysconfdir}/%{name}

install contribs/launch-jobstats %{buildroot}%{_datadir}/%{name}/bin
cp conf/launcher.conf %{buildroot}%{_sysconfdir}/%{name}

install contribs/encode-password %{buildroot}%{_datadir}/%{name}/bin
install contribs/sync-hpcstats-slurm-job-accounts %{buildroot}%{_datadir}/%{name}/bin

python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}

%clean

%files
%doc README.md
%{python3_sitelib}
%config %{_bindir}/hpcstats
%config %{_sysconfdir}/%{name}/%{name}.conf
%config %{_sysconfdir}/%{name}/architecture.conf
%config %{_datadir}/%{name}/db/*

%package -n hpcstats-jobstats-agent
Summary: Jobstat agent of HPC cluster usage accounting software 
Requires: python3

%description -n hpcstats-jobstats-agent
This agent is typically installed on HPC cluster frontend. It provides all files required by the launcher to test end-to-end HPC cluster availability.

%files -n hpcstats-jobstats-agent
%config %{_sysconfdir}/%{name}/jobstats.conf
%config %{_datadir}/%{name}/bin/jobstats.tpl.sh
%config %{_datadir}/%{name}/bin/jobstats

%package -n hpcstats-jobstats-launcher
Summary: Jobstat launcher of HPC cluster usage accounting software 
Requires: python3
Requires: python3-paramiko

%description -n hpcstats-jobstats-launcher
The component launches the jobstats agent on all configured HPC cluster frontends.

%files -n hpcstats-jobstats-launcher
%config %{_sysconfdir}/%{name}/launcher.conf
%config %{_datadir}/%{name}/bin/launch-jobstats

%package -n hpcstats-fsusage-agent
Summary: FSUsage agent of HPC cluster usage accounting software 
Requires: python3

%description -n hpcstats-fsusage-agent
This agent is typically installed on HPC cluster frontend to log in a CSV file the usage rate of file systems.

%files -n hpcstats-fsusage-agent
%config %{_sysconfdir}/%{name}/fsusage.conf
%config %{_datadir}/%{name}/bin/fsusage

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
%config %{_datadir}/%{name}/bin/encode-password
%config %{_datadir}/%{name}/bin/sync-hpcstats-slurm-job-accounts


%changelog
* Thu Mar 18 2021 Nilce BOUSSAMBA <nilce-externe.boussamba@edf.fr>
- first rpm package
