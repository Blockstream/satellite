# Blockstream Satellite

This repository contains tools and instructions for running a Blockstream
Satellite receiver.

The Blockstream Satellite network broadcasts the Bitcoin blockchain using the
[second-generation Digital Video Broadcasting Satellite (DVB-S2)
standard](https://en.wikipedia.org/wiki/DVB-S2). To receive this signal, you
will need a DVB-S2 demodulator, for which there are a couple of options. The
output of the demodulator will be a data stream that you will feed to a host
running the [Bitcoin FIBRE](http://bitcoinfibre.org) application. This
application, in turn, will decode the blocks received over satellite and keep
the blockchain in sync.

Find out if your location has coverage by looking at our [Coverage
   Map](https://blockstream.com/satellite/#satellite_network-coverage).

To assemble a receiver setup, you will need to go through the following steps:

1. Get the required hardware, such as the DVB-S2 demodulator, the satellite
   dish/antenna and the low-noise block downconverter (LNB).
2. Install all software requirements and configure the receiver setup.
3. Align your satellite dish appropriately to receive the Blockstream Satellite
   signal.

You can find detailed guidance for these steps along this documentation.

## Hardware

There are 3 supported setup options with varying levels of budget, performance
and CPU usage. They are summarized in the table below:

| **Setup**                        | Budget          | Performance/Reliability | CPU Usage  |
|----------------------------------|-----------------|-------------------------|------------|
| **Software-defined Radio (SDR)** | Most Affordable | Limited                 | High       |
| **Linux USB Receiver**           | Moderate        | Excellent               | Negligible |
| **Standalone Demodulator**       | Higher          | Excellent               | None       |

In all options, the following hardware components are required:

| Component                | Region-Specific | General Requirements |
|--------------------------|-----------------|----------------------------|
| Satellite dish (antenna) | Yes             | Diameter of 45cm or larger |
| LNB                      | Yes             | Must be a **PLL LNB** with linear polarization and stability of `+- 250 kHz` or less |
| LNB mounting bracket     | No              |                            |
| Coaxial Cable            | No              | RG6 Cable                  |

Note both the satellite dish and the LNB are **region-specific**, that is, they
must attend to the specifications of the satellite that covers your region. This
is because they must be appropriate for the frequency band of your satellite.

Additionally, each of the above three setups has specific complementary
components, which are summarized below:

| Setup | Specific Components |
|--------------------|---------|
| Software-defined Radio (SDR) | RTL-SDR dongle, LNB Power Supply, SMA Cable and SMA to F adapter |
| Linux USB Receiver | TBS5927 Professional DVB-S2 TV Tuner USB |
| Standalone Demodulator | Novra S400 PRO DVB satellite Receiver and Ethernet Cable  |

Please refer to the comprehensive [hardware guide](doc/hardware.md) in order to
pick the appropriate components.

## Software and Setup Configuration

Setup configurations are dependent on your demodulator choice and on the
satellite that covers your region. To obtain the configuration instructions that
are suitable to your setup, please run the configuration helper of the
Blockstream Satellite command-line interface (CLI).

First install the CLI as follows:
```
python3 setup.py install
```

Then, run the configuration helper:
```
blocksat-cli cfg
```

Next, build and install Bitcoin FIBRE, following the [FIBRE installation
guide](doc/fibre.md).

## Antenna Pointing

Aligning a satellite antenna is a precise procedure. Remember that the
satellites are over 35,000 km (22,000 mi) away. A tenth of a degree of error
will miss the satellite by more than 3500 km. Hence, this is likely the most
time-consuming step of the process.

Please refer to comprehensive instructions in our [antenna alignment
guide](doc/antenna-pointing.md).

## User Guide

- [Frequency Bands](doc/frequency.md)
- [Hardware Guide](doc/hardware.md)
- Receiver Configuration:
    - [Novra S400](doc/s400.md)
    - [TBS5927](doc/tbs.md)
    - [SDR Setup](doc/sdr.md)
- [Antenna Pointing](doc/antenna-pointing.md)
- [Bitcoin FIBRE](doc/fibre.md)
- [Satellite API](api/README.md)

## Support

For additional help, you can join the **#blockstream-satellite** IRC channel on
freenode.

