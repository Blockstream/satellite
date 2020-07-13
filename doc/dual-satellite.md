# Dual-Satellite Connection

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Dual-Satellite Connection](#dual-satellite-connection)
    - [Novra S400 standalone receiver](#novra-s400-standalone-receiver)
    - [TBS5927 USB receiver](#tbs5927-usb-receiver)
    - [SDR-based receiver](#sdr-based-receiver)

<!-- markdown-toc end -->


Some regions worldwide are covered by two satellites at the same time. For
example, most of the US has coverage from both the Galaxy 18 and Eutelsat 113
satellites. In Asia, there is extensive overlapping coverage from Telstar 18V C
and Telstar 18V Ku.

You can check if your location has overlapping coverage from two satellites by
checking our [Coverage
Map](https://blockstream.com/satellite/#satellite_network-coverage).

If you are in such a region with overlapping coverage, you can simultaneously
connect to the two satellites and double the bitcoin block transfer speed. To do
so, you need separate antennas pointed to each satellite. Correspondingly, you
need two LNBs (one per dish), double the number of cables, connectors, etc. The
only exception refers to the receiver device, in case you have one that supports
dual satellite connectivity.

If you have the Novra S400 receiver of the [Pro Ethernet
Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/), you
can use a single unit simultaneously connected to two antennas/LNBs. Otherwise,
with a USB or SDR-based receiver (or combinations of them), you need two
receivers, each connected to a different antenna.

To run multiple receivers, you need to set up different sets of configurations
on the command-line interface (CLI). Recall that your first step with the CLI
regardless of the type of receiver is to run the configuration helper, as
follows:

```
blocksat-cli cfg
```

To configure a second receiver, you need to set option `--cfg name`, where
argument `name` should be the name of the second configuration. For example, you
can set up a configuration named `rx2`, as follows:

```
blocksat-cli --cfg rx2 cfg
```

On this second configuration, you select the other satellite and provide the
information regarding the parts of your second receiver setup. Subsequently, you
can run all commands in the CLI using option `--cfg rx2`. Specific instructions
are provided next.

## Novra S400 standalone receiver

On the Novra S400, you need to configure the two RF interfaces on the same
unit. Each interface will be connected to a different antenna and receiving from
a different satellite. As explained on the [S400 guide](s400.md), all
configurations are provided by the command:

```
blocksat-cli instructions
```

Use these instructions to configure interface RF1. Then, get the instructions
for the other interface by running:

```
blocksat-cli --cfg rx2 instructions
```

Use these instructions to configure interface RF2.

## TBS5927 USB receiver


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

## SDR-based receiver

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
> `--rtl-idx`. For example, on the second RTL-SDR, run:
>
> ```
> blocksat-cli --cfg rx2 sdr --rtl-idx 1
> ```

