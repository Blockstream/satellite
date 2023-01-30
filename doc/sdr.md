---
parent: Receiver Setup
nav_order: 4
---

# SDR Receiver

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Connections](#connections)
- [Software Requirements](#software-requirements)
- [Configuration](#configuration)
- [Running](#running)
- [Next Steps](#next-steps)
- [Further Information](#further-information)
  - [Software Updates](#software-updates)
  - [Docker](#docker)
  - [gr-dvbs2rx Receiver](#gr-dvbs2rx-receiver)
  - [Manual Installation of SDR Software](#manual-installation-of-sdr-software)
  - [Manual Compilation of SDR Software](#manual-compilation-of-sdr-software)

<!-- markdown-toc end -->

## Connections

The SDR setup is connected as follows:

![SDR connections](img/sdr_connections.png?raw=true "SDR connections")

- Connect the RTL-SDR USB dongle to your host PC.
- Connect the **non-powered** port of the power supply (labeled as “Signal to IRD”) to the RTL-SDR using an SMA cable and an SMA-to-F adapter.
- Connect the **powered** port (labeled “Signal to SWM”) of the power supply to the LNB using a coaxial cable (an RG6 cable is recommended).

**IMPORTANT**: Do NOT connect the powered port of the power supply to the SDR interface. Permanent damage may occur to your SDR and/or your computer.

## Software Requirements

The SDR-based setup relies on the applications listed below:

- [leandvb](http://www.pabr.org/radio/leandvb/leandvb.en.html): a software-based DVB-S2 receiver application.
- [rtl_sdr](https://github.com/osmocom/rtl-sdr): reads samples taken by the RTL-SDR and feeds them into [leandvb](http://www.pabr.org/radio/leandvb/leandvb.en.html).
- [TSDuck](https://tsduck.io/): unpacks the output of leandvb and produces IP packets to be fed to [Bitcoin Satellite](bitcoin.md).
- [Gqrx](https://gqrx.dk): useful for spectrum visualization during antenna pointing.

To install them all at once, run the following:

```
blocksat-cli deps install
```

> Note: this command supports the two most recent releases of Ubuntu LTS, Fedora, CentOS, Debian, and Raspbian. In case you are using another Linux distribution or version, please refer to the [manual compilation and installation instructions](#manual-compilation-of-sdr-software).

If you prefer to install all software components manually, please refer to the [manual installation section](#manual-installation-of-sdr-software). Also, if you would like to try the alternative receiver application based on the [GNU Radio](https://www.gnuradio.org) framework, see the [gr-dvbs2rx section](#gr-dvbs2rx-receiver).

## Configuration

After installing, you can generate the configurations that are needed for gqrx by running:

```
blocksat-cli gqrx-conf
```

> Note: this command assumes you are using an RTL-SDR dongle.

## Running

You should now be ready to launch the SDR receiver. You can run it by executing:

```
blocksat-cli sdr
```

More specifically, as thoroughly explained in the [antenna alignment section](antenna-pointing.md#sdr-based), you might want to run with specific gain and de-rotation parameters that are suitable to your setup, like so:

```
blocksat-cli sdr -g [gain] --derotate [freq_offset]
```

where `[gain]` and `[freq_offset]` should be substituted by the appropriate values.

## Next Steps

At this point, if your antenna is already correctly pointed, you should be able to start receiving data on Bitcoin Satellite. Please follow the instructions for [Bitcoin Satellite configuration](bitcoin.md). If your antenna is not aligned yet, refer to the [antenna alignment guide](antenna-pointing.md).

## Further Information

### Software Updates

To update the SDR software to the most recent releases, run:

```
blocksat-cli deps update
```

### Docker

A Docker image is available for running the SDR host on a container. Please refer to the instructions in the [Docker guide](docker.md).

### gr-dvbs2rx Receiver

An alternative software-defined DVB-S2 receiver implementation named gr-dvbs2rx is available on the CLI starting from version 0.4.5. This alternative application is based on the [GNU Radio](https://www.gnuradio.org) framework for software-defined radio.

To try gr-dvbs2rx, first, run the command below to install it. The installation is supported on Fedora 36 and Ubuntu 22.04 or later versions.

```
blocksat-cli deps install --gr-dvbs2rx
```

Then, use the `--impl gr-dvbs2rx` option when launching the receiver, as follows:

```
blocksat-cli sdr --impl gr-dvbs2rx
```

### Manual Installation of SDR Software

If you do not wish to rely on the automatic installation handled by command `blocksat-cli deps install`, you can install all applications manually.

First, enable our repository for binary packages. On Ubuntu/Debian, run:

```
add-apt-repository ppa:blockstream/satellite
apt-get update
```

> If command `add-apt-repository` is not available in your system, install package `software-properties-common`.

On Fedora, run:
```
dnf copr enable blockstream/satellite
```

> If command `copr enable` is not available in your system, install package `dnf-plugins-core`.

Finally, install the applications:

```
sudo apt install rtl-sdr leandvb tsduck gqrx-sdr
```
or
```
sudo dnf install rtl-sdr leandvb tsduck gqrx
```

### Manual Compilation of SDR Software

If `leandvb` and (or) `tsduck` are not available as binary packages in your distribution, you can build and install them from source.

#### Leandvb from source

To build leandvb from source, first install the dependencies:

```
apt install git make g++ libx11-dev
```
or
```
dnf install git make g++ libX11-devel
```

Then, run:

```
git clone --recursive https://github.com/Blockstream/leansdr.git
cd leansdr/src/apps
make
sudo install leandvb /usr/bin
```

Next, build and install `ldpc_tool`:

```
cd ../../LDPC/
make CXX=g++ ldpc_tool
sudo install ldpc_tool /usr/bin
```

#### TSDuck from source

To build and install TSDuck from source, run:

```
git clone https://github.com/tsduck/tsduck.git
cd tsduck
build/install-prerequisites.sh
make NOTELETEXT=1 NOSRT=1 NOPCSC=1 NOCURL=1 NODTAPI=1
sudo make NOTELETEXT=1 NOSRT=1 NOPCSC=1 NOCURL=1 NODTAPI=1 install
```

---

Prev: [Receiver Setup](receiver.md) - Next: [Bitcoin Satellite](bitcoin.md) or [Antenna Pointing](antenna-pointing.md)
