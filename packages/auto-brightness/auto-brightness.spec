Name:           auto-brightness
Version:        %{_version}
Release:        1%{?dist}
Summary:        Automatically adjust screen brightness based on webcam ambient light
License:        MIT
URL:            https://github.com/kter/linux-pkg
BuildArch:      noarch

Requires:       brightnessctl
Requires:       ffmpeg
Requires:       ImageMagick

%description
A bash script that periodically adjusts screen brightness using webcam
luminance measurement via ffmpeg and ImageMagick. Includes a systemd user
timer that runs every 30 seconds. Brightness curve is tuned for comfortable
low-light use with Intel backlight devices.

%install
install -D -m 0755 %{_sourcedir}/auto-brightness \
    %{buildroot}/usr/local/bin/auto-brightness
install -D -m 0644 %{_sourcedir}/auto-brightness.service \
    %{buildroot}/usr/lib/systemd/user/auto-brightness.service
install -D -m 0644 %{_sourcedir}/auto-brightness.timer \
    %{buildroot}/usr/lib/systemd/user/auto-brightness.timer

%files
/usr/local/bin/auto-brightness
/usr/lib/systemd/user/auto-brightness.service
/usr/lib/systemd/user/auto-brightness.timer

%post
systemctl --global enable auto-brightness.timer >/dev/null 2>&1 || :
for u in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
    uid=$(id -u "$u" 2>/dev/null) || continue
    [ "$uid" -lt 1000 ] && continue
    XDG_RUNTIME_DIR="/run/user/$uid" runuser -u "$u" -- \
        systemctl --user start auto-brightness.timer >/dev/null 2>&1 || :
done

%preun
if [ $1 -eq 0 ]; then
    systemctl --global disable auto-brightness.timer >/dev/null 2>&1 || :
    for u in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
        uid=$(id -u "$u" 2>/dev/null) || continue
        [ "$uid" -lt 1000 ] && continue
        XDG_RUNTIME_DIR="/run/user/$uid" runuser -u "$u" -- \
            systemctl --user stop auto-brightness.timer >/dev/null 2>&1 || :
    done
fi

%changelog
* Wed May 28 2026 Tomohiko Takahashi <takahashi@tomohiko.io> - 1.0-1
- Initial package
