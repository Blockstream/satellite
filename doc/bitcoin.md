---
nav_order: 6
---

# Bitcoin Satellite

<!-- markdown-toc start -->
**Table of Contents**

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [Further Information](#further-information)
  - [UDP Multicast Reception Option](#udp-multicast-reception-option)
  - [Installation from Binary Packages](#installation-from-binary-packages)
  - [Compilation from Source](#compilation-from-source)

<!-- markdown-toc end -->

## Overview

[Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite) is a fork of [FIBRE (Fast Internet Bitcoin Relay Engine)](https://bitcoinfibre.org) and, consequently, also a fork of [Bitcoin Core](https://bitcoincore.org). It features a version of the bitcoind application with support for the reception of blocks sent over satellite in UDP datagrams with multicast addressing. You can find in-depth information about Bitcoin Satellite on the project's [Wiki page](https://github.com/Blockstream/bitcoinsatellite/wiki).

## Installation

If using the GUI, go to the Receiver tab and select the Settings sub-tab. Then, open the Bitcoin dropdown menu and select "Install Bitcoin Satellite," as shown below:

![GUI Bitcoin Satellite Installation](img/gui_btc_sat_install.png?raw=true)

If using the CLI, install bitcoin-satellite by running:

```
blocksat-cli deps install --btc
```

> NOTE:
>
> - This step works with the two most recent releases of Ubuntu LTS, Fedora, Debian, and Raspbian.
>
> - bitcoin-satellite is a fork of bitcoin core. As such, it installs applications with the same name (i.e., `bitcoind`, `bitcoin-cli`, `bitcoin-qt`, and `bitcoin-tx`). Hence, the installation of `bitcoin-satellite` will fail if you already have bitcoin core installed.

Alternatively, you can install bitcoin-satellite manually [from binary packages](#installation-from-binary-packages) or [from source](#compilation-from-source).

## Configuration

Next, you need to generate a `bitcoin.conf` file with configurations to receive Bitcoin data over satellite. If using the GUI, select "Create configuration file" on the Bitcoin dropdown menu shown above.

With the CLI, run the following command:

```
blocksat-cli btc
```

By default, the generated `bitcoin.conf` file is placed at `~/.bitcoin/`, the default Bitcoin [data directory](https://en.bitcoin.it/wiki/Data_directory) used by Bitcoin Satellite. However, you can specify an alternative `datadir` as follows:

```
blocksat-cli btc -d datadir
```

## Running

Next, run `bitcoind` as usual, like so:

```
bitcoind
```

Note that other Bitcoin Core options are supported and can be added to the generated `bitcoin.conf` file or as arguments to the above command. For example, you can run the node based on satellite links only (unplugged from the internet) using option `connect=0` on `bitcoin.conf` or by running:

```
bitcoind -connect=0
```

Also, you can run `bitcoind` in daemon mode:

```
bitcoind -daemon
```

Once `bitcoind` is running, you can check the satellite interface is receiving data by running the following command:

```
bitcoin-cli getudpmulticastinfo
```

If the receiver is correctly locked to the satellite signal, you should see a bitrate around 1.09 Mbps.

Furthermore, you can check the number of blocks being received concurrently over satellite with the following command:

```
bitcoin-cli getchunkstats
```

## Further Information

### UDP Multicast Reception Option

The GUI and the CLI command described previously generate the `bitcoin.conf` required to process the multicast-addressed UDP/IPv4 stream received over satellite. The main option defined on the generated configuration file is the `udpmulticast` option, explained next.

There are several ways to configure option `udpmulticast`, depending on your hardware setup, such as your [receiver](hardware.md#supported-receiver-options) and the satellite from which you are receiving the signal. The option should be set as follows:

```
 -udpmulticast=<if>,<dst_ip>:<port>,<src_ip>,<trusted>[,<label>]
```

With this command, the application listens to multicast-addressed UDP messages sent by IP address `<src_ip>` towards IP address `<dst_ip>:<port>` using interface `<if>`. When option `<trusted>` is set to 1, the application assumes the sender is a trusted node. Lastly, option `<label>` assigns a label to the multicast stream in order to facilitate the inspection of logs.

Consider the following example:

```
udpmulticast=dvb0_0,239.0.0.2:4434,172.16.235.9,1,blocksat
```

In this case, it follows that:

- `dvb0_0` is the network interface receiving multicast-addressed UDP messages out of the receiver.
- `239.0.0.2:4434` is the destination IP address and port of the packets sent over satellite.
- `172.16.235.9` is the IP address of the Blockstream ground station node broadcasting data over the satellite network (each satellite has a unique source IP address).
- `1` configures this stream as coming from a *trusted* source, which is helpful to speed up block reception.
- `blocksat` is a label used to facilitate the inspection of logs.

Please note that the `bitcoin.conf` file generated by the GUI or CLI already has the `udpmulticast` option with the appropriate parameters for your chosen hardware and satellite, so no further action is needed.

### Installation from Binary Packages

We recommend using the GUI or CLI to install the Bitcoin Satellite application, as instructed [previously](#installation). However, you can also install `bitcoin-satellite` manually from the binary packages available for the two most recent Ubuntu LTS, Fedora, Debian, and Raspbian releases. The manual installation instructions are as follows:

Ubuntu:

```
add-apt-repository ppa:blockstream/satellite
apt-get update
apt-get install bitcoin-satellite
```

> If command `add-apt-repository` is not available, install `software-properties-common`.

Debian:

```
add-apt-repository https://aptly.blockstream.com/satellite/debian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt-get update
apt-get install bitcoin-satellite
```

> Install `gnupg`, `apt-transport-https`, and `software-properties-common`, if necessary.

Raspbian:

```
add-apt-repository https://aptly.blockstream.com/satellite/raspbian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt-get update
apt-get install bitcoin-satellite
```

> Install `gnupg`, `apt-transport-https`, and `software-properties-common`, if necessary.

Fedora:

```
dnf copr enable blockstream/satellite
dnf install bitcoin-satellite
```

> If command `dnf copr enable` is not available, install `dnf-plugins-core`.

CentOS:

```
yum copr enable blockstream/satellite
yum install bitcoin-satellite
```

> If command `yum copr enable` is not available, install `yum-plugin-copr`.

### Compilation from Source

To build Bitcoin Satellite from source, first, clone the repository:

```
git clone https://github.com/Blockstream/bitcoinsatellite.git
cd bitcoinsatellite/
```

Then, install all build requirements listed [in the project's documentation](https://github.com/Blockstream/bitcoinsatellite/blob/master/doc/build-unix.md#dependency-build-instructions-ubuntu--debian).

Next, run:

```
./autogen.sh
./configure
make
```

This will build the `bitcoind` application binary within the `src`/` directory, and you can execute it from there. Alternatively, you can install the application in your system:

```
make install
```

Detailed build instructions can be found within [the project's documentation](https://github.com/Blockstream/bitcoinsatellite/tree/master/doc#building).

---

Prev: [Novra S400 Setup](s400.md) | [TBS Setup](tbs.md) | [SDR Setup](sdr.md) | [Sat-IP Setup](sat-ip.md)
