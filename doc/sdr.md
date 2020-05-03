# SDR Setup

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [SDR Setup](#sdr-setup)
    - [Connections](#connections)
    - [Software Requirements](#software-requirements)
    - [Gqrx](#gqrx)
        - [From binary](#from-binary)
        - [From source](#from-source)
        - [Configuration](#configuration)
    - [Running](#running)
    - [Docker](#docker)
    - [Next Steps](#next-steps)

<!-- markdown-toc end -->

The instructions in this guide assume and have been tested with Ubuntu
18.04. Please adapt accordingly in case you are using another Linux distribution
or Ubuntu version.

## Connections

The SDR setup is connected as follows:

![SDR Connections](img/sdr_connections.png?raw=true "SDR Connections")

- Connect the RTL-SDR USB dongle to your host PC.
- Connect the **non-powered** port of the power supply (labeled as “Signal to
  IRD”) to the RTL-SDR using an SMA cable and an SMA-to-F adapter.
- Connect the **powered** port (labeled “Signal to SWM”) to the LNB using a
  coaxial cable (an RG6 cable is recommended).

## Software Requirements

The SDR-based relies on three application that follow:

- [leandvb](http://www.pabr.org/radio/leandvb/leandvb.en.html), a software-based
  DVB-S2 demodulator.
- [rtl_sdr](https://github.com/osmocom/rtl-sdr), which reads samples taken by
  the RTL-SDR and feeds them into
  [leandvb](http://www.pabr.org/radio/leandvb/leandvb.en.html).
- [TSDuck](https://tsduck.io/), which unpacks the output of leandvb and produces
  IP packets to be fed to [Bitcoin Satellite](bitcoin.md).

To install leandvb, first install the dependencies:

```
apt install make g++ libx11-dev libfftw3-dev
```

Then, on your directory of choice, run:

```
git clone --recursive https://github.com/Blockstream/leansdr.git
cd leansdr/src/apps
make
sudo install leandvb /usr/local/bin
```

Next, build and install `ldpc_tool`, which is used as an add-on to `leandvb`:

```
cd ../../LDPC/
make CXX=g++ ldpc_tool
sudo install ldpc_tool /usr/local/bin
```

To install the RTL-SDR application, run:

```
apt-get install rtl-sdr
```

Finally, to build TSDuck from source, run:

```
mkdir -p ~/src/
cd ~/src/
git clone https://github.com/tsduck/tsduck.git
cd tsduck
build/install-prerequisites.sh
make NOTELETEXT=1 NOSRT=1 NOPCSC=1 NOCURL=1 NODTAPI=1
```

And then add the following to your `.bashrc`:

```
source ~/src/tsduck/src/tstools/release-x86_64/setenv.sh
```

The above `setenv.sh` script sets environmental variables that are necessary in
order to use TSDuck.

## Gqrx

The gqrx application can be very helpful for pointing the antenna and for
troubleshooting. You can install it from binary package or from source.

### From binary

```
sudo apt install gqrx-sdr
```

### From source

First install dependencies:
```
apt-get install g++ pkg-config gnuradio gr-osmosdr qt5-default libqt5svg5-dev
```

The build gqrx:
```
cd ~/src/
git clone https://github.com/csete/gqrx.git
cd gqrx
mkdir build
cd build
qmake ..
make
```

Finally, install:
```
make install
```

### Configuration

After installing, you can generate the configurations that are needed for gqrx
by running:

```
blocksat-cli gqrx-conf
```

> NOTE: this assumes you are going to use gqrx with an RTL-SDR dongle.

## Running

You should now be ready to launch the SDR receiver. You can run it by executing:

```
blocksat-cli sdr
```

More specifically, as thoroughly explained in the [Antenna Pointing
Guide](antenna-pointing#sdr-based), you might want to run with specific gain and
de-rotation parameters that are suitable in your setup, like so:

```
blocksat-cli sdr -g [gain] --derotate [freq_offset]
```

where `[gain]` and `[freq_offset]` should be substituted by the appropriate
values.

Furthermore, in the SDR setup, you must choose which stream you would like to
receive from the two streams that are simultaneously broadcast through the
Blockstream Satellite network (refer to more information in the [Antenna
Pointing Guide](antenna-pointing#optimize-snr)).

By default, the application will try to decode the low-throughput stream. To try
decoding the high-throughput stream, run with option `-m high`, as follows:

```
blocksat-cli sdr -g [gain] --derotate [freq_offset] -m high
```

## Docker

There is a Docker image available in this repository for running the SDR
setup. Please refer to instructions in the [Docker guide](../docker/README.md).

## Next Steps

At this point, if your dish is already correctly pointed, you should be able to
start receiving data in Bitcoin Satellite. Please follow the [instructions for
Bitcoin Satellite configuration](bitcoin.md). If your antenna is not pointed
yet, please follow the [antenna alignment guide](antenna-pointing.md).

