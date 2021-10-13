DESTDIR = /
prefix = usr

libdir = $(DESTDIR)/$(prefix)/lib/wb-hwconf-manager
datadir = $(DESTDIR)/$(prefix)/share/wb-hwconf-manager
test_tmpdir = ./test/tmp

all:
	@echo "Nothing to do"

install_data:
	install -D -m 0644 functions.sh $(libdir)/functions.sh
	install -D -m 0755 init.sh $(libdir)/init.sh
	cp -rv ./slots $(datadir)/slots
	cd $(datadir)/slots && ./gen_extio_slots.sh && rm *.sh
	install -d -m 0755 $(datadir)/modules
	cp modules/*.dtso modules/*.dtsi modules/*.sh $(datadir)/modules
	cp wb-hardware.conf.* $(datadir)/


install: install_data
	install -D -m 0755 wb-hwconf-helper $(DESTDIR)/$(prefix)/bin/wb-hwconf-helper
	install -d -m 0755 $(DESTDIR)/usr/share/wb-mqtt-confed/schemas
	cat wb-hardware.schema.json modules/*.schema.json | \
		jq --slurp '.[0].definitions = .[0].definitions + (.[1:] | add) | .[0]' \
		> $(DESTDIR)/usr/share/wb-mqtt-confed/schemas/wb-hardware.schema.json
	install -D -m 0644 wb-hwconf-manager.wbconfigs $(DESTDIR)/etc/wb-configs.d/02wb-hwconf-manager

test_clean:
	rm -rf $(test_tmpdir)

test: test_clean
	make datadir=$(test_tmpdir) install_data
	cd test && ./test.sh

clean: test_clean

.PHONY: install install_data all test test_clean clean
