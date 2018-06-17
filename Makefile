SHELL:=/bin/bash

XML_PATH = gr-mods/grc
CC_PATH = gr-mods/lib
PY_PATH = gr-mods/python
H_PATH = gr-mods/include/mods

HIER_FILES = $(shell find grc/hier/ -type f -name '*.grc')
HIER_PY_FILES = $(patsubst grc/hier/%.grc, gr-mods/python/%.py, $(HIER_FILES))
HIER_RC = $(patsubst grc/hier/%.grc, grc/hier/%.build_record, $(HIER_FILES))

GRC_FILES = $(shell find grc/ -maxdepth 1 -type f -name '*.grc')
GRC_PY_FILES = $(patsubst grc/%.grc, build/%.py, $(GRC_FILES))

MOD_XML = $(shell find $(XML_PATH) -type f -name '*.xml')
MOD_I_H = $(shell find $(CC_PATH) -type f -name '*.h')
MOD_CC = $(shell find $(CC_PATH) -type f -name '*.cc')
MOD_PY = $(shell find $(PY_PATH) -type f -name '*.py')
MOD_H = $(shell find $(H_PATH) -type f -name '*.h')

GR_FRAMERS_REPO = https://github.com/gr-vt/gr-framers.git
GR_FRAMERS_BUILD_DIR = gr-framers/build
GR_FRAMERS_BUILD_RC = gr-framers/build_record
GR_MODS_BUILD_DIR = gr-mods/build
GR_MODS_BUILD_RC = gr-mods/build_record

.PHONY: build install clean uninstall mods install-mods clean-mods \
uninstall-mods framers install-framers clean-framers uninstall-framers hier \
build-hier clean-hier

# Build Rx Flowgraphs
build: $(GRC_PY_FILES)

build/%.py: grc/%.grc
	@echo "Check if framers and mods libraries are installed"
	@python -c "import framers"
	@python -c "import mods"
	mkdir -p build
	grcc $< -d $(@D)
	@sed -i 's/'\
	'dest=\"scan_mode\", type=\"intx\", default=0/'\
	'dest=\"scan_mode\", action=\"store_true\", default=False/g' $@
	@chmod u+x $@
	python -m compileall $@
	f=$@ && x=$${f%.py} && y="$${x//_/-}" &&\
	echo "#!/bin/bash" > $$y &&\
	echo "/usr/bin/python $(DESTDIR)/usr/lib/bs-rx/$(@F)c \"\$$@\"" >> $$y

# Build GR Framers
framers: $(GR_FRAMERS_BUILD_RC)

$(GR_FRAMERS_BUILD_RC):
	@if [ ! -d "gr-framers" ]; then\
		git clone $(GR_FRAMERS_REPO);\
	fi
	mkdir -p $(GR_FRAMERS_BUILD_DIR)
	cd $(GR_FRAMERS_BUILD_DIR) && git pull origin master && \
	cmake .. && make
	touch $(GR_FRAMERS_BUILD_RC)

# Install gr-framers
install-framers: $(GR_FRAMERS_BUILD_RC)
	cd $(GR_FRAMERS_BUILD_DIR) && make DESTDIR=$(DESTDIR) install

# Build GR Mods
mods: $(GR_MODS_BUILD_RC)

$(GR_MODS_BUILD_RC): $(MOD_CC) $(MOD_I_H) $(MOD_H) $(MOD_XML) $(MOD_PY)
	mkdir -p $(GR_MODS_BUILD_DIR)
	cd $(GR_MODS_BUILD_DIR) && cmake .. && make
	touch $(GR_MODS_BUILD_RC)

# Install GR Mods
install-mods: $(GR_MODS_BUILD_RC)
	cd $(GR_MODS_BUILD_DIR) && make DESTDIR=$(DESTDIR) install

install:
	mkdir -p $(DESTDIR)/usr/bin
	mkdir -p $(DESTDIR)/usr/lib/bs-rx
	install -m 0644 build/bs_*.py* $(DESTDIR)/usr/lib/bs-rx/
	cd build && ls | grep -v '\.py*' | \
	xargs -L 1 -I '{}' install -m 0755 '{}' $(DESTDIR)/usr/bin/

# Clean builds
clean-framers:
	rm -f $(GR_FRAMERS_BUILD_RC)
	$(MAKE) -C $(GR_FRAMERS_BUILD_DIR) clean
	rm -rf $(GR_FRAMERS_BUILD_DIR)

clean-mods:
	rm -f $(GR_MODS_BUILD_RC)
	$(MAKE) -C $(GR_MODS_BUILD_DIR) clean
	rm -rf $(GR_MODS_BUILD_DIR)

clean:
	rm -f $(GRC_PY_FILES)
	rm -r build/

# Uninstall
uninstall-framers:
	rm -f $(GR_FRAMERS_BUILD_RC)
	$(MAKE) -C $(GR_FRAMERS_BUILD_DIR) uninstall

uninstall-mods:
	rm -f $(GR_MODS_BUILD_RC)
	$(MAKE) -C $(GR_MODS_BUILD_DIR) uninstall

uninstall:
	rm $(DESTDIR)/usr/lib/bs_rx*
	rm $(DESTDIR)/usr/bin/bs-rx*

# Re-build Hierarchical Blocks
# NOTE: the hierarchical blocks are pre-built in the repository due to the fact
# that the top-level Python modules that they generate have been
# customized. They should only be re-built in case there is some
# incompatibility. In this case, the customizations in the top-level Python need
# to be restored. These are easily tracked by using "git diff".
hier: clean-hier build-hier

build-hier: $(HIER_RC)

grc/hier/%.build_record: grc/hier/%.grc
	grcc $<
	mv $(HOME)/.grc_gnuradio/$(*F).py gr-mods/python/
	mv $(HOME)/.grc_gnuradio/$(*F).py.xml gr-mods/grc/mods_$(*F).xml
	$(warning Build of hier blocks discards required python customizations)
	$(info Check the changes using git and restore the customizations)
	touch grc/hier/$(*F).build_record

clean-hier:
	-rm $(HIER_PY_FILES)
	-rm $(HIER_RC)
