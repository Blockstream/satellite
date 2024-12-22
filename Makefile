PY_FILES   = $(shell find . -type f -name '*.py')
CLI_VERSION = $(shell grep "__version__ =" blocksatcli/__init__.py | cut -d '"' -f2)
GUI_VERSION = $(shell grep "__version__ =" blocksatgui/__init__.py | cut -d '"' -f2)
SDIST_CLI  = dist/blocksat-cli-$(CLI_VERSION).tar.gz
SDIST_GUI  = dist/blocksat-gui-$(GUI_VERSION).tar.gz
WHEEL_CLI  = dist/blocksat-cli-$(CLI_VERSION)-py3-none-any.whl
WHEEL_GUI  = dist/blocksat-gui-$(GUI_VERSION)-py3-none-any.whl
DISTRO     = ubuntu:jammy
DISTRO_ALT = $(subst :,-,$(DISTRO))
PLATFORM   = linux/amd64,linux/arm64
DOCKERHUB_REPO = blockstream
MANPAGE    = blocksat-cli.1
COMPLETION = blocksat-cli.bash-completion

.PHONY: all clean clean-py sdist-cli sdist-gui sdist wheel-cli wheel-gui wheel install docker pypi testpypi manpage completion

all: sdist

check-version:
ifneq ($(CLI_VERSION), $(GUI_VERSION))
	@echo "CLI and GUI versions do not match"
	@exit 1
endif

clean: clean-py

clean-py:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -f $(MANPAGE)
	rm -f $(COMPLETION)
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

# By default, setuptools includes both the setup_cli.py and setup.py files on
# the source distribution archive. This causes a problem when installing the
# CLI package via pip because the setup.py file will be used instead of
# setup_cli.py. As a workaround, keep a single setup.py file on the CLI archive
# with the contents from setup_cli.py.
$(SDIST_CLI): $(PY_FILES)
	python3 setup_cli.py sdist -k
	mv blocksat_cli-${CLI_VERSION} blocksat-cli-${CLI_VERSION} || true
	mv blocksat-cli-${CLI_VERSION}/setup_cli.py blocksat-cli-${CLI_VERSION}/setup.py
	tar czf $(SDIST_CLI) blocksat-cli-${CLI_VERSION}
	rm -fr blocksat-cli-${CLI_VERSION}/

# NOTE: depending on the setuptools version, the generated sdist file name may
# have blocksat_cli (with an underscore) instead of blocksat-cli (with a
# hyphen). Rename it to blocksat-cli for consistency.

$(SDIST_GUI): $(PY_FILES)
	python3 setup_gui.py sdist -k
	mv blocksat_gui-${CLI_VERSION} blocksat-gui-${CLI_VERSION} || true
	mv blocksat-gui-${GUI_VERSION}/setup_gui.py blocksat-gui-${GUI_VERSION}/setup.py
	tar czf $(SDIST_GUI) blocksat-gui-${GUI_VERSION}
	rm -fr blocksat-gui-${GUI_VERSION}/

sdist-cli: $(SDIST_CLI)

sdist-gui: $(SDIST_GUI)

sdist: sdist-cli sdist-gui check-version

$(WHEEL_CLI): $(PY_FILES)
	python3 setup_cli.py bdist_wheel

$(WHEEL_GUI): $(PY_FILES)
	python3 setup_gui.py bdist_wheel

wheel-cli: $(WHEEL_CLI)

wheel-gui: $(WHEEL_GUI)

wheel: wheel-cli wheel-gui

install: sdist
	pip3 install $(SDIST_CLI)[fec] $(SDIST_GUI)

manpage: $(MANPAGE)

$(MANPAGE): $(PY_FILES)
	help2man ./blocksat-cli.py -o $@ -s 1

completion: $(COMPLETION)

$(COMPLETION): $(PY_FILES)
	shtab blocksatcli.main.get_parser -s bash > $@

pypi: clean sdist wheel
	python3 -m twine upload --repository pypi \
		dist/blocksat-cli-$(VERSION).tar.gz \
		dist/blocksat_cli-$(VERSION)-*.whl

testpypi: clean sdist wheel
	python3 -m twine upload --repository testpypi \
		dist/blocksat-cli-$(VERSION).tar.gz \
		dist/blocksat_cli-$(VERSION)-*.whl

docker: sdist $(MANPAGE) $(COMPLETION)
	docker build --build-arg distro=$(DISTRO) \
	--build-arg version=$(CLI_VERSION) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(DISTRO_ALT) \
	-t $(DOCKERHUB_REPO)/satellite:$(CLI_VERSION) \
	-f docker/blocksat-host.docker .

docker-push: docker
	docker push $(DOCKERHUB_REPO)/satellite

docker-buildx: sdist $(MANPAGE) $(COMPLETION)
	docker buildx build --platform $(PLATFORM) \
	--build-arg distro=$(DISTRO) \
	--build-arg version=$(CLI_VERSION) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(CLI_VERSION) \
	-f docker/blocksat-host.docker .

docker-buildx-push: sdist $(MANPAGE) $(COMPLETION)
	docker buildx build --platform $(PLATFORM) --push \
	--build-arg distro=$(DISTRO) \
	--build-arg version=$(CLI_VERSION) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(CLI_VERSION) \
	-f docker/blocksat-host.docker .
