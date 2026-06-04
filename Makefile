LINUX_CONFIG := $(HOME)/.config
PAM_FPRINT_VERSION := 1.94.2
ZENITH_VERSION := 1.0

.PHONY: sync-sources
sync-sources:
	cp $(LINUX_CONFIG)/bin/auto-brightness packages/auto-brightness/sources/auto-brightness
	cp $(LINUX_CONFIG)/systemd/user/auto-brightness.timer packages/auto-brightness/sources/auto-brightness.timer
	@echo "Sources synced from linux-config"
	git -C $(HOME)/workspace/pam-fprint-grosshack archive \
		--prefix=pam-fprint-grosshack-$(PAM_FPRINT_VERSION)/ HEAD \
		| gzip > packages/pam-fprint-grosshack/sources/pam-fprint-grosshack-$(PAM_FPRINT_VERSION).tar.gz
	@echo "pam-fprint-grosshack tarball created"
	git -C $(HOME)/workspace/zenith-wallpaper archive \
		--prefix=zenith-wallpaper-$(ZENITH_VERSION)/ HEAD \
		| gzip > packages/zenith-wallpaper/sources/zenith-wallpaper-$(ZENITH_VERSION).tar.gz
	@echo "zenith-wallpaper tarball created"

.PHONY: build-local
build-local:
	rpmdev-setuptree
	cp packages/auto-brightness/sources/* ~/rpmbuild/SOURCES/
	rpmbuild -bb --define "_version 1.0" --define "dist .local" \
		packages/auto-brightness/auto-brightness.spec
	@find ~/rpmbuild/RPMS -name "*.rpm" -newer packages/auto-brightness/auto-brightness.spec

.PHONY: build-local-pam-fprint-grosshack
build-local-pam-fprint-grosshack:
	rpmdev-setuptree
	cp packages/pam-fprint-grosshack/sources/pam-fprint-grosshack-$(PAM_FPRINT_VERSION).tar.gz ~/rpmbuild/SOURCES/
	rpmbuild -bb \
		--define "_version $(PAM_FPRINT_VERSION)" \
		--define "dist .local" \
		packages/pam-fprint-grosshack/pam-fprint-grosshack.spec
	@find ~/rpmbuild/RPMS -name "pam-fprint-grosshack*.rpm" -newer packages/pam-fprint-grosshack/pam-fprint-grosshack.spec

.PHONY: build-local-zenith-wallpaper
build-local-zenith-wallpaper:
	rpmdev-setuptree
	cp packages/zenith-wallpaper/sources/zenith-wallpaper-$(ZENITH_VERSION).tar.gz ~/rpmbuild/SOURCES/
	cp packages/zenith-wallpaper/sources/zenith-wallpaper.service ~/rpmbuild/SOURCES/
	cp packages/zenith-wallpaper/sources/zenith-wallpaper.timer ~/rpmbuild/SOURCES/
	rpmbuild -bb \
		--define "_version $(ZENITH_VERSION)" \
		--define "dist .local" \
		packages/zenith-wallpaper/zenith-wallpaper.spec
	@find ~/rpmbuild/RPMS -name "zenith-wallpaper*.rpm" -newer packages/zenith-wallpaper/zenith-wallpaper.spec
