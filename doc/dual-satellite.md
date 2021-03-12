# Dual-Satellite Connection

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Dual-Satellite Connection](#dual-satellite-connection)
    - [Novra S400 Standalone Receiver](#novra-s400-standalone-receiver)
    - [TBS5927 USB Receiver](#tbs5927-usb-receiver)
    - [SDR-based Receiver](#sdr-based-receiver)

<!-- markdown-toc end -->


Some regions worldwide are covered by two satellites at the same time. For
example, most of the US has coverage from both the Galaxy 18 and
Eutelsat 113. In Asia, there is extensive overlapping coverage from Telstar 18V
C and Telstar 18V Ku. If you are in such a region with overlapping coverage, you
can simultaneously connect to two satellites and double the bitcoin block
transfer speed.

You can check if your location has overlapping coverage from two satellites in
our [Coverage
Map](https://blockstream.com/satellite/#satellite_network-coverage).

To connect to two satellites simultaneously, you need separate antennas pointed
to each satellite. Correspondingly, you need two LNBs (one per dish), double the
number of cables, connectors, etc. The only exception is the receiver device, in
case you have one that supports dual satellite connectivity.

If you have the Novra S400 receiver of the [Pro Ethernet
Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/), you
can use a single unit simultaneously connected to two antennas/LNBs. Otherwise,
with a USB or SDR-based receiver (or combinations of them), you need two
receivers, each connected to a different antenna.

To run multiple receivers, you need to set up different sets of configurations
on the command-line interface (CLI). Recall that your first step with the CLI,
regardless of the type of receiver, is to run the configuration helper, as
follows:

```
blocksat-cli cfg
```

To configure a second receiver, you need to set option `--cfg name`. For
example, you can set up a second configuration named `rx2`, as follows:

```
blocksat-cli --cfg rx2 cfg
```

On this second configuration, you select the other satellite and provide the
information regarding the parts of your second receiver setup. Subsequently, you
can run all CLI commands using option `--cfg rx2`. Specific instructions are
provided next.

## Novra S400 Standalone Receiver

With the Novra S400, you need to configure the two RF interfaces
separately. Each interface will be connected to a different antenna and
receiving from a different satellite. As explained on the [S400
guide](s400.md#receiver-and-host-configuration), the first RF interface (RF1) is
configured by the following command:

```
sudo blocksat-cli standalone cfg
```

To configure the second RF interface, run:

```
sudo blocksat-cli --cfg rx2 standalone --demod 2 cfg --rx-only
```

Next, access the S400 web management console [as instructed in the S400
guide](s400.md#s400-configuration-via-the-web-ui). Go to `Interfaces > RF2` and
enable the RF2 interface.

Lastly, you need to configure [Bitcoin Satellite](bitcoin.md) to receive the
second satellite stream. You can do so by running:

```
blocksat-cli --cfg rx2 btc --concat
```

## TBS5927 USB Receiver


With a TBS5927 USB receiver, you would ordinarily run the following sequence
of commands:

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
sudo blocksat-cli usb config
```

4. Receiver launch:
```
blocksat-cli usb launch
```

To use a second TBS5927 unit as the second receiver of a dual-satellite setup,
you only need to repeat steps 3 and 4 while including argument `--cfg rx2`, as
follows:

```
sudo blocksat-cli --cfg rx2 usb config

blocksat-cli --cfg rx2 usb launch
```

Make sure to select the second TBS5927 unit on both steps.

Lastly, you need to configure [Bitcoin Satellite](bitcoin.md) to receive from
the second TBS5927 device. You can do so by running:

```
blocksat-cli --cfg rx2 btc --concat
```

## SDR-based Receiver

To set up an SDR-based receiver, you would ordinarily run the following sequence
of commands:

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

To run a second SDR-based receiver, you only need to repeat step 3 while
switching to the second configuration, as follows:

```
blocksat-cli --cfg rx2 sdr
```

> NOTE: if you are running two SDR-based receivers on the same host, with two
> RTL-SDR dongles, you can select the RTL-SDR dongle using option
> `--rtl-idx`. For example, for the second RTL-SDR, run:
>
> ```
> blocksat-cli --cfg rx2 sdr --rtl-idx 1
> ```

Lastly, you need to configure [Bitcoin Satellite](bitcoin.md) to receive the
second satellite stream. You can do so by running:

```
blocksat-cli --cfg rx2 btc --concat
```

