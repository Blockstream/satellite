# Selfsat>IP22 Sat-IP Receiver

The Selfsat>IP22 is an all-in-one flat-panel antenna with an integrated DVB-S2
receiver and LNB. It is the basis of the Blockstream Satellite Base Station kit
available on the [Blockstream
Store](https://store.blockstream.com/product/blockstream-satellite-base-station/).
This device receives the satellite signal and outputs IP packets to one or more
[Sat-IP clients](https://en.wikipedia.org/wiki/Sat-IP) listening to it in the
local network. This page explains how you can connect to the base station device
to receive the Blockstream Satellite traffic.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Sat-IP Receiver](#sat-ip-receiver)
    - [Connections](#connections)
    - [Software Requirements](#software-requirements)
    - [Running](#running)
    - [Next Steps](#next-steps)
    - [Further Information](#further-information)
        - [Software Updates](#software-updates)
        - [Docker](#docker)
        - [Compilation from Source](#compilation-from-source)

<!-- markdown-toc end -->


## Connections

- Connect the Ethernet cable from your switch or computer's network adapter
  directly to the antenna's Sat>IP port.
- If your switch/adapter does not support [Power over Ethernet
  (PoE)](https://en.wikipedia.org/wiki/Power_over_Ethernet), insert a PoE
  injector in-line between the switch/adapter and the antenna's Sat-IP
  port. Connect the injector's PoE-enabled port to the Sat-IP antenna and the
  non-powered (non-PoE) port to the switch/adapter.

**IMPORTANT**: If using a PoE injector, make sure you are connecting the correct
ports. Permanent damage may occur to your switch or network adapter otherwise.

## Software Requirements

To install the required applications, run:

```
blocksat-cli deps install
```

> Note: this command supports the two most recent releases of Ubuntu LTS,
> Fedora, and CentOS. In case you are using another Linux distribution or
> version, please refer to the [compilation
> instructions](#compilation-from-source).

## Running

You should now be ready to launch the Sat-IP client. You can run it by
executing:

```
blocksat-cli sat-ip
```

> Note: the Sat-IP client discovers the server via
> [UPnP](https://en.wikipedia.org/wiki/Universal_Plug_and_Play). If your network
> blocks this traffic type, you can specify the Sat-IP server's IP address
> (i.e., the Satellite Base Station address) directly using option `-a/--addr`.

## Next Steps

At this point, if your antenna is already correctly pointed, you should be able
to start receiving data on Bitcoin Satellite. Please follow the [instructions
for Bitcoin Satellite configuration](bitcoin.md). If your antenna is not aligned
yet, refer to the [antenna alignment guide](antenna-pointing.md).

## Further Information

### Software Updates

To stay up-to-date with the Sat-IP client software, run the following to search
for updates and install them when available:

```
blocksat-cli deps update
```

### Docker

A Docker image is available for running the Sat-IP client on a container. Please
refer to the instructions on the [Docker guide](docker.md).

### Compilation from Source

The Sat-IP setup relies on the [TSDuck](https://tsduck.io/) application. To
build and install it from source, run:

```
git clone https://github.com/tsduck/tsduck.git
cd tsduck
build/install-prerequisites.sh
make NOTELETEXT=1 NOSRT=1 NOPCSC=1 NODTAPI=1
sudo make NOTELETEXT=1 NOSRT=1 NOPCSC=1 NODTAPI=1 install
```

> Refer to [TSDuck's documentation](https://tsduck.io/doxy/building.html) for
> further information.

---

Prev: [Receiver Setup](receiver.md) - Next: [Bitcoin Satellite](bitcoin.md) or [Antenna Pointing](antenna-pointing.md)
