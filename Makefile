PY_FILES   = $(shell find . -type f -name '*.py')
VERSION    = $(shell grep "__version__ =" blocksatcli/main.py | cut -d '"' -f2)
SDIST      = dist/blocksat-cli-$(VERSION).tar.gz
SDIST_UNDERSCORE = dist/blocksat_cli-$(VERSION).tar.gz
WHEEL      = dist/blocksat-cli-$(VERSION)-py3-none-any.whl
WHEEL_UNDERSCORE = dist/blocksat_cli-$(VERSION)-py3-none-any.whl
DISTRO     = ubuntu:jammy
DISTRO_ALT = $(subst :,-,$(DISTRO))
PLATFORM   = linux/amd64,linux/arm64
DOCKERHUB_REPO = blockstream
MANPAGE    = blocksat-cli.1
COMPLETION = blocksat-cli.bash-completion

.PHONY: all clean clean-py sdist wheel install docker pypi testpypi manpage completion

all: sdist

clean: clean-py

clean-py:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -f $(MANPAGE)
	rm -f $(COMPLETION)
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

$(SDIST): $(PY_FILES)
	python3 setup.py sdist
	mv $(SDIST_UNDERSCORE) $(SDIST) || true

# NOTE: depending on the setuptools version, the generated sdist and wheel file
# names may have an underscore instead of a dash. Rename them to the expected
# names with a dash.

sdist: $(SDIST)

$(WHEEL): $(PY_FILES)
	python3 setup.py bdist_wheel
	mv $(WHEEL_UNDERSCORE) $(WHEEL) || true

wheel: $(WHEEL)

install: $(SDIST)
	pip3 install $(SDIST)[fec]

manpage: $(MANPAGE)

$(MANPAGE): $(PY_FILES)
	help2man ./blocksat-cli.py -o $@ -s 1

completion: $(COMPLETION)

$(COMPLETION): $(PY_FILES)
	shtab blocksatcli.main.get_parser -s bash > $@

pypi: clean sdist wheel
	python3 -m twine upload --repository pypi \
		dist/blocksat-cli-$(VERSION).tar.gz \
		dist/blocksat-cli-$(VERSION)-*.whl

testpypi: clean sdist wheel
	python3 -m twine upload --repository testpypi \
		dist/blocksat-cli-$(VERSION).tar.gz \
		dist/blocksat-cli-$(VERSION)-*.whl

docker: $(SDIST) $(MANPAGE) $(COMPLETION)
	docker build --build-arg distro=$(DISTRO) \
	--build-arg version=$(VERSION) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(DISTRO_ALT) \
	-t $(DOCKERHUB_REPO)/satellite:$(VERSION) \
	-f docker/blocksat-host.docker .

docker-push: docker
	docker push $(DOCKERHUB_REPO)/satellite

docker-buildx: $(SDIST) $(MANPAGE) $(COMPLETION)
	docker buildx build --platform $(PLATFORM) \
	--build-arg distro=$(DISTRO) \
	--build-arg version=$(VERSION) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(VERSION) \
	-f docker/blocksat-host.docker .

docker-buildx-push: $(SDIST) $(MANPAGE) $(COMPLETION)
	docker buildx build --platform $(PLATFORM) --push \
	--build-arg distro=$(DISTRO) \
	--build-arg version=$(VERSION) \
	-t $(DOCKERHUB_REPO)/satellite \
	-t $(DOCKERHUB_REPO)/satellite:$(VERSION) \
	-f docker/blocksat-host.docker .
