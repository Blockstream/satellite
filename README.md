# Blockstream Satellite Receiver

This repository contains the development sources of the GNU Radio-based receiver
for the Blockstream Satellite network.

In order to set up your receiver system, please read the following information
carefully and follow the instructions outlined in the [wiki](../../wiki). For
additional help, go to the #blockstream-satellite IRC channel on freenode.

This is an initial release and regular improvements will be made to make
Blockstream Satellite more user friendly and less technically complex.

# Getting Started

During your initial set-up, you will need to go through the following steps:

1. Check your coverage at Blockstream's
   [Interactive Coverage Map](https://blockstream.com/satellite/#satellite_network-coverage).
2. Get the required hardware - software defined radio (SDR) interface, satellite
   dish/antenna, low-noise block downconverter (LNB), power supply, mounting
   hardware, cables and connectors.
3. Install the required software - Bitcoin FIBRE, GNU Radio and GR OsmoSDR.
4. Install the satellite receiver.
5. Align your satellite dish with the help of the receiver application.

All of these steps are thoroughly explained in [**the wiki**](../../wiki), which
you should read next.

# Quickstart

The following instructions consist in the minimal/quickest possible
setup. However, it is likely that extra configuration will be needed. Hence, it
is highly recommeded to follow the wiki first.

## GNU Radio and OsmoSDR via Binary Package Manager

Install GNU Radio and OsmoSDR:

(Ubuntu/Debian)
```
$ sudo apt-get install gnuradio gr-osmosdr
```
(Fedora)
```
sudo dnf install gnuradio gnuradio-devel gr-osmosdr
```

The GNU Radio version is reuqired to be 3.7.9 or later. This is met by the
versions that are available in Ubuntu 16.04 and Fedora 26 or any subsequent
Ubuntu/Fedora release.

## Build and Install the Blockstream Satellite Receiver

Assuming you have `make`, `cmake` and `swig`, build and install the receiver
dependencies. In the root folder of this project, run:

```
$ make framers
$ sudo make install-framers
$ make blocksat
$ sudo make install-blocksat
```

Then, build and install the Blockstream Satellite receiver applications:
```
$ make
$ sudo make install
```

Finally, install Bitcoin FIBRE: http://bitcoinfibre.org.

# Receiver Startup

After successful set-up of your receiver, run the receiver application with:

```
blocksat-rx -f [freq_in_hz]
```

**Parameters:**

- `freq_in_hz`: the frequency parameter, **specified in units of Hz**.  This
parameter should be equal to the difference between your satellite's frequency
and the frequency of your LNB local oscillator (LO).  For more details on how to
compute it, see the
[Antenna Alignment guide](../../wiki/Antenna-Alignment#freq_param).

There are several optional parameters. For example, you can try adjusting the
gain using option `-g`. See more information in the
[wiki](../../wiki/Running-the-System).

**Example:**

```
blocksat-rx -f 1276150000 -g 40
```

**NOTE:** The frequency parameter is specified in Hz. So 1276.15 MHz would be
specified as 1276150000 Hz, as in the above example.

## Frequency Scan Mode

In case the stability of your LNB exceeds `+-200` kHz, it is advisable
to start the receiver in **scan mode**. See the explanation in
[**the wiki**](../../wiki/Running-the-System#scan_mode). This mode will first
sweep a wider range of frequencies and then pick a suitable frequency to start
receiving on.

To use the scan mode, run the receiver with the `-s` flag:

```
blocksat-rx -f 1276150000 -s
```

The scan mode is recommended also if you are not sure about the stability of
your LNB.

## Split Receiver Mode

You can also split your receiver into two different hosts. In this case, one
computer is connected to the SDR board and correspondingly the LNB/dish. The
other computer receives the processed data over the network (via TCP/IP) and
runs Bitcoin FIBRE. This can be useful when, due to space and cabling
limitations, only a small form factor computer can be connected to the antenna.

The wiki explains how to
[**run the receiver in Split Mode**](../../wiki/Running-the-System#split_mode).

# Bitcoin FIBRE Startup

Bitcoin FIBRE uses the same `bitcoin.conf` configuration file as Bitcoin Core.
Configure as needed and start `bitcoind` with the following parameters after the
satellite receiver is running:

```
./bitcoind -fecreaddevice=/tmp/blocksat/bitcoinfibre
```

>Note: The Blockstream Satellite receiver will create the `/tmp/blocksat/bitcoinfibre` file.

