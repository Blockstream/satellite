# Bitcoin Satellite

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Bitcoin Satellite](#bitcoin-satellite)
    - [Overview](#overview)
    - [Installation](#installation)
    - [Configuration](#configuration)
    - [Running](#running)
    - [Further Information](#further-information)
        - [UDP Multicast Reception Option](#udp-multicast-reception-option)
        - [Installation from Binary Packages](#installation-from-binary-packages)
        - [Installation from Source](#installation-from-source)

<!-- markdown-toc end -->

## Overview

[Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite) is a fork
of [FIBRE (Fast Internet Bitcoin Relay Engine)](https://bitcoinfibre.org) and,
consequently, also a fork of [Bitcoin Core](https://bitcoincore.org). It
features a version of the bitcoind application with support for the reception of
blocks sent over satellite in UDP datagrams with multicast addressing. You can
find detailed information regarding how Bitcoin Satellite works on the project's
[Wiki page](https://github.com/Blockstream/bitcoinsatellite/wiki).

## Installation

Install bitcoin-satellite by running:

```
blocksat-cli deps install --btc
```

> NOTE:
>
> - This command supports Ubuntu (18.04, 19.10, and 20.04), Fedora (30,
> 31, and 32), and CentOS 7.
>
> - bitcoin-satellite is a fork of bitcoin core. As such, it installs
> applications with the same name (i.e., `bitcoind`, `bitcoin-cli`,
> `bitcoin-qt`, and `bitcoin-tx`). Hence, the installation of
> `bitcoin-satellite` will fail if you already have bitcoin core installed.

Alternatively, you can install bitcoin-satellite manually [from binary
packages](#installation-from-binary-packages) or [from
source](#installation-from-source).

## Configuration

Next, you need to generate a `bitcoin.conf` file with configurations to receive
bitcoin data via satellite. To do so, run:

```
blocksat-cli btc
```

By default, this command will place the generated `bitcoin.conf` file at
`~/.bitcoin/`, which is the default Bitcoin [data
directory](https://en.bitcoin.it/wiki/Data_directory) used by Bitcoin
Satellite. If you so desire, you can specify an alternative `datadir` as
follows:
```
blocksat-cli btc -d datadir
```

## Running

Next, run `bitcoind` as usual, like so:

```
bitcoind
```

Note that other [Bitcoin Core
options](https://wiki.bitcoin.com/w/Running_Bitcoin) are supported and can be
added to the generated `bitcoin.conf` file as needed, or directly as arguments
to the above command. For example, you can run the node based on satellite links
only (unplugged from the internet) using option `connect=0` on `bitcoin.conf` or
by running:

```
bitcoind -connect=0
```

Also, you can run `bitcoind` in daemon mode:

```
bitcoind -daemon
```

Once `bitcoind` is running, you can check the satellite interface is receiving
data by running the following command:

```
bitcoin-cli getudpmulticastinfo
```

If the receiver is correctly locked to the satellite signal, you should see a
bitrate around 1.09 Mbps.

Furthermore, you can check the number of blocks being received concurrently over
satellite with the following command:

```
bitcoin-cli getchunkstats
```

## Further Information

### UDP Multicast Reception Option

In a Blockstream Satellite receiver setup, the satellite receiver will decode
and output a UDP/IPv4 stream. Bitcoin Satellite, in turn, listens to such a
stream when configured with option `udpmulticast` (added to the `bitcoin.conf`
file).

There are several possibilities regarding the configuration of option
`udpmulticast`. It depends on your hardware setup (for instance, your [receiver
type](hardware.md#receiver-options)) and the satellite that you are receiving
from. The option is described as follows:

```
 -udpmulticast=<if>,<dst_ip>:<port>,<src_ip>,<trusted>[,<label>]
       Listen to multicast-addressed UDP messages sent by <src_ip> towards
       <dst_ip>:<port> using interface <if>. Set <trusted> to 1 if
       sender is a trusted node. An optional <label> may be defined for
       the multicast group in order to facilitate inspection of logs.
```

Here is an example:

```
udpmulticast=dvb0_0,239.0.0.2:4434,172.16.235.9,1,blocksat
```

In this case, we have that:

- `dvb0_0` is the name of the network interface that receives data out of the
  receiver.
- `239.0.0.2:4434` is the destination IP address and port of the packets that
  are sent over satellite.
- `172.16.235.9` is the IP address of the Blockstream ground station node
  broadcasting data over the satellite network (each satellite has a unique
  source IP address).
- `1` configures this stream as coming from a *trusted* source, which is helpful
  to speed-up block reception.
- `blocksat` is a label used simply to facilitate inspection of logs.

To simplify the process, command `blocksat-cli btc` generates the `bitcoin.conf`
file for you.


### Installation from Binary Packages

You can install `bitcoin-satellite` directly from binary packages that are
available for the following distribution/releases:

- Ubuntu Bionic (18.04), Eoan (19.10), and Focal (20.04)
- Fedora 30, 31, and 32
- CentOS 7 and 8

Ubuntu:

```
add-apt-repository ppa:blockstream/satellite
apt-get update
apt-get install bitcoin-satellite
```

> If command `add-apt-repository` is not available, install
> `software-properties-common`.

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

### Installation from Source

To build Bitcoin Satellite from source, first clone the repository:

```
git clone https://github.com/Blockstream/bitcoinsatellite.git
cd bitcoinsatellite/
```

Then, install all build requirements listed [in the project's
documentation](https://github.com/Blockstream/bitcoinsatellite/blob/master/doc/build-unix.md#dependency-build-instructions-ubuntu--debian).

Next, run:

```
./autogen.sh
./configure
make
```

This will build the `bitcoind` application binary within the `src/` directory
and you can execute it from there. Alternatively, you can install the
application in your system:

```
make install
```

Detailed build instructions can be found within [the project's documentation
](https://github.com/Blockstream/bitcoinsatellite/tree/master/doc#building).

---

Prev: [Novra S400 Setup](s400.md) | [TBS5927 Setup](tbs.md) | [SDR Setup](sdr.md)
