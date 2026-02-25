prefix = /usr

libdir = $(DESTDIR)$(prefix)/lib/wb-hwconf-manager
datadir = $(DESTDIR)$(prefix)/share/wb-hwconf-manager
test_tmpdir = ./test/tmp

modules_schema_part = modules/*.schema.json
hidden_modules_schema_part = modules/hidden_modules.json
hidden_modules = $(shell jq -cM '.hidden_from_webui' $(hidden_modules_schema_part))
vendor_modules_config = vendor-modules.json

processed_pybuild_test_args = $(shell echo $(PYBUILD_TEST_ARGS) | sed -E "s|--cov-config=[^ ]+|--cov-config=coveragerc|")

all:
	@echo "Nothing to do"

install_data:
	install -m 0755 -d $(datadir) $(libdir)
	install -m 0644 functions.sh $(libdir)/functions.sh
	install -m 0755 init.sh $(libdir)/init.sh
	install -m 0755 config.py $(libdir)/config.py
	install -m 0644 $(vendor_modules_config) $(datadir)/vendor-modules.json
	cp -rv ./slots $(datadir)/slots
	cd $(datadir)/slots && ./gen_extio_slots.sh && rm *.sh
	install -d -m 0755 $(datadir)/modules
	cp modules/*.dtso modules/*.dtsi modules/*.sh $(datadir)/modules
	install -d -m 0755 $(datadir)/boards
	cp -r boards $(datadir)

install: install_data
	install -D -m 0755 wb-hwconf-helper $(DESTDIR)$(prefix)/bin/wb-hwconf-helper
	install -d -m 0755 $(DESTDIR)$(prefix)/share/wb-mqtt-confed/schemas
	@echo "Embedding modules from $(modules_schema_part) to schema; $(hidden_modules) (from $(hidden_modules_schema_part)) are hidden"
	cat wb-hardware.schema.json $(modules_schema_part) | \
		jq --slurp '.[0].definitions = .[0].definitions + (.[1:] | add) | .[0]' | \
		jq '.definitions.slot.properties.module.options.enum_hidden += $(hidden_modules)' \
		> $(DESTDIR)$(prefix)/share/wb-mqtt-confed/schemas/wb-hardware.schema.json
	install -D -m 0644 wb-hwconf-manager.wbconfigs $(DESTDIR)/etc/wb-configs.d/02wb-hwconf-manager
	install -Dm0644 wb-hardware.conf $(DESTDIR)/etc/wb-hardware.conf

test:
	python3 -m pytest -vv $(processed_pybuild_test_args)

.PHONY: install install_data all test
