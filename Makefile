DESTDIR = /
prefix = usr

datadir = $(DESTDIR)/$(prefix)/share/wb-hwconf-manager

all:
	@echo "Nothing to do"

install:
	install -D -m 0755 wb-hwconf-helper $(DESTDIR)/$(prefix)/bin/wb-hwconf-helper
	install -D -m 0644 functions.sh $(datadir)/functions.sh
	install -d -m 0755 $(datadir)/modules
	cp -r slots $(datadir)/
	cp wb-hardware.conf.* $(datadir)/
	cp modules/*.dtso ${datadir}/modules
	cp modules/*.sh ${datadir}/modules
	install -d -m 0755 $(DESTDIR)/usr/share/wb-mqtt-confed/schemas
	cat wb-hardware.schema.json modules/*.schema.json | \
		jq --slurp '.[0].definitions = .[0].definitions + (.[1:] | add) | .[0]' \
		> $(DESTDIR)/usr/share/wb-mqtt-confed/schemas/wb-hardware.schema.json
	install -D -m 0644 wb-hwconf-manager.wbconfigs $(DESTDIR)/etc/wb-configs.d/02wb-hwconf-manager

.PHONY: install all
