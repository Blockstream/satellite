---
nav_order: 7
---

# Dual-Satellite Connection

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Required Hardware](#required-hardware)
- [Host Configuration](#host-configuration)
  - [Novra S400 Standalone Receiver](#novra-s400-standalone-receiver)
  - [TBS USB Receiver](#tbs-usb-receiver)
  - [Blockstream Base Station Sat-IP Receiver](#blockstream-base-station-sat-ip-receiver)
  - [SDR Receiver](#sdr-receiver)

<!-- markdown-toc end -->


Some regions worldwide are covered by two satellites at the same time. Currently, there is extensive overlapping coverage in Asia from Telstar 18V C and Telstar 18V Ku. If you are in a region with overlapping coverage, you can connect to two satellites simultaneously and double the Bitcoin block transfer speed. This page describes the hardware and host configurations required to run such a dual-satellite setup.

Before continuing, however, you should check if your location has overlapping coverage from two satellites using our [Coverage Map](https://blockstream.com/satellite/#satellite_network-coverage). Also, note distinct signal strengths are expected from each satellite, given that the distance and viewing angles from your station to each satellite are different. Hence, we also recommend checking the [Link Analyzer](https://satellite.blockstream.space/link-analyzer/) tool for more specific antenna recommendations for each satellite.

## Required Hardware

A straightforward way to connect to two satellites simultaneously is to use separate antennas pointed to each satellite. To do so, you need two [LNBs](hardware.md#lnb) (one per dish), double the number of cables, twice as many connectors, etc. Nevertheless, it is also possible to receive two satellite beams simultaneously while using a single parabolic reflector. However, this approach requires more advanced parts and installation skills.

> If your location has overlapping coverage from the Telstar 18V C band and Ku band beams, note these are two different beams out of the same satellite. In principle, you could use a single dual-band (C and Ku) combo LNB if you were able to find one. However, such combo LNB models usually select one band or the other (C or Ku) instead of outputting both bands simultaneously. Hence, they are not sufficient for a dual-satellite setup. Thus, we recommend installing two independent antennas with independent LNBs instead. The [Pro Kit](https://store.blockstream.com/products/blockstream-satellite-pro-kit/) already comes with C and Ku band LNBs (see the [parts list](hardware.md#blockstream-satellite-pro-kit)), so you only need to purchase two dishes (and a few cables) in addition to the kit.

You also need two receivers for a dual-satellite setup, each connected to an LNB. The only exception is if your receiver is the Novra S400 of the [Pro Ethernet Kit](https://store.blockstream.com/products/blockstream-satellite-pro-kit/). This model supports dual satellite connectivity by offering two independent radio-frequency (RF) channels. Otherwise, if using a Sat-IP, USB, or SDR-based receiver (or combinations of them), you need two receiver units, each connected to a different antenna/LNB. If using the [Satellite Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/) (an integrated receiver-antenna), you also need two units, each pointing to a distinct satellite.

## Host Configuration

Once you have the required hardware parts, the next step is to configure the receivers using the host computer. Regardless of the adopted hardware, you need to create different configurations on the command-line interface (CLI). Recall that your first step with the CLI is to run the configuration helper, as follows:

```
blocksat-cli cfg
```

To create a second receiver configuration, you need to use option `--cfg name`. For example, you can set up a second configuration named `rx2`, as follows:

```
blocksat-cli --cfg rx2 cfg
```

Then, select the other satellite of interest and inform the parts composing your second receiver setup. Subsequently, you can run all CLI commands using option `--cfg rx2`. Specific instructions are provided next.

### Novra S400 Standalone Receiver

With the Novra S400, you need to configure the two RF interfaces separately. Each interface will be connected to a different antenna and receiving from a different satellite. As explained on the [S400 guide](s400.md#receiver-and-host-configuration), the first RF interface (RF1) is configured by the following command:

```
blocksat-cli standalone cfg
```

To configure the second RF interface, run:

```
blocksat-cli --cfg rx2 standalone --demod 2 cfg --rx-only
```

Next, access the S400 web management console as instructed in the [S400 guide](s400.md#s400-configuration-via-the-web-ui). Go to `Interfaces > RF2` and enable the RF2 interface.

Lastly, you need to configure [Bitcoin Satellite](bitcoin.md) to receive the second satellite stream. You can do so by running:

```
blocksat-cli --cfg rx2 btc --concat
```

### TBS USB Receiver


With a TBS 5927 or 5520SE USB receiver, you would ordinarily run the following sequence of commands:

1. Initial configurations:
```
blocksat-cli cfg
```

2. Installation of dependencies:
```
blocksat-cli deps install
```

3. Configuration of the host interfaces:
```
blocksat-cli usb config
```

4. Receiver launch:
```
blocksat-cli usb launch
```

To use a second TBS unit as the second receiver of a dual-satellite setup, you only need to repeat steps 3 and 4 while including argument `--cfg rx2`, as follows:

```
blocksat-cli --cfg rx2 usb config

blocksat-cli --cfg rx2 usb launch
```

Make sure to select the second TBS 5927/5520SE unit on both steps.

Lastly, you need to configure [Bitcoin Satellite](bitcoin.md) to receive from the second TBS device. You can do so by running:

```
blocksat-cli --cfg rx2 btc --concat
```

### Blockstream Base Station Sat-IP Receiver

With the [Satellite Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/) Sat-IP receiver, you need two base station devices for a dual-satellite setup. Also, when launching the Sat-IP client, you need to select the correct receiver by IP address.


Run the first Sat-IP client and select the correct receiver when prompted:
```
blocksat-cli sat-ip
```

Next, launch the second Sat-IP client and, again, select the appropriate receiver:
```
blocksat-cli --cfg rx2 sat-ip
```

### SDR Receiver

To set up an SDR-based receiver, you would ordinarily run the following sequence of commands:

1. Initial configurations:
```
blocksat-cli cfg
```

2. Installation of dependencies:
```
blocksat-cli deps install
```

3. Receiver launch:
```
blocksat-cli sdr
```

To run a second SDR-based receiver, you only need to repeat step 3 while switching to the second configuration, as follows:

```
blocksat-cli --cfg rx2 sdr
```

> NOTE: if you are running two SDR-based receivers on the same host, with two RTL-SDR dongles, you can select the RTL-SDR dongle using option `--rtl-idx`. For example, for the second RTL-SDR, run:
>
> ```
> blocksat-cli --cfg rx2 sdr --rtl-idx 1
> ```

Lastly, you need to configure [Bitcoin Satellite](bitcoin.md) to receive the second satellite stream. You can do so by running:

```
blocksat-cli --cfg rx2 btc --concat
```

