SHELL:=/bin/bash

MACHINE    := $(shell uname -m)
OS         := $(shell cat /etc/os-release | grep "^NAME=" | cut -d"=" -f2)

prefix      = /usr/local
exec_prefix = $(prefix)
bindir      = $(exec_prefix)/bin
libdir      = $(exec_prefix)/lib
sharedir    = $(exec_prefix)/share

ifeq ($(MACHINE), x86_64)
ifneq ($(OS), "Ubuntu")
export PYTHONPATH := $(PYTHONPATH):/usr/local/lib64/python2.7/site-packages
endif
endif

XML_PATH = gr-blocksat/grc
LIB_PATH = gr-blocksat/lib
PY_PATH  = gr-blocksat/python
H_PATH   = gr-blocksat/include/blocksat

ifeq ($(GUI), 0)
	GRC_FILES = $(shell find grc/ -maxdepth 1 -type f -name '*.grc' ! \
				  -path '*gui.grc')
else
	GRC_FILES = $(shell find grc/ -maxdepth 1 -type f -name '*.grc')
endif
GRC_PY_FILES      = $(patsubst grc/%.grc, build/%.py, $(GRC_FILES))
GRC_PYC_FILES     = $(patsubst grc/%.grc, build/%.pyc, $(GRC_FILES))
GRC_WRAPPER_FILES = $(subst _,-, $(patsubst grc/%.grc, build/%, $(GRC_FILES)))

XML = $(shell find $(XML_PATH) -type f -name '*.xml')
I_H = $(shell find $(LIB_PATH) -type f -name '*.h')
CC  = $(shell find $(LIB_PATH) -type f -name '*.cc')
PY  = $(shell find $(PY_PATH) -type f -name '*.py')
H   = $(shell find $(H_PATH) -type f -name '*.h')
AFF3CT  = $(shell find $(LIB_PATH) -type f -name '*.cpp')

GR_FRAMERS_REPO       = https://github.com/gr-vt/gr-framers.git
GR_FRAMERS_BUILD_DIR  = gr-framers/build
GR_FRAMERS_BUILD_RC   = build/gr-framers_build_record
GR_BLOCKSAT_BUILD_DIR = gr-blocksat/build
GR_BLOCKSAT_BUILD_RC  = gr-blocksat/build_record

.PHONY: build install clean uninstall blocksat install-blocksat clean-blocksat \
uninstall-blocksat framers install-framers clean-framers uninstall-framers

# Build Rx Flowgraphs
build: $(GRC_PY_FILES)

build/%.py: grc/%.grc
	@echo "Check gr-framers and gr-blocksat installations"
	@python -c "import framers"
	@python -c "import blocksat"
	mkdir -p build
	grcc $< -d $(@D)
	@sed -i 's/'\
	'dest=\"scan_mode\", type=\"intx\", default=0/'\
	'dest=\"scan_mode\", action=\"store_true\", default=False/g' $@
	@sed -i 's/'\
	'dest=\"no_api\", type=\"intx\", default=0/'\
	'dest=\"no_api\", action=\"store_true\", default=False/g' $@
	@chmod u+x $@
	python -m compileall $@
	f=$@ && x=$${f%.py} && y="$${x//_/-}" &&\
	echo "#!/bin/bash" > $$y &&\
	echo "/usr/bin/env python $(libdir)/blocksat-rx/$(@F)c \"\$$@\"" >> $$y

# Build GR Framers
framers: $(GR_FRAMERS_BUILD_RC)

$(GR_FRAMERS_BUILD_RC):
	git submodule update --init gr-framers
	mkdir -p $(GR_FRAMERS_BUILD_DIR)
	cd $(GR_FRAMERS_BUILD_DIR) && cmake .. && make
	mkdir -p build
	touch $(GR_FRAMERS_BUILD_RC)

# Install gr-framers
install-framers: $(GR_FRAMERS_BUILD_RC)
	cd $(GR_FRAMERS_BUILD_DIR) && make DESTDIR=$(DESTDIR) install
	-ldconfig

# Build GR Blocksat
blocksat: $(GR_BLOCKSAT_BUILD_RC)

$(GR_BLOCKSAT_BUILD_RC): $(CC) $(I_H) $(AFF3CT) $(H) $(XML) $(PY)
	git submodule update --init gr-blocksat
	mkdir -p $(GR_BLOCKSAT_BUILD_DIR)
	cd $(GR_BLOCKSAT_BUILD_DIR) && cmake .. && make
	touch $(GR_BLOCKSAT_BUILD_RC)

# Install GR Blocksat
install-blocksat: $(GR_BLOCKSAT_BUILD_RC)
	cd $(GR_BLOCKSAT_BUILD_DIR) && make DESTDIR=$(DESTDIR) install
	-ldconfig

install:
	mkdir -p $(DESTDIR)$(bindir)
	mkdir -p $(DESTDIR)$(libdir)/blocksat-rx
	install -m 0755 build/blocksat_*.py* $(DESTDIR)$(libdir)/blocksat-rx/
	cd build && ls | grep -v '\.py*' | \
	xargs -L 1 -I '{}' install -m 0755 '{}' $(DESTDIR)$(bindir)

install-docs:
	mkdir -p $(DESTDIR)$(sharedir)/doc/satellite/
	mkdir -p $(DESTDIR)$(sharedir)/doc/satellite/api/
	mkdir -p $(DESTDIR)$(sharedir)/doc/satellite/api/examples/
	install -m 0644 README.md $(DESTDIR)$(sharedir)/doc/satellite/
	install -m 0644 api/README.md $(DESTDIR)$(sharedir)/doc/satellite/api/
	install -m 0644 api/examples/*.{md,txt} \
	$(DESTDIR)$(sharedir)/doc/satellite/api/examples/
	install -m 0755 api/examples/*.py \
	$(DESTDIR)$(sharedir)/doc/satellite/api/examples/

# Clean builds
clean-framers:
	rm -f $(GR_FRAMERS_BUILD_RC)
	$(MAKE) -C $(GR_FRAMERS_BUILD_DIR) clean
	rm -rf $(GR_FRAMERS_BUILD_DIR)

clean-blocksat:
	rm -f $(GR_BLOCKSAT_BUILD_RC)
	$(MAKE) -C $(GR_BLOCKSAT_BUILD_DIR) clean
	rm -rf $(GR_BLOCKSAT_BUILD_DIR)

clean:
	rm -f $(GRC_PY_FILES)
	rm -f $(GRC_PYC_FILES)
	rm -f $(GRC_WRAPPER_FILES)

# Uninstall
uninstall-framers:
	rm -f $(GR_FRAMERS_BUILD_RC)
	$(MAKE) -C $(GR_FRAMERS_BUILD_DIR) uninstall

uninstall-blocksat:
	rm -f $(GR_BLOCKSAT_BUILD_RC)
	$(MAKE) -C $(GR_BLOCKSAT_BUILD_DIR) uninstall

uninstall:
	rm $(DESTDIR)$(libdir)/blocksat-rx/blocksat_rx*
	rm $(DESTDIR)$(bindir)/blocksat-rx*

uninstall-docs:
	rm -r $(DESTDIR)$(sharedir)/doc/satellite/

