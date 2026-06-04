LINUX_CONFIG := $(HOME)/.config
ZENITH_VERSION := 1.0

.PHONY: sync-sources
sync-sources:
	cp $(LINUX_CONFIG)/bin/auto-brightness packages/auto-brightness/sources/auto-brightness
	cp $(LINUX_CONFIG)/systemd/user/auto-brightness.timer packages/auto-brightness/sources/auto-brightness.timer
	@echo "Sources synced from linux-config"
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
