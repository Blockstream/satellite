---
nav_order: 9
---

# Running on Docker

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Standalone Receiver](#standalone-receiver)
- [USB Receiver](#usb-receiver)
- [SDR Receiver](#sdr-receiver)
- [Sat-IP Receiver](#sat-ip-receiver)
- [Bitcoin Satellite](#bitcoin-satellite)
- [Build the Docker Image Locally](#build-the-docker-image-locally)

<!-- markdown-toc end -->


A Docker image is available to be used as the *Blockstream Satellite host*, that is, the system with everything you need to interface with the supported satellite receivers. All you need to do is run the `blockstream/satellite` Docker image while providing the appropriate resources to the container. This process is explained next.

## Standalone Receiver

There are no special requirements to communicate with the standalone receiver from a container. You can launch the `satellite` image as follows:

```
docker run --rm -it \
    -v blocksat-cfg:/root/.blocksat/ \
    blockstream/satellite
```

Note the `blocksat-cfg` named volume is meant to provide persistent storage for the configurations created by `blocksat-cli`.

## USB Receiver

First of all, there is an important limitation to running a Linux USB receiver inside a container. The USB receiver's drivers must be installed on the Docker host, not on the Docker container. Hence, the referred `blockstream/satellite` image does not contain the drivers. Instead, you will need to install the drivers on your Docker host. Please refer to the driver installation instructions on the [USB receiver guide](tbs.md#tbs-drivers).

Next, after installing the drivers and connecting the USB receiver to your host, you can start the container. Just note that you will need to share the DVB network interface (visible on the Docker host) with the container. To do so, check the DVB interface at `/dev/dvb/` (typically named `adapter0`) and assign it to the container using option `--device` as follows:

```
docker run --rm -it \
    --device=/dev/dvb/adapter0 \
    --network=host \
    --cap-add=NET_ADMIN \
    --cap-add=SYS_ADMIN \
    -v blocksat-cfg:/root/.blocksat/ \
    blockstream/satellite
```

After that, you can run the [USB configuration command](tbs.md#configure-the-host) inside the container:

```
blocksat-cli usb config
```

The above step creates a network interface (typically named `dvb0_0`), configures the appropriate firewall rules, and assigns an IP address to the interface. Additionally, it configures the so-called reverse-path filtering rule for the interface. However, this particular configuration will not take effect when executed inside the container, as the container does not have permission to change the reverse-path filtering rules. Hence, to complete the configuration, run the following command directly from the host instead:

```
blocksat-cli rp -i dvb0_0
```

> Note: If your network interface is named differently (not `dvb0_0`), you can find its name by running: `ip link show | grep dvb`.

Finally, launch the receiver inside the container:

```
blocksat-cli usb launch
```

## SDR Receiver

The important point for running the SDR receiver inside a container is that you need to share the RTL-SDR USB device (connected to the Docker host) with the container. To do so, run the container as follows:

```
docker run --rm -it \
    --privileged \
    -v /dev/bus/usb:/dev/bus/usb \
    -v blocksat-cfg:/root/.blocksat/ \
    blockstream/satellite
```

Note **privileged mode** is used to grant access to the RTL-SDR USB device. Furthermore, it is used to allow the execution of `sysctl`, which the SDR application uses for changing option `fs.pipe-max-size`.

> On a Mac OSX host, you will need to set up a [docker-machine](https://docs.docker.com/machine/) to share the SDR USB device. Once the docker-machine is active, you can share the USB device through the [machine driver's settings](https://github.com/machine-drivers). Then, run the above `docker run` command normally.

## Sat-IP Receiver

The essential point for running the Sat-IP client inside a container concerns the network configuration. By default, the Sat-IP client discovers the Sat-IP server via [UPnP](https://en.wikipedia.org/wiki/Universal_Plug_and_Play). However, the discovery mechanism does not work if the container runs on an isolated network. To solve the problem, you need to launch the container using option `--network=host` as follows:

```
docker run --rm -it \
    --network=host \
    -v blocksat-cfg:/root/.blocksat/ \
    blockstream/satellite
```

Alternatively, if you know the IP address of the Sat-IP receiver, you can specify it directly using option `-a/--addr` when running the Sat-IP client. In this case, you don't need the `--network=host` option when launching the container.

## Bitcoin Satellite

In addition to controlling or running the satellite receivers, you can also run [Bitcoin Satellite](bitcoin.md) using the `satellite` container image. For example, you can run the following:

```
docker run --rm -it \
    -v ~/.bitcoin/:/root/.bitcoin/ \
    -v blocksat-cfg:/root/.blocksat/ \
    blockstream/satellite
```

> NOTE: with option `-v ~/.bitcoin/:/root/.bitcoin/`, the `bitcoind` application running inside the container will use the host's `~/.bitcoin/` directory as its Bitcoin [data directory](https://en.bitcoin.it/wiki/Data_directory).

Then, inside the container, run `bitcoind` as usual.

Also, if you have not generated your `bitcoin.conf` [configuration file](bitcoin.md#configuration) yet, you can run the following inside the container:

```
blocksat-cli btc
```

## Build the Docker Image Locally

You can also build the Docker image locally, rather than pulling it from Docker Hub. To do so, run the following from the root directory of this repository:

```
make docker
```
