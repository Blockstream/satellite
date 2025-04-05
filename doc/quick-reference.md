---
nav_order: 12
---

# Quick Reference Guide

This page contains a quick reference guide for the Blockstream Satellite receiver setup and its general usage via the command-line interface (CLI). Please refer to the [main guide](../index.md) for detailed explanations on all steps and instructions for the graphical user interface (GUI).

<!-- markdown-toc start -->
- [Installation and Upgrade](#installation-and-upgrade)
- [Installation and Upgrade as a Python Package](#installation-and-upgrade-as-a-python-package)
- [Common Steps](#common-steps)
- [Receiver-specific Configuration Steps](#receiver-specific-configuration-steps)
  - [Novra S400 standalone receiver](#novra-s400-standalone-receiver)
  - [TBS USB receiver](#tbs-usb-receiver)
  - [Sat-IP receiver](#sat-ip-receiver)
  - [SDR receiver](#sdr-receiver)
- [Receiver-specific Antenna Alignment Steps](#receiver-specific-antenna-alignment-steps)
  - [Novra S400 standalone receiver](#novra-s400-standalone-receiver-1)
  - [TBS USB receiver](#tbs-usb-receiver-1)
  - [Sat-IP receiver](#sat-ip-receiver-1)
  - [SDR receiver](#sdr-receiver-1)
- [Bitcoin-satellite Setup](#bitcoin-satellite-setup)
- [Satellite API](#satellite-api)

<!-- markdown-toc end -->

## Installation and Upgrade

**Ubuntu:**

```bash
add-apt-repository ppa:blockstream/satellite
apt update && apt install blockstream-satellite
```

**Fedora:**

```bash
dnf copr enable blockstream/satellite
dnf install blockstream-satellite
```

**Debian:**

```bash
add-apt-repository https://aptly.blockstream.com/satellite/debian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt update && apt install blockstream-satellite
```

**Raspberry Pi OS (formerly Raspbian):**

```bash
add-apt-repository https://aptly.blockstream.com/satellite/raspbian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt update && apt install blockstream-satellite
```

## Installation and Upgrade as a Python Package

**Note:** Consider this method only if not using the above instructions for installing and upgrading directly with the Linux package manager.

Install the command-line interface (CLI) and the graphical user interface (GUI) packages:

```
sudo pip3 install blocksat-cli blocksat-gui
```

Alternatively, upgrade the existing installation:

```
sudo pip3 install blocksat-cli --upgrade
sudo pip3 install blocksat-gui --upgrade
```

To check your current version, run:

```
blocksat-cli -v
blocksat-gui -v
```

## Common Steps

These are the commands that are applicable to all the supported types of receivers.

Set initial configurations:

```
blocksat-cli cfg
```

Install software dependencies:

```
blocksat-cli deps install
```

> To update the dependencies, run:
>
> ```
> blocksat-cli deps update
> ```

Get instructions:

```
blocksat-cli instructions
```

## Receiver-specific Configuration Steps

### Novra S400 standalone receiver

Configure the receiver and the host by running:

```
blocksat-cli standalone cfg
```

Monitor the S400 receiver:
```
blocksat-cli standalone monitor
```

### TBS USB receiver

Install the drivers:
```
blocksat-cli deps tbs-drivers
```

Configure the host and the TBS 5927/5520SE:
```
blocksat-cli usb config
```

Start the USB receiver:
```
blocksat-cli usb launch
```

### Sat-IP receiver

Launch the Sat-IP client:
```
blocksat-cli sat-ip
```

### SDR receiver

Configure Gqrx:
```
blocksat-cli gqrx-conf
```

Run the SDR receiver:
```
blocksat-cli sdr
```

## Receiver-specific Antenna Alignment Steps

This is the most time-consuming part of the process and has detailed guidance on the [antenna alignment guide](antenna-pointing.md#find-the-satellite-and-lock-the-signal).

In summary, you will try to point your antenna until you get a signal lock on your receiver.

### Novra S400 standalone receiver

Monitor the S400 receiver by running:
```
blocksat-cli standalone monitor
```

While pointing the antenna, check the logs on the terminal until the receiver logs a `Lock`. Alternatively, check the lock indicator on the S400's web UI or front panel until it becomes green (locked).

### TBS USB receiver

Make sure that the USB receiver is running with:
```
blocksat-cli usb launch
```

While pointing the antenna, check the logs on the terminal until the receiver logs a `Lock`.

### Sat-IP receiver

Launch the Sat-IP client:
```
blocksat-cli sat-ip
```

While pointing the antenna, check the logs on the terminal until the receiver logs a `Lock`.

### SDR receiver

Run gqrx:
```
gqrx
```

Point the antenna until you can visualize the Blockstream Satellite signal spanning 1.2 MHz. Take note of the offset between the observed signal's center frequency and the nominal center frequency (at the center of the gqrx plot).

Run the receiver with the GUI enabled and in debug mode:

```
blocksat-cli sdr --gui -d --derotate freq_offset
```

where `freq_offset` is the offset (in units of kHz) you observed on the `gqrx` step.

On the plots that open up, confirm the presence of the signal. Then, wait until the receiver prints `LOCKED` on the terminal.

## Bitcoin-satellite Setup

Install bitcoin-satellite:
```
blocksat-cli deps install --btc
```

> To update a previous installation of bitcoin-satellite, run:
>
> ```
> blocksat-cli deps update --btc
> ```

Generate the `bitcoin.conf` configuration file:
```
blocksat-cli btc
```

Run bitcoin-satellite:
```
bitcoind
```

## Satellite API

Configure encryption keys:
```
blocksat-cli api cfg
```

Broadcast a message using the satellite API:
```
blocksat-cli api send
```

Bump the bid of an API transmission order:
```
blocksat-cli api bump
```

Delete an API transmission order:
```
blocksat-cli api del
```

Listen for API messages acquired by the satellite receiver:
```
blocksat-cli api listen
```

Run the [demo receiver](api.md#demo-receiver):
```
blocksat-cli api demo-rx
```

Listen to the API messages coming from the demo receiver:
```
blocksat-cli api listen -d
```
