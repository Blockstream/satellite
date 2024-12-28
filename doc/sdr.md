---
parent: Receiver Setup
nav_order: 4
---

# SDR Receiver

<!-- markdown-toc start -->
**Table of Contents**

- [Connections](#connections)
- [Software Requirements](#software-requirements)
- [Running](#running)
- [Next Steps](#next-steps)
- [Further Information](#further-information)
  - [Docker](#docker)
  - [gr-dvbs2rx Receiver](#gr-dvbs2rx-receiver)
  - [Gqrx Configuration](#gqrx-configuration)
  - [Manual Installation of SDR Software](#manual-installation-of-sdr-software)
  - [Manual Compilation of SDR Software](#manual-compilation-of-sdr-software)
<!-- markdown-toc end -->

## Connections

The software-defined radio (SDR) setup is connected as follows:

![SDR connections](img/sdr_connections.png?raw=true "SDR connections")

- Connect the RTL-SDR USB dongle to your host PC.
- Connect the **non-powered** port of the power supply (labeled as “Signal to IRD”) to the RTL-SDR using an SMA cable and an SMA-to-F adapter.
- Connect the **powered** port (labeled “Signal to SWM”) of the power supply to the LNB using a coaxial cable (an RG6 cable is recommended).

**IMPORTANT**: Do NOT connect the powered port of the power supply to the SDR interface. Permanent damage may occur to your SDR and/or your computer.

## Software Requirements

Next, ensure all software prerequisites are installed on your host. If using the GUI, in case some dependencies are missing, click on the "Install Dependencies" button on the Receiver tab, as shown below. If you cannot see the button, all dependencies are already installed correctly.

![GUI Receiver Missing Dependencies](img/gui_receiver_missing_deps.png?raw=true)

If using the CLI, run the following command to ensure all dependencies are installed:

```
blocksat-cli deps install
```

> Note: this step works with the two most recent releases of Ubuntu LTS, Fedora, Debian, and Raspbian. In case you are using another Linux distribution or version, please refer to the [manual compilation and installation instructions](#manual-compilation-of-sdr-software).

## Running

You should now be ready to launch the SDR receiver. If using the GUI, click on the "Run Receiver" button on the Receiver tab, shown above. After that, you can monitor the receiver in real time as follows:

![GUI SDR Receiver Monitoring](img/gui_sdr_rx.png?raw=true)

If using the CLI, run the following command:

```
blocksat-cli sdr
```

More specifically, as thoroughly explained in the [antenna alignment section](antenna-pointing.md#sdr-based), you likely need to run with specific gain and de-rotation parameters suitable to your setup. With the GUI, you can set these in the Options panel. With the CLI, you use the `--gain` and `--derotate` command-line parameters, like so:

```
blocksat-cli sdr --gain [gain] --derotate [freq_offset]
```

where `[gain]` and `[freq_offset]` should be substituted by the appropriate values.

## Next Steps

At this point, if your antenna is already correctly pointed, you should be able to start receiving data on Bitcoin Satellite. Please follow the [Bitcoin Satellite configuration instructions](bitcoin.md). If your antenna is not aligned yet, refer to the [antenna alignment guide](antenna-pointing.md).

## Further Information

### Docker

A Docker image is available for running the SDR host on a container. Please refer to the instructions in the [Docker guide](docker.md).

### gr-dvbs2rx Receiver

The software-defined DVB-S2 receiver implementation named gr-dvbs2rx is available on the CLI starting from version 0.4.5. This application is based on the [GNU Radio](https://www.gnuradio.org) framework for software-defined radio, and it is supported on Fedora 36 and Ubuntu 22.04 or later versions only.

The GUI and CLI install gr-dvbs2rx automatically when available. Meanwhile, in Linux distributions other than Fedora and Ubuntu, the [leandvb](http://www.pabr.org/radio/leandvb/leandvb.en.html) receiver application is used instead. You can always toggle the implementation using CLI option `--impl` or the implementation field on the GUI.

### Gqrx Configuration

The GUI and CLI generate a configuration file for Gqrx to facilitate its use during antenna pointing. The GUI generates the file automatically on the receiver configuration wizard. Similarly, the CLI generates the configuration file automatically, but you can regenerate it manually by running the following command:

```
blocksat-cli gqrx-conf
```

> Note: this command assumes you are using an RTL-SDR dongle.

### Manual Installation of SDR Software

You can install all applications manually if you do not wish to rely on the automatic installation handled by the GUI or the CLI.

First, enable Blockstream Satellite's binary package repository. On Ubuntu/Debian, run:

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
sudo apt install rtl-sdr leandvb tsduck gqrx-sdr gr-dvbs2rx gr-osmosdr
```
or
```
sudo dnf install rtl-sdr leandvb tsduck gqrx gr-dvbs2rx gr-osmosdr
```

### Manual Compilation of SDR Software

If one of the applications is not available as binary packages in your distribution, you can build and install it from source, as follows:

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

#### gr-dvbs2rx from source

Please refer to the project's [installation instructions](https://igorauad.github.io/gr-dvbs2rx/docs/installation.html).

#### TSDuck from source

To build and install TSDuck from source, run:

```
git clone https://github.com/tsduck/tsduck.git
cd tsduck
build/install-prerequisites.sh
make NOTELETEXT=1 NOSRT=1 NOPCSC=1 NOCURL=1 NODTAPI=1
sudo make NOTELETEXT=1 NOSRT=1 NOPCSC=1 NOCURL=1 NODTAPI=1 install
```

> Refer to [TSDuck's documentation](https://tsduck.io/doxy/building.html) for further information.

---

Prev: [Receiver Setup](receiver.md) - Next: [Bitcoin Satellite](bitcoin.md) or [Antenna Pointing](antenna-pointing.md)
