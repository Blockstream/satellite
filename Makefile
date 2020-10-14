PY_FILES   = $(shell find . -type f -name '*.py')
VERSION    = $(shell grep "__version__ =" blocksatcli/main.py | cut -d '"' -f2)
SDIST      = dist/blocksat-cli-$(VERSION).tar.gz
WHEEL      = dist/blocksat-cli-$(VERSION)-py3-none-any.whl
DISTRO     = ubuntu:focal
DISTRO_ALT = $(subst :,-,$(DISTRO))
DOCKERHUB_REPO = blockstream

.PHONY: all clean clean-py sdist wheel install docker pypi

all: sdist

clean: clean-py

clean-py:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

$(SDIST): $(PY_FILES)
	python3 setup.py sdist

sdist: $(SDIST)

$(WHEEL): $(PY_FILES)
	python3 setup.py bdist_wheel

wheel: $(WHEEL)

install: $(SDIST)
	pip3 install $(SDIST)

docker: $(SDIST)
	docker build --build-arg distro=$(DISTRO) \
	-t $(DOCKERHUB_REPO)/blocksat-host \
	-t $(DOCKERHUB_REPO)/blocksat-host-$(DISTRO_ALT) \
	-f docker/blocksat-host.docker .

pypi: clean sdist wheel
	python3 -m twine upload --repository pypi dist/*

docker-push: docker
	docker push $(DOCKERHUB_REPO)/blocksat-host
