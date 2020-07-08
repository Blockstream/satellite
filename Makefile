PY_FILES   = $(shell find blocksatcli -type f -name '*.py')
VERSION    = $(shell grep "__version__ =" blocksatcli/main.py | cut -d '"' -f2)
DIST       = dist/blocksat-cli-$(VERSION).tar.gz
DISTRO     = ubuntu:bionic
DISTRO_ALT = $(subst :,-,$(DISTRO))

.PHONY: all clean clean-py sdist wheel install docker pip

all: sdist

clean: clean-py

clean-py:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

$(DIST): $(PY_FILES)
	python3 setup.py sdist

sdist: $(DIST)

wheel: $(DIST)
	python3 setup.py bdist_wheel

install: $(DIST)
	pip3 install $(DIST)

docker: $(DIST)
	docker build --build-arg distro=$(DISTRO) \
	-t blockstream/blocksat-host \
	-t blockstream/blocksat-host-$(DISTRO_ALT) \
	-f docker/blocksat-host.docker .

pip: clean wheel
	python3 -m twine upload --repository pypi dist/*

