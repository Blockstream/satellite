---
title: Home
nav_order: 1
---

# Blockstream Satellite

## Overview

The Blockstream Satellite network broadcasts the Bitcoin blockchain worldwide
24/7 for free, protecting against network interruptions and providing areas
without reliable internet connection with the opportunity to use Bitcoin. You
can join this network by running your own Blockstream Satellite receiver
node. This document guides you over all the hardware options, software
components, and assembly instructions.

The first step to get started is to get the required hardware. As detailed in
this guide, there is a range of options to suit your needs. Additionally, you
need a host computer running a few software components. One of them is the
[Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite/)
application, a fork of Bitcoin Core with custom capabilities to receive the
Bitcoin blocks and transactions transmitted over satellite.

More importantly, you need to be in a location with coverage and clear
line-of-sight to the satellite in the sky. You can confirm whether your area is
covered by looking at our [Coverage
Map](https://blockstream.com/satellite/#satellite_network-coverage).

Once you get your receiver node up and running, there is a lot that you can do
with it. You can use it as a satellite-connected Bitcoin node offering
redundancy and protection from internet failures to connected
peers. Alternatively, you can run it as your primary Bitcoin full node, either
with hybrid connectivity (internet and satellite) or satellite-connected
only. The satellite network broadcasts new blocks and transactions, as well as
the complete block history. Hence, you can synchronize the entire blockchain
from scratch using the satellite connection only.

You can also send your own encrypted messages worldwide through the satellite
network using our [Satellite API](doc/api.md) while paying for each transmission
through the Lightning Network. Moreover, if you run a Lightning node, you can
sync it faster through [Lightning gossip
snapshots](doc/api.md#lightning-gossip-snapshots) sent over satellite. You can
even [download the Bitcoin source code](doc/api.md#bitcoin-source-code-messages)
over satellite and bootstrap the node without ever touching the internet.

The remainder of this guide covers the essential steps to get you started. In
summary, you will need to:

1. Get the required hardware, such as a
   [DVB-S2](https://en.wikipedia.org/wiki/DVB-S2) receiver and a compatible
   satellite antenna.
2. Install all software requirements, configure the receiver, and configure the
   host.
3. Align your satellite dish appropriately to receive the Blockstream Satellite
   signal.
4. Run the Bitcoin Satellite and Satellite API applications.

## Hardware

The quickest way to get started is by purchasing a Satellite Kit on [Blockstream
Store](https://store.blockstream.com/product-category/satellite_kits/).

In summary, there are four supported receiver types with varying offerings in
terms of budget, performance, CPU usage, form factor, and compatibility. They
are compared below:

| Receiver   | Kit Available                                                                             | Budget | Performance | CPU  | Form Factor | Dual-Sat<sup>*</sup> | Band |
|------------|-------------------------------------------------------------------------------------------|--------|-------------|------|-------------|----------------------|------|
| SDR        | :heavy_multiplication_x:                                                                  | Low    | Limited     | High | USB Dongle  | No                   | C/Ku |
| Linux USB  | :heavy_multiplication_x:                                                                  | Medium | Excellent   | Low  | USB Device  | No                   | C/Ku |
| Standalone | [Pro Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/)           | High   | Excellent   | None | Standalone  | Yes                  | C/Ku |
| Sat-IP     | [Base Station](https://store.blockstream.com/product/blockstream-satellite-base-station/) | Medium | Excellent   | None | All-in-one  | No                   | Ku   |

<sup>*</sup> Specific to locations with overlapping coverage from two
satellites.

The [Satellite Base
Station](https://store.blockstream.com/product/blockstream-satellite-base-station/)
Sat-IP receiver is the only all-in-one hardware option (an antenna with an
integrated receiver and
[LNB](https://en.wikipedia.org/wiki/Low-noise_block_downconverter)). Hence, it
is our go-to receiver choice, with a minimalist design, simplified setup, and
sufficient performance for most Bitcoin users' needs. However, note it has
limited compatibility in the Asia-Pacific region, particularly in locations
covered only by the Telstar 18V C band beam (check the [coverage
map](https://blockstream.com/satellite/#satellite_network-coverage)). Everywhere
else, the base station is compatible.

In all other setup options, the following hardware components are required in
addition to the receiver:

| Component                           | Region-Specific |
|-------------------------------------|-----------------|
| Satellite dish (antenna)            | Yes             |
| Low-noise block downconverter (LNB) | Yes             |
| LNB mounting bracket                | No              |
| Coaxial Cable                       | No              |

Note that both the satellite dish and the LNB are **region-specific**. That is,
they must attend to the frequency band of the signal covering your
region. Furthermore, note that other specific complementary components may be
required, such as connectors, power supply, etc. Please refer to the
[hardware section](doc/hardware.md) to pick the right parts or visit [our
store](https://store.blockstream.com/product-category/satellite_kits/).

## Software and Setup Configuration

The Blockstream Satellite command-line interface (CLI) is required to configure
and run your receiver. You can install it by executing the following command on
the terminal:

```
sudo pip3 install blocksat-cli
```

> NOTE:
>
> 1. The CLI requires Python 3 and the above command requires Python3's package
>    installer ([pip3](https://pip.pypa.io/en/stable/installing/)).
> 2. Some blocksat-cli commands require root access, so it is preferable to run
>    the installation command using `sudo`.

Next, run the configuration helper:

```
blocksat-cli cfg
```

Then, check out the instructions for your setup by running:

```
blocksat-cli instructions
```

Within the set of instructions, one of the required steps is the installation of
software dependencies, which is accomplished by the following command:

```
blocksat-cli deps install
```

After following the instructions, the next steps include the receiver/host
configuration, the [Bitcoin Satellite](doc/bitcoin.md) installation, and the
[antenna pointing](doc/antenna-pointing.md). Please follow the instructions in
this guide.

A [quick reference guide](doc/quick-reference.md) is available if you are
familiar with the commands and steps of the process. Moreover, if you have
purchased a [satellite
kit](https://store.blockstream.com/product-category/satellite_kits/), you can
follow the kit-specific instructions available on [Blockstream's Help
Center](https://help.blockstream.com/hc/en-us/articles/900001613686).
Otherwise, we recommend continuing on this guide. You can move to the next
section, which covers the [hardware options](doc/hardware.md).

## Support

For additional help, you can join the **#blockstream-satellite** IRC channel on
freenode or contact [Blockstream Support](https://help.blockstream.com/).


