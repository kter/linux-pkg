Name:           kter-release
Version:        1
Release:        1%{?dist}
Summary:        kter linux-pkg repository configuration
License:        MIT
URL:            https://github.com/kter/linux-pkg
BuildArch:      noarch

%description
Installs the DNF repository configuration and GPG key for kter's linux-pkg
packages, making packages like auto-brightness available via dnf.

%install
install -D -m 0644 %{_sourcedir}/kter-linux-config.repo \
    %{buildroot}/etc/yum.repos.d/kter-linux-pkg.repo

%files
/etc/yum.repos.d/kter-linux-pkg.repo

%post
rpm --import https://repo.devtools.site/RPM-GPG-KEY-kter 2>/dev/null || :

%changelog
* Wed May 28 2026 Tomohiko Takahashi <takahashi@tomohiko.io> - 1-1
- Initial release
