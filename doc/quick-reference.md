# Quick Reference

This page contains a quick reference guide for the Blockstream Satellite
receiver setup and its general usage. Please refer to the [main
guide](README.md) for detailed explanations on all steps.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->

- [1. CLI Installation and Upgrade](#1-cli-installation-and-upgrade)
- [2. Common Steps](#2-common-steps)
- [3. Receiver-specific Configuration Steps](#3-receiver-specific-configuration-steps)
    - [Novra S400 standalone receiver](#novra-s400-standalone-receiver)
    - [TBS5927 USB receiver](#tbs5927-usb-receiver)
    - [SDR-based receiver](#sdr-based-receiver)
- [4. Receiver-specific Antenna Alignment Steps](#4-receiver-specific-antenna-alignment-steps)
    - [Novra S400 standalone receiver](#novra-s400-standalone-receiver)
    - [TBS5927 USB receiver](#tbs5927-usb-receiver)
    - [SDR-based receiver](#sdr-based-receiver)
- [5. Bitcoin-satellite Setup](#5-bitcoin-satellite-setup)
- [6. Satellite API](#6-satellite-api)

<!-- markdown-toc end -->

## 1. CLI Installation and Upgrade

Install the command-line interface (CLI):

```
sudo pip3 install blocksat-cli
```

Alternatively, to upgrade a previous installation of the CLI, run:

```
sudo pip3 install blocksat-cli --upgrade
```

To check your current version, run:

```
blocksat-cli -v
```

## 2. Common Steps

These are the commands that are applicable to all the supported types of
receivers.

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

## 3. Receiver-specific Configuration Steps

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

## 4. Receiver-specific Antenna Alignment Steps

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

## 5. Bitcoin-satellite Setup

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

## 6. Satellite API

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

Listen for API messages coming from the demo receiver:
```
blocksat-cli api listen -d
```
