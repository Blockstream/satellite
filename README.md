# Blockstream Satellite

This repository contains tools and instructions for running a Blockstream
Satellite receiver.

The Blockstream Satellite network broadcasts the Bitcoin blockchain using the
[second-generation Digital Video Broadcasting Satellite (DVB-S2)
standard](https://en.wikipedia.org/wiki/DVB-S2). To receive this signal, you
need a DVB-S2 receiver, for which there are a couple of options. The receiver
outputs a data stream that can be fed to a host running the [Bitcoin
Satellite](https://github.com/Blockstream/bitcoinsatellite/) application. This
application, in turn, decodes the blocks received over satellite and keeps the
blockchain in sync.

Find out if your location has coverage by looking at our [Coverage
   Map](https://blockstream.com/satellite/#satellite_network-coverage).

To assemble a receiver setup, you will need to go through the following steps:

1. Get the required hardware, such as the DVB-S2 receiver, the satellite
   dish/antenna, and the low-noise block downconverter (LNB).
2. Install all software requirements, configure the receiver, and configure the
   host.
3. Align your satellite dish appropriately to receive the Blockstream Satellite
   signal.

You can find detailed guidance for these steps in this documentation.

## Hardware

The first step to getting started with Blockstream Satellite is to gather all
the required hardware components. Satellite Kits with all parts included are
available at the [Blockstream
Store](https://store.blockstream.com/product-category/satellite_kits/).

There are four supported setup options with varying combinations of budget,
performance, CPU usage, form factor, and compatibility. They are summarized
below:

| **Setup**                        | Kit Available                                                                             | Budget          | Performance/Reliability | CPU Usage  | Form Factor | Dual Satellite<sup>*</sup> | C-band Compatible |
|----------------------------------|-------------------------------------------------------------------------------------------|-----------------|-------------------------|------------|-------------|--------------------------|------------------------|
| **Software-defined Radio (SDR)** | :heavy_multiplication_x:                                                                  | Most Affordable | Limited                 | High       | USB Dongle  | :heavy_multiplication_x: | :heavy_check_mark:                    |
| **Linux USB Receiver**           | :heavy_multiplication_x:                                                                  | Moderate        | Excellent               | Low        | USB Device  | :heavy_multiplication_x: | :heavy_check_mark:                    |
| **Standalone Receiver**          | [Pro Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/)           | Higher          | Excellent               | None       | Standalone  | :heavy_check_mark:       | :heavy_check_mark:                    |
| **Sat-IP Receiver**              | [Satellite Base Station](https://store.blockstream.com/product/blockstream-satellite-base-station/)  | Moderate        | Excellent               | None       | All-in-one  | :heavy_multiplication_x: | :heavy_multiplication_x:                     |

<sup>*</sup> Specific to locations with overlapping coverage from two satellites.

The [Satellite Base
Station](https://store.blockstream.com/product/blockstream-satellite-base-station/) Sat-IP
receiver is the only all-in-one hardware option (an antenna with an integrated
receiver and LNB). Hence, it is our go-to receiver choice, with a minimalist
design, simplified setup, and sufficient performance for most Bitcoin users'
needs. However, note it only works in [Ku
band](doc/frequency.md#signal-bands). That is, it does not work with the Telstar
18V C band satellite covering the Asia-Pacific region.

In all other setup options, the following hardware components are required in
addition to the receiver:

| Component                | Region-Specific | General Requirements |
|--------------------------|-----------------|----------------------------|
| Satellite dish (antenna) | Yes             | Diameter of 45cm or larger |
| LNB                      | Yes             | Must be a **PLL LNB** with linear polarization and stability of `+- 250 kHz` or less |
| LNB mounting bracket     | No              |                            |
| Coaxial Cable            | No              | RG6 Cable                  |

Note that both the satellite dish and the LNB are **region-specific**. That is,
they must attend to the frequency band of the signal covering your region.

Additionally, each of the above three setups has specific complementary
components, summarized below:

| Setup | Specific Components |
|--------------------|---------|
| Software-defined Radio (SDR) | RTL-SDR dongle, LNB Power Supply, SMA Cable, and SMA to F adapter |
| Linux USB Receiver | TBS5927 Professional DVB-S2 TV Tuner USB |
| Standalone Receiver | Novra S400 PRO DVB satellite Receiver and Ethernet Cable  |

Please refer to the comprehensive [hardware guide](doc/hardware.md) to pick the
appropriate components or visit [our
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
> 1. The CLI requires Python 3.
> 2. Some blocksat-cli commands require root access, so it is preferable to run
> the installation command using `sudo`.

Next, run the configuration helper:

```
blocksat-cli cfg
```

Then, run the instructions helper and follow the instructions:

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
[antenna pointing](doc/antenna-pointing.md). Please follow the user guide.

A [quick reference guide](doc/quick-reference.md) is available if you are
familiar with the commands and steps of the process. Otherwise, we recommend
following the detailed user guide below.

## User Guide

- [Frequency Bands](doc/frequency.md)
- [Hardware Guide](doc/hardware.md)
- Receiver Setup:
    - [Novra S400 Standalone Receiver](doc/s400.md)
    - [TBS 5927 Linux USB Receiver](doc/tbs.md)
    - [Satellite Base Station Sat-IP Receiver](doc/sat-ip.md)
	- [SDR Receiver](doc/sdr.md)
- [Antenna Pointing](doc/antenna-pointing.md)
- [Bitcoin Satellite](doc/bitcoin.md)
- Further Information
  - [Quick Reference](doc/quick-reference.md)
  - [Dual-Satellite Reception](doc/dual-satellite.md)
  - [Satellite API](doc/api.md)
  - [Running on Docker](doc/docker.md)

## Support

For additional help, you can join the **#blockstream-satellite** IRC channel on
freenode.

