DESTDIR = /
prefix = usr

datadir = $(DESTDIR)/$(prefix)/share/wb-hwconf-manager

all:
	@echo "Nothing to do"

install:
	install -D -m 0755 wb-hwconf-helper $(DESTDIR)/$(prefix)/bin/wb-hwconf-helper
	install -D -m 0644 functions.sh $(datadir)/functions.sh
	cp -r slots modules $(datadir)/
	cp wb-hardware.conf.* $(datadir)/
	install -D -m 0644 wb-hardware.schema.json $(DESTDIR)/usr/share/wb-mqtt-confed/schemas/wb-hardware.schema.json
	install -D -m 0644 wb-hwconf-manager.wbconfigs $(DESTDIR)/etc/wb-configs.d/02wb-hwconf-manager

.PHONY: install all
