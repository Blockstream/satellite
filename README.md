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
   [Interactive Coverage Map](http://www.blockstream.com/satellite/satellite).
2. Gather the required hardware - appropriate satellite dish, low-noise block
   downconverter (LNB), power supply, mounting hardware, SDR interface, cables
   and connectors.
3. Download the required software - Bitcoin FIBRE, GNU Radio and GR OsmoSDR.
4. Install the receiver and software dependencies.
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
$ sudo apt-get install gnuradio=3.7.11\* gr-osmosdr
```
(Fedora)
```
sudo dnf install gnuradio-3.7.11* gnuradio-devel gr-osmosdr
```

The above installation points to version 3.7.11 of GNU Radio, but you can
install 3.7.10 or any later version.

Check if the version is available via package manager, e.g. in Ubuntu/Debian:

```
apt-cache policy gnuradio
```

If a suitable version is not available, you can either search for a repository
that provides the package or use PyBOMBS.

## GNU Radio and OsmoSDR via PyBOMBS

**NOTE:** PyBOMBS detects if a binary package is available. In case it is not,
it will build from source. Hence, please note that this method can take much
longer.

Please follow the instructions from
[github.com/gnuradio/pybombs](https://github.com/gnuradio/pybombs#quickstart).

In summary, the following steps can be used:
```
sudo apt-get install pip
sudo pip install PyBOMBS
pybombs auto-config
pybombs recipes add-defaults
pybombs prefix init ~/prefix -a myprefix -R gnuradio-default
source ~/prefix/setup_env.sh
```

Make sure you understand the concept of prefixes in PyBOMBS, explained in the
above link. More importantly, ensure that GNU Radio 3.7.10 or later is installed
when using this method.

## Build the Project

Assuming you have `make`, `cmake` and `swig`, build and install the Blockstream
Satellite receiver. In the root folder of this project, run:

```
$ make
```

Finally, install Bitcoin FIBRE: http://bitcoinfibre.org.

# Receiver Startup

After successful set-up of your receiver, run the receiver application with:

```
./rx.py -f [freq_in_hz]
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
./rx.py -f 1276150000 -g 40
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
./rx.py -f 1276150000 -s
```

The scan mode is recommended also if you are not sure about the stability of
your LNB.

## Split Receiver Mode (Using a Raspberry Pi)

You can also split your receiver into two different hosts. In this case, one
computer is connected to the SDR board and correspondingly the LNB/dish. The
other computer receives the processed data over the network (via TCP/IP) and
runs Bitcoin FIBRE. This can be useful when, due to space and cabling
limitations, only a small form factor computer (e.g. a Raspberry Pi) can be
connected to the antenna. The setup is illustrated below:

<img src="doc/split_rx.png" width="80%"/>

The wiki explains how to
[**run the receiver in Split Mode**](../../wiki/Running-the-System#split_mode).

# Bitcoin FIBRE Startup

Bitcoin FIBRE uses the same `bitcoin.conf` configuration file as Bitcoin Core.
Configure as needed and start `bitcoind` with the following parameters after the
receiver (above) is running:

```
./bitcoind -fecreaddevice=/tmp/async_rx
```

>Note: The Blockstream Satellite receiver will create the `/tmp/async_rx` file.

# Setup Complete

Once both the Blockstream Satellite Receiver and Bitcoin FIBRE are running, your
node will stay in sync!

