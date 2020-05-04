# Bitcoin Satellite

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Bitcoin Satellite](#bitcoin-satellite)
    - [Overview](#overview)
    - [Build](#build)
    - [Usage](#usage)

<!-- markdown-toc end -->

## Overview

This project is a fork from [FIBRE (Fast Internet Bitcoin Relay
Engine)](https://bitcoinfibre.org) and, consequently, also a fork of [Bitcoin
Core](https://bitcoincore.org). It features a version of the bitcoind
application with support for reception of blocks sent over satellite in UDP
datagrams with multicast addressing.

## Build

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

## Usage

In a Blockstream Satellite receiver setup, the satellite demodulator will decode
and output a UDP/IPv4 stream, which in turn Bitcoin Satellite can listen to. In
order for Bitcoin Satellite to listen to such stream, option `udpmulticast` must
be added to bitcoin's configuration file (i.e. the `bitcoin.conf` file).

There are several possibilities regarding the configuration of option
`udpmulticast`. It depends on your hardware setup and, more specifically, your
[demodulator type](hardware.md#demodulator-options), as well on the satellite
that you are receiving from. The option is described as follows:

```
 -udpmulticast=<if>,<dst_ip>:<port>,<src_ip>,<trusted>[,<label>]
       Listen to multicast-addressed UDP messages sent by <src_ip> towards
       <dst_ip>:<port> using interface <if>. Set <trusted> to 1 if
       sender is a trusted node. An optional <label> may be defined for
       the multicast group in order to facilitate inspection of logs.
```

Here is an example:

```
udpmulticast=dvb0_0,239.0.0.2:4434,192.168.200.2,1,blocksat
```

In this case, we have that:

- `dvb0_0` is the name of the network interface that receives data out of the demodulator.
- `239.0.0.2:4434` is the destination IP address and port of the packets that are sent over satellite.
- `192.168.200.2` is the IP address of one of our Tx nodes that broadcasts data over the Blockstream Satellite network. 
- `1` configures this stream as coming from a *trusted* source, which is helpful to speed up block reception.
- `blocksat` is a label used simply to facilitate inspection of logs.

Note that you will need to configure a specific destination IP address:port and
Tx source IP address, based on the satellite that covers your region. To
simplify this process, we provide a `bitcoin.conf` generator, which you can run
as follows:

```
blocksat-cli bitcoin-conf -d [datadir]
```

where `[datadir]` should be the target Bitcoin [data
directory](https://en.bitcoin.it/wiki/Data_directory) that you will use when
running Bitcoin Satellite (by default `~/.bitcoin/`).

Lastly, note that Bitcoin Satellite is a fork of Bitcoin Core Version 0.19,
hence other [Bitcoin Core configuration
options](https://wiki.bitcoin.com/w/Running_Bitcoin) are supported and can be
added to the generated `bitcoin.conf` configuration file as needed. For example,
to run the node based on satellite links only (unplugged from the internet), add
option `connect=0` to `bitcoin.conf`.

