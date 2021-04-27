# Quick Reference Guide

This page contains a quick reference guide for the Blockstream Satellite
receiver setup and its general usage. Please refer to the [main
guide](README.md) for detailed explanations on all steps.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->

- [CLI Installation and Upgrade](#cli-installation-and-upgrade)
- [Common Steps](#common-steps)
- [Receiver-specific Configuration Steps](#receiver-specific-configuration-steps)
    - [Novra S400 standalone receiver](#novra-s400-standalone-receiver)
    - [TBS5927 USB receiver](#tbs5927-usb-receiver)
    - [Sat-IP receiver](#sat-ip-receiver)
    - [SDR receiver](#sdr-receiver)
- [Receiver-specific Antenna Alignment Steps](#receiver-specific-antenna-alignment-steps)
    - [Novra S400 standalone receiver](#novra-s400-standalone-receiver-1)
    - [TBS5927 USB receiver](#tbs5927-usb-receiver-1)
    - [Sat-IP receiver](#sat-ip-receiver-1)
    - [SDR receiver](#sdr-receiver-1)
- [Bitcoin-satellite Setup](#bitcoin-satellite-setup)
- [Satellite API](#satellite-api)

<!-- markdown-toc end -->


## CLI Installation and Upgrade

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

## Common Steps

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

## Receiver-specific Configuration Steps

### Novra S400 standalone receiver

Configure the receiver and the host by running:

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

This is the most time-consuming part of the process and has detailed guidance on
the [antenna alignment
guide](antenna-pointing.md#find-the-satellite-and-lock-the-signal).

In summary, you will try to point your antenna until you get a signal lock on
your receiver.

### Novra S400 standalone receiver

Monitor the S400 receiver by running:
```
blocksat-cli standalone monitor
```

While pointing the antenna, check the logs on the terminal until the receiver
logs a `Lock`. Alternatively, check the lock indicator on the S400's web UI or
front panel until it becomes green (locked).

### TBS5927 USB receiver

Make sure that the USB receiver is running with:
```
blocksat-cli usb launch
```

While pointing the antenna, check the logs on the terminal until the receiver
logs a `Lock`.

### Sat-IP receiver

Launch the Sat-IP client:
```
blocksat-cli sat-ip
```

While pointing the antenna, check the logs on the terminal until the receiver
logs a `Lock`.

### SDR receiver

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
