%global debug_package %{nil}

Name:           zenith-wallpaper
Version:        %{_version}
Release:        2%{?dist}
Summary:        Render the real night sky as a sway desktop wallpaper
License:        MIT
URL:            https://github.com/kter/zenith-wallpaper
Source0:        zenith-wallpaper-%{version}.tar.gz

BuildRequires:  golang

Requires:       sway
Recommends:     geoclue2

%description
A Go tool that renders the real night sky (computed from your current location
and time) as a Wayland/sway desktop wallpaper, refreshed hourly via a systemd
user timer. The full-dome sky (Lambert equal-area projection, zenith-centered)
includes the Milky Way, ~8400 stars from the Yale Bright Star Catalogue, and
real-time planet/moon positions. All assets (NASA Deep Star Maps 2020, BSC5)
are embedded in the binary — no internet download needed at runtime.

%prep
%autosetup -n zenith-wallpaper-%{version}

%build
export GOFLAGS='-mod=vendor'
export CGO_ENABLED=0
export GOCACHE=$(mktemp -d)
go build -trimpath -ldflags "-s -w -X main.version=%{version}" -o zenith-wallpaper .

%install
install -D -m 0755 zenith-wallpaper \
    %{buildroot}%{_bindir}/zenith-wallpaper
install -D -m 0644 %{_sourcedir}/zenith-wallpaper.service \
    %{buildroot}%{_userunitdir}/zenith-wallpaper.service
install -D -m 0644 %{_sourcedir}/zenith-wallpaper.timer \
    %{buildroot}%{_userunitdir}/zenith-wallpaper.timer

%files
%license LICENSE
%doc README.md
%{_bindir}/zenith-wallpaper
%{_userunitdir}/zenith-wallpaper.service
%{_userunitdir}/zenith-wallpaper.timer

%changelog
* Wed Jun 10 2026 Tomohiko Takahashi <takahashi@tomohiko.io> - 1.1-2
- Inject version into binary via ldflags so --version reports the
  package version instead of "dev"

* Thu Jun 04 2026 Tomohiko Takahashi <takahashi@tomohiko.io> - 1.0-1
- Initial package
