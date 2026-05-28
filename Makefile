LINUX_CONFIG := $(HOME)/.config

.PHONY: sync-sources
sync-sources:
	cp $(LINUX_CONFIG)/bin/auto-brightness packages/auto-brightness/sources/auto-brightness
	cp $(LINUX_CONFIG)/systemd/user/auto-brightness.timer packages/auto-brightness/sources/auto-brightness.timer
	@echo "Sources synced from linux-config"

.PHONY: build-local
build-local:
	rpmdev-setuptree
	cp packages/auto-brightness/sources/* ~/rpmbuild/SOURCES/
	rpmbuild -bb --define "_version 1.0" --define "dist .local" \
		packages/auto-brightness/auto-brightness.spec
	@find ~/rpmbuild/RPMS -name "*.rpm" -newer packages/auto-brightness/auto-brightness.spec
