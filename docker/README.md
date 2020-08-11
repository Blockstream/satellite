# Running on Docker

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Running on Docker](#running-on-docker)
    - [USB Receiver](#usb-receiver)
    - [SDR Receiver](#sdr-receiver)
    - [Bitcoin Satellite](#bitcoin-satellite)
    - [Build the Docker Image Locally](#build-the-docker-image-locally)

<!-- markdown-toc end -->

A Docker image is available to be used as the *Blockstream Satellite host*, that
is, the machine with everything you need to interface with the supported
satellite receivers. All you need to do is run this `blockstream/blocksat-host`
image via Docker and provide the appropriate resources to the container, as
explained next.

## USB Receiver

First of all, there is an important limitation to running the [Linux USB
receiver](../doc/tbs.md) inside a container. It is that the drivers of the USB
receiver must be installed on the Docker host, rather than the Docker
container. This means that the referred `blockstream/blocksat-host` image does
not contain the drivers. Instead, you will need to install the drivers on your
Docker host. Please refer to the driver installation instructions on the [USB
receiver guide](tbs.md#tbs-5927-drivers).

After installing the drivers and connecting the TBS5927 device to your Docker
host, you can then start the container. You will need to share the DVB network
interfaces (visible in the Docker host) with the container. Check the DVB
interfaces at `/dev/` (typically named `dvb0_0` and `dvb0_1`) and adapt the
command below accordingly:

```
docker run --rm -it \
	--device=/dev/dvb0_0 \
	--device=/dev/dvb0_1 \
	--network=host \
	--cap-add=NET_ADMIN \
	--cap-add=SYS_ADMIN \
	-v blocksat-cfg:/root/.blocksat/ \
	blockstream/blocksat-host
```

After running, configure reverse path filters by running the following on the
Docker host (not from the container):

```
blocksat-cli rp -i dvb0_0
blocksat-cli rp -i dvb0_1
```

## SDR Receiver

The important point for running the SDR receiver inside a container is that you
need to share the RTL-SDR USB device (connected to the Docker host) with the
container. To do so, run the container as follows:

```
docker run --rm -it \
	--privileged \
	-v /dev/bus/usb:/dev/bus/usb \
	-v blocksat-cfg:/root/.blocksat/ \
	blockstream/blocksat-host
```

Note **privileged mode** is used in order to allow the container to access the
RTL-SDR USB device and to allow the execution of `sysctl`, which is used by the
SDR application for changing option `fs.pipe-max-size`.

> On a Mac OSX host, you will need to set up a
> [docker-machine](https://docs.docker.com/machine/) in order share the SDR USB
> device. Once this docker-machine is active, you can share the USB device via
> the settings of the [machine
> driver](https://docs.docker.com/machine/drivers/). Then, run the above `docker
> run` command normally.


## Bitcoin Satellite

In addition to controlling or running the satellite receivers, you can also run
[Bitcoin Satellite](../doc/bitcoin.md) using the `blocksat-host` container. For
example, you can run the following:

```
docker run --rm -it \
	-v ~/.bitcoin/:/root/.bitcoin/ \
	-v blocksat-cfg:/root/.blocksat/ \
	blockstream/blocksat-host
```

> NOTE: with option `-v ~/.bitcoin/:/root/.bitcoin/`, by default `bitcoind`
> running inside the container will use your host's directory `~/.bitcoin/` as
> its Bitcoin [data directory](https://en.bitcoin.it/wiki/Data_directory).

Then, inside the container, run `bitcoind` [as
usual](../doc/bitcoin.md#running).

Also, if you have not [generated your `bitcoin.conf`
configurations](../doc/bitcoin.md#configuration) yet, you can run the following
inside the container:

```
blocksat-cli btc
```

## Build the Docker Image Locally

You can also build the Docker image locally, rather than pulling it from Docker
Hub. To build the image, run the following from the root directory of this
repository:

```
make docker
```
