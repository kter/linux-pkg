Name:           pam-fprint-grosshack
Version:        %{_version}
Release:        1%{?dist}
Summary:        PAM module for simultaneous fingerprint and password authentication
License:        GPLv2+
URL:            https://gitlab.com/mishakmak/pam-fprint-grosshack

Source0:        pam-fprint-grosshack-%{version}.tar.gz

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  gcc
BuildRequires:  pam-devel
BuildRequires:  systemd-devel
BuildRequires:  glib2-devel
BuildRequires:  libfprint-devel
BuildRequires:  polkit-devel

Requires:       fprintd-pam

%description
A PAM module that enables simultaneous fingerprint and password authentication
through fprintd. When used before pam_unix in the PAM stack, it allows the user
to authenticate by either typing their password or placing their finger on the
reader — whichever succeeds first.

This is a fork of the pam_fprintd module from the fprintd project, modified to
run fingerprint and password verification concurrently.

%prep
%autosetup -n pam-fprint-grosshack-%{version}
# pam_wrapper is only used by tests (subdir commented out); make it optional
sed -i 's/required: get_option(.pam.)/required: false/' meson.build

%build
%meson \
    -Dpam=true \
    -Dman=false \
    -Dsystemd=false \
    -Dpam_modules_dir=%{_libdir}/security
%meson_build

%install
%meson_install

%files
%license COPYING
%{_libdir}/security/pam_fprintd_grosshack.so

%changelog
* Wed Jun 04 2026 Tomohiko Takahashi <takahashi@tomohiko.io> - 1.94.2-1
- Initial package based on gitlab.com/mishakmak/pam-fprint-grosshack
