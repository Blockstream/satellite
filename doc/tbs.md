# TBS5927 Professional DVB-S2 TV Tuner USB

The TBS 5927 is a USB receiver, which will receive data from satellite and will
output data to the host over USB. The host, in turn, is responsible for
configuring the receiver using specific DVB-S2 tools. Hence, next, you need to
prepare the host for driving the TBS 5927.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [TBS5927 Professional DVB-S2 TV Tuner USB](#tbs5927-professional-dvb-s2-tv-tuner-usb)
    - [Hardware Connections](#hardware-connections)
    - [TBS 5927 Drivers](#tbs-5927-drivers)
    - [Setup Configuration Helper](#setup-configuration-helper)
    - [Software Requirements](#software-requirements)
    - [Configure the Host](#configure-the-host)
    - [Launch](#launch)
    - [Next Steps](#next-steps)
    - [Further Information](#further-information)
        - [Docker](#docker)
        - [Useful Resources](#useful-resources)
        - [Install Binary Packages Manually](#install-binary-packages-manually)
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

Next, install the drivers for the TBS 5927 by running:

```
blocksat-cli deps tbs-drivers
```

Once the script completes the installation, reboot the virtual machine.

## Setup Configuration Helper

Some configurations depend on your specific setup. To obtain detailed
instructions, please run the configuration helper and the instructions menu as
follows:

```
blocksat-cli cfg
blocksat-cli instructions
```

## Software Requirements

Now, install all software pre-requisites (in the virtual machine) by running:

```
blocksat-cli deps install
```

> NOTE: this command supports the `apt`, `dnf` and `yum` package managers. For
> other package managers, refer to the instructions [by the end of this
> guide](#install-binary-packages-manually) and adapt package names accordingly.

## Configure the Host

Next, you need to create and configure the network interfaces that will output
the IP traffic received via the TBS5927. You can apply all configurations by
running the following command:

```
sudo blocksat-cli usb config
```

If you would like to review the changes that will be made before applying them,
first run the command as a non-root user:

```
blocksat-cli usb config
```

Note this command will define arbitrary IP addresses to the interfaces. If you
need (or want) to define specific IP addresses instead, for example to avoid IP
address conflicts, use command-line argument `--ip`.

Furthermore, note that this configuration is not persistent across reboots. If
you reboot you computer, you need to run `sudo blocksat-cli usb config` again.

## Launch

Finally, start the receiver by running:

```
blocksat-cli usb launch
```

> NOTE: you can run this command with a non-root user. Only the configuration
> step (`blocksat-cli usb config`) requires root access.

At this point, if your dish is already correctly pointed, you should be able to
start receiving data on Bitcoin Satellite. Please follow the [instructions for
Bitcoin Satellite configuration](bitcoin.md). If your antenna is not pointed
yet, please follow the [antenna alignment guide](antenna-pointing.md).

## Next Steps

At this point, if your antenna is already correctly pointed, you should be able
to start receiving data on Bitcoin Satellite. Please follow the [instructions
for Bitcoin Satellite configuration](bitcoin.md). If your antenna is not pointed
yet, refer to the [antenna alignment guide](antenna-pointing.md).a

## Further Information

### Docker

There is a Docker image available in this repository for running the Linux USB
receiver host on a container. Please refer to instructions in the [Docker
guide](../docker/README.md).

### Useful Resources

- [TBS 5927 User guide](https://www.tbsiptv.com/download/tbs5927/tbs5957_user_guide.pdf)
- [TBS 5927 Datasheet](https://www.tbsiptv.com/download/tbs5927/tbs5927_professtional_dvb-S2_TV_Tuner_USB_data_sheet.pdf)
- [TBS Drivers Wiki](https://github.com/tbsdtv/linux_media/wiki).

### Install Binary Packages Manually

The following instructions are an alternative to the automatic installation via
the CLI (with command `blocksat-cli deps install`).

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

Specifically on Fedora 31 and 32, package `dvb-apps` is not available via the
main dnf repository. In this case, you can install it from our repository, by
running:

```
sudo dnf copr enable blockstream/satellite
sudo dnf install dvb-apps
```

> If command `dnf copr enable` is not available in your system, install package
> `dnf-plugins-core`.

Alternatively, you can build `dvb-apps` from source. Refer to the [instructions
presented further below.](#building-dvb-apps-from-source)


### Building dvb-apps from source

If instead of installing `dvb-apps` from a binary package you desire to build it
from source, here are the instructions:

```
git clone https://github.com/Blockstream/dvb-apps
cd dvb-apps
make
sudo make install
```

