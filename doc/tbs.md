---
parent: Receiver Setup
nav_order: 2
---

# TBS Linux USB Receiver

The TBS 5927 and TBS 5520SE devices are USB-based DVB-S2 receivers. They
receive the satellite signal fed via a coaxial interface and output data to the
host over USB. They are also configured directly over USB, and the host is
responsible for setting such configurations using specific Linux tools.

The instructions that follow prepare the host for driving the TBS receiver.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [TBS Linux USB Receiver](#tbs-linux-usb-receiver)
    - [Hardware Connections](#hardware-connections)
    - [TBS Drivers](#tbs-drivers)
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

The TBS 5927/5520SE should be connected as follows:

![TBS5927 connections](img/usb_connections.png?raw=true "TBS5927 connections")

- Connect the LNB directly to "LNB IN" interface of the TBS 5927/5520SE using a
  coaxial cable (an RG6 cable is recommended).
- Connect the TBS's USB2.0 interface to your computer.
- Power up the TBS device. For the TBS 5927 model, connect the 12V DC power
  supply. For the TBS 5520SE, connect both male connectors of the dual-male USB
  Y cable to your host.


## TBS Drivers

Next, you will need to install specific device drivers to use the TBS 5927 or
5520SE receivers. These are installed by rebuilding and rewriting the Linux
Media drivers. Hence, if you are not setting up a dedicated machine to host the
TBS receiver, it would be safer and **recommended** to use a virtual machine
(VM) as the receiver host so that the drivers can be installed directly on the
VM instead of your main machine.

To install the drivers, run the following command:

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

> Note: this command supports the `apt`, `dnf` and `yum` package managers. For
> other package managers, refer to the [manual installation
> instructions](#install-binary-packages-manually) and adapt package names
> accordingly.

## Configure the Host

Next, you need to create and configure a network interface to output the IP
traffic received via the TBS 5927/5520SE unit. You can do so by running the
following command:

```
blocksat-cli usb config
```

If you would like to review the changes before applying them, first run the
command in dry-run mode:

```
blocksat-cli usb config --dry-run
```

Note this command will define an arbitrary IP address to the interface. If you
would like to set a specific IP address instead, for example, to avoid address
conflicts, use the command-line argument `--ip`.

Furthermore, note that this configuration is not persistent across
reboots. After a reboot, you need to run `blocksat-cli usb config` again.

## Launch

Finally, start the receiver by running:

```
blocksat-cli usb launch
```

## Next Steps

At this point, if your antenna is already correctly pointed, you should be able
to start receiving data on Bitcoin Satellite. Please follow the instructions for
[Bitcoin Satellite configuration](bitcoin.md). If your antenna is not pointed
yet, refer to the [antenna alignment guide](antenna-pointing.md).

## Further Information

### Docker

A Docker image is available for running the Linux USB receiver host on a
container. Please refer to the instructions in the [Docker guide](docker.md).

### Useful Resources

- [TBS 5927 Datasheet](https://www.tbsiptv.com/download/tbs5927/tbs5927_professtional_dvb-S2_TV_Tuner_USB_data_sheet.pdf).
- [TBS 5520SE Datasheet](https://www.tbsiptv.com/download/tbs5520se/tbs5520se_multi_standard_universal_tv_tuner_box_data_sheet.pdf).
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

On Fedora, package `dvb-apps` is not available via the main dnf repository. In
this case, you can install it from our repository by running:

```
sudo dnf copr enable blockstream/satellite
sudo dnf install dvb-apps
```

> If command `dnf copr enable` is not available in your system, install package
> `dnf-plugins-core`.


### Building dvb-apps from source

Alternatively, you can build `dvb-apps` from source by running the following
commands:

```
git clone https://github.com/Blockstream/dvb-apps
cd dvb-apps
make
sudo make install
```

---

Prev: [Receiver Setup](receiver.md) - Next: [Bitcoin Satellite](bitcoin.md) or [Antenna Pointing](antenna-pointing.md)
