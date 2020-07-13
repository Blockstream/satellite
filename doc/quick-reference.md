# Quick Reference

This page contains a quick reference guide for the Blockstream Satellite
receiver setup. In a nutshell, you need to go through the following:

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->

- [1. Common Steps](#1-common-steps)
- [2. Receiver-specific Configuration Steps](#2-receiver-specific-configuration-steps)
    - [Novra S400 standalone receiver](#novra-s400-standalone-receiver)
    - [TBS5927 USB receiver](#tbs5927-usb-receiver)
    - [SDR-based receiver](#sdr-based-receiver)
- [3. Receiver-specific Antenna Alignment Steps](#3-receiver-specific-antenna-alignment-steps)
    - [Novra S400 standalone receiver](#novra-s400-standalone-receiver)
    - [TBS5927 USB receiver](#tbs5927-usb-receiver)
    - [SDR-based receiver](#sdr-based-receiver)
- [4. Bitcoin-satellite Setup](#4-bitcoin-satellite-setup)

<!-- markdown-toc end -->

Please refer to the [main guide](README.md) for detailed explanations on all
steps.

## 1. Common Steps

These are the commands that are applicable to all the supported types of
receivers.

Install the command-line interface (CLI):

```
sudo pip3 install blocksat-cli
```

Alternatively, to upgrade a previous installation of the CLI, run:

```
sudo pip3 install blocksat-cli --upgrade
```

Set initial configurations:

```
blocksat-cli cfg
```

Install software dependencies:

```
blocksat-cli deps install
```

Get instructions:

```
blocksat-cli instructions
```

## 2. Receiver-specific Configuration Steps

### Novra S400 standalone receiver

Set all configurations on the S400 by following the instructions from:
```
blocksat-cli instructions
```

Configure the host to communicate with the S400:
```
sudo blocksat-cli standalone cfg
```

### TBS5927 USB receiver

Install the drivers:
```
blocksat-cli deps tbs-drivers
```

Configure the host's interfacing with the TBS5927:
```
sudo blocksat-cli usb config
```

Start the USB receiver:
```
blocksat-cli usb launch
```

### SDR-based receiver

Configure Gqrx:
```
blocksat-cli gqrx-conf
```

Run the SDR receiver:
```
blocksat-cli sdr
```

## 3. Receiver-specific Antenna Alignment Steps

This is the most time-consuming part of the process and has detailed guidance on
the [antenna alignment
guide](antenna-pointing.md#find-the-satellite-and-lock-the-signal).

In summary, you will try to point your antenna until you get a signal lock on
your receiver.

### Novra S400 standalone receiver

While pointing the antenna, check the lock indicator on the S400's web UI until
it becomes green (locked).

### TBS5927 USB receiver

Make sure that the USB receiver is running with:
```
blocksat-cli usb launch
```

While pointing the antenna, check the receiver logs on the terminal until the
receiver logs a `Lock`.

### SDR-based receiver

Run gqrx:
```
gqrx
```

Point the antenna until you can visualize the Blockstream Satellite signal
spanning 1.2 MHz. Take note of the offset between the observed signal's center
frequency and the nominal center frequency (at the center of the gqrx plot).

Run the receiver with the GUI enabled and in debug mode:

```
blocksat-cli sdr --gui -d --derotate freq_offset
```

where `freq_offset` is the offset (in units of kHz) you observed on the `gqrx`
step.

On the plots that open up, confirm the presence of the signal. Then, wait until
the receiver prints `LOCKED` on the terminal.

## 4. Bitcoin-satellite Setup

Install bitcoin-satellite:
```
blocksat-cli deps install --btc
```

Generate the `bitcoin.conf` configuration file:
```
blocksat-cli btc
```

Run bitcoin-satellite:
```
bitcoind
```
