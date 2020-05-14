# Blockstream Satellite

This repository contains tools and instructions for running a Blockstream
Satellite receiver.

The Blockstream Satellite network broadcasts the Bitcoin blockchain using the
[second-generation Digital Video Broadcasting Satellite (DVB-S2)
standard](https://en.wikipedia.org/wiki/DVB-S2). To receive this signal, you
will need a DVB-S2 receiver, for which there are a couple of options. The
receiver output will be a data stream that you will feed to a host running the
[Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite/)
application. This application, in turn, will decode the blocks received over
satellite and keep the blockchain in sync.

Find out if your location has coverage by looking at our [Coverage
   Map](https://blockstream.com/satellite/#satellite_network-coverage).

To assemble a receiver setup, you will need to go through the following steps:

1. Get the required hardware, such as the DVB-S2 receiver, the satellite
   dish/antenna and the low-noise block downconverter (LNB).
2. Install all software requirements, configure the receiver, and configure the
   host.
3. Align your satellite dish appropriately to receive the Blockstream Satellite
   signal.

You can find detailed guidance for these steps on this documentation.

## Hardware

The first step to getting started with Blockstream Satellite is to gather all
the required hardware components. Satellite Kits with all parts included are
available at the [Blockstream
Store](https://store.blockstream.com/product-category/satellite_kits/).

There are three supported options with varying levels of budget, performance,
CPU usage, and form factors. They are summarized in the table below:

| **Setup**                        | Kit Available                                                                             | Budget          | Performance/Reliability | CPU Usage  | Form Factor | Dual Satellite* |
|----------------------------------|-------------------------------------------------------------------------------------------|-----------------|-------------------------|------------|-------------|-----------------|
| **Software-defined Radio (SDR)** | :heavy_multiplication_x:                                                                  | Most Affordable | Limited                 | High       | USB Dongle  | No              |
| **Linux USB Receiver**           | [Basic Kit](https://store.blockstream.com/product/blockstream-satellite-basic-kit/)       | Moderate        | Excellent               | Low        | USB Device  | No              |
| **Standalone Receiver**          | [Pro Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/)           | Higher          | Excellent               | None       | Standalone  | Yes             |

<sup>*</sup> Specific to locations that have overlapping coverage from two satellites.

In all options, the following hardware components are required:

| Component                | Region-Specific | General Requirements |
|--------------------------|-----------------|----------------------------|
| Satellite dish (antenna) | Yes             | Diameter of 45cm or larger |
| LNB                      | Yes             | Must be a **PLL LNB** with linear polarization and stability of `+- 250 kHz` or less |
| LNB mounting bracket     | No              |                            |
| Coaxial Cable            | No              | RG6 Cable                  |

Note that both the satellite dish and the LNB are **region-specific**, that is,
they must attend to the specifications of the satellite that covers your
region. This is because they must be appropriate for the frequency band of your
satellite.

An alternative to the satellite dish and LNB is the [Flat Panel
Antenna](https://store.blockstream.com/product/flat-panel-antenna/), available
at the Blockstream Store. This antenna includes the functionality of the LNB
internally, so it substitutes the dish, LNB and mounting bracket
altogether. However, note it only works in Ku band (i.e. does not work with
satellite T18V C band).

Additionally, each of the above three setups has specific complementary
components, which are summarized below:

| Setup | Specific Components |
|--------------------|---------|
| Software-defined Radio (SDR) | RTL-SDR dongle, LNB Power Supply, SMA Cable and SMA to F adapter |
| Linux USB Receiver | TBS5927 Professional DVB-S2 TV Tuner USB |
| Standalone Receiver | Novra S400 PRO DVB satellite Receiver and Ethernet Cable  |

Please refer to the comprehensive [hardware guide](doc/hardware.md) in order to
pick the appropriate components or visit [our
store](https://store.blockstream.com/product-category/satellite_kits/).

## Software and Setup Configuration

Setup configurations are dependent on your receiver choice and on the satellite
that covers your region. To obtain the configuration instructions for your
setup, please use the Blockstream Satellite command-line interface (CLI).

First, install the CLI as follows:

```
sudo pip3 install blocksat-cli
```

> NOTE:
> 1. The CLI requires Python 3.
> 2. Some blocksat-cli commands require root access, so it is preferable to run
> the installation using `sudo`.

Next, run the configuration helper:

```
blocksat-cli cfg
```

Then, run the instructions helper and follow the instructions:

```
blocksat-cli instructions
```

Within the set of instructions, a common required step is the installation of
software dependencies, which is accomplished with the following command:

```
blocksat-cli deps install
```

After following all instructions, the next steps include the receiver/host
configuration, the installation of [Bitcoin Satellite](doc/bitcoin.md) and the
[antenna pointing](doc/antenna-pointing.md). Please follow the user guide.

A [quick reference guide](doc/quick-reference.md) is available if you are
familiar with the commands and steps of the process. Otherwise, we commend
following the detailed user guide below:

## User Guide

- [Frequency Bands](doc/frequency.md)
- [Hardware Guide](doc/hardware.md)
- Receiver Configuration:
    - [Novra S400](doc/s400.md)
    - [TBS5927](doc/tbs.md)
    - [SDR Setup](doc/sdr.md)
- [Antenna Pointing](doc/antenna-pointing.md)
- [Bitcoin Satellite](doc/bitcoin.md)
- Further Information
  - [Quick Reference](doc/quick-reference.md)
  - [Dual-Satellite Reception](doc/dual-satellite.md)
  - [Satellite API](doc/api.md)

## Support

For additional help, you can join the **#blockstream-satellite** IRC channel on
freenode.

