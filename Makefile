PY_FILES   = $(shell find blocksatcli -type f -name '*.py')
VERSION    = $(shell grep "__version__ =" blocksatcli/main.py | cut -d '"' -f2)
DIST       = dist/blocksat-cli-$(VERSION).tar.gz
DISTRO     = ubuntu:bionic
DISTRO_ALT = $(subst :,-,$(DISTRO))

.PHONY: all docker clean clean-py pip

all: docker

clean: clean-py

clean-py:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

$(DIST): $(PY_FILES)
	python3 setup.py sdist

docker: $(DIST)
	docker build --build-arg distro=$(DISTRO) \
	-t blockstream/blocksat-host \
	-t blockstream/blocksat-host-$(DISTRO_ALT) \
	-f docker/blocksat-host.docker .

pip: clean
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload --repository pypi dist/*

