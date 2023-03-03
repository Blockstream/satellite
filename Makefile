PY_FILES   = $(shell find . -type f -name '*.py')
VERSION    = $(shell grep "__version__ =" blocksatcli/main.py | cut -d '"' -f2)
SDIST      = dist/blocksat-cli-$(VERSION).tar.gz
WHEEL      = dist/blocksat-cli-$(VERSION)-py3-none-any.whl
DISTRO     = ubuntu:jammy
DISTRO_ALT = $(subst :,-,$(DISTRO))
PLATFORM   = linux/amd64,linux/arm64
DOCKERHUB_REPO = blockstream

.PHONY: all clean clean-py sdist wheel install docker pypi testpypi

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
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(DISTRO_ALT) \
	-t $(DOCKERHUB_REPO)/satellite:$(VERSION) \
	-f docker/blocksat-host.docker .

pypi: clean sdist wheel
	python3 -m twine upload --repository pypi dist/*

testpypi: clean sdist wheel
	python3 -m twine upload --repository testpypi dist/*

docker-push: docker
	docker push $(DOCKERHUB_REPO)/satellite

buildx: $(SDIST)
	docker buildx build --platform $(PLATFORM) \
	--build-arg distro=$(DISTRO) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(VERSION) \
	-f docker/blocksat-host.docker .

buildx-push: $(SDIST)
	docker buildx build --platform $(PLATFORM) --push \
	--build-arg distro=$(DISTRO) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(VERSION) \
	-f docker/blocksat-host.docker .
