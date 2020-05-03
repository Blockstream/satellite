# TBS5927 Professional DVB-S2 TV Tuner USB

The TBS 5927 is a USB demodulator, which will receive data from satellite and
will output data to the host over USB. The host, in turn, is responsible for
configuring the demodulator using specific DVB-S2 tools. Hence, next, you need
to prepare the host for driving the TBS 5927.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [TBS5927 Professional DVB-S2 TV Tuner USB](#tbs5927-professional-dvb-s2-tv-tuner-usb)
    - [Hardware Connections](#hardware-connections)
    - [TBS 5927 Drivers](#tbs-5927-drivers)
    - [Configuration Helper](#configuration-helper)
    - [Host Requirements](#host-requirements)
    - [Launch](#launch)
    - [Docker](#docker)
    - [Further Information](#further-information)
    - [Building dvb-apps from source](#building-dvb-apps-from-source)

<!-- markdown-toc end -->

## Hardware Connections

The TBS 5927 should be connected as follows:

![TBS5927 Connections](img/usb_connections.png?raw=true "TBS5927 Connections")

- Connect the LNB directly to "LNB IN" of the TBS 5927 using a coaxial cable (an
  RG6 cable is recommended).
- Connect the TBS 5927's USB interface to your computer.

## TBS 5927 Drivers

Before anything else, note that specific device drivers are required in order to
use the TBS5927. Please, do note that driver installation can cause corruptions
and, therefore, it is safer and **strongly recommended** to use a virtual
machine for running the TBS5927. If you do so, please note that all commands
recommended in the remainder of this page are supposed to be executed in the
virtual machine.

Next, install the drivers for the TBS 5927. A helper script is available in the
`util` directory from the root of this repository:

Run:

```
cd util/
./tbsdriver.sh
```

Once the script completes the installation, reboot the virtual machine.

## Setup Configuration Helper

Some configurations depend on your specific setup. To obtain detailed
instructions, please run the configuration helper as follows:

```
blocksat-cli cfg
```

Furthermore, in order to run the demodulator, it is necessary to have the
so-called *channel configuration file*. The above configuration helper will
generate this configuration file for you.

Also, the configuration helper will print out all instructions that follow.

## Host Requirements

Now, install all pre-requisites (in the virtual machine):

On Ubuntu/Debian:

```
sudo apt apt update
sudo apt install python3 iproute2 iptables dvb-apps dvb-tools
```

On Fedora:

```
sudo dnf update
sudo dnf install python3 iproute iptables dvb-apps v4l-utils
```

> NOTE: `iproute`/`iproute2` and `iptables` are used in order to ensure `ip` and
> `iptables` tools are available.


## Configure the Host

Run the following as root:

```
sudo blocksat-cli usb config
```

This script will create network interfaces in order to handle the IP traffic
received via the satellite link. It will define arbitrary IP addresses to the
interfaces. To define a specific IP instead, use command-line argument `--ip`.

> NOTE: root privileges are required in order to configure firewall and *reverse
> path (RP) filtering*, as well as accessing the adapter at `/dev/dvb`. You will
> be prompted to accept or refuse the firewall and RP configurations.

## Launch

Finally, launch the DVB-S2 interface by running:

```
blocksat-cli usb launch
```

> NOTE: you can run this command with a non-root user. Only the configuration
> step (`blocksat-cli usb config`) requires root access.

At this point, if your dish is already correctly pointed, you should be able to
start receiving data in Bitcoin Satellite. Please follow the [instructions for
Bitcoin Satellite configuration](bitcoin.md). If your antenna is not pointed
yet, please follow the [antenna alignment guide](antenna-pointing.md).

## Docker

There is a Docker image available in this repository for running the Linux USB
setup. Please refer to instructions in the [Docker guide](../docker/README.md).

## Further Information

- [User guide](https://www.tbsiptv.com/download/tbs5927/tbs5957_user_guide.pdf)
- [Datasheet](https://www.tbsiptv.com/download/tbs5927/tbs5927_professtional_dvb-S2_TV_Tuner_USB_data_sheet.pdf)
- [Drivers](https://github.com/tbsdtv/linux_media/wiki).

## Building dvb-apps from source

If instead of installing `dvb-apps` from binary packages you desire to build it
from source, here are some instructions:

```
git clone https://github.com/Blockstream/dvb-apps
cd dvb-apps
make
sudo make install
```

More information can be found at
[linuxtv's wiki page](https://www.linuxtv.org/wiki/index.php/LinuxTV_dvb-apps).

