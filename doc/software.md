---
title: Software Requirements
nav_order: 3
---

# Software Requirements

The next step is to install the Blockstream Satellite graphical user interface (GUI) and command-line interface (CLI) applications. Then, using either of the two interfaces, you can install the other software applications (the *dependencies*) required to configure and run your receiver.

To start, you should install the binary package containing the GUI and CLI. Currently, this package is available for Linux only (Ubuntu, Fedora, Debian, and Raspberry Pi OS), as explained next.

<!-- markdown-toc start -->
**Table of Contents**

- [Blockstream Satellite Software Installation](#blockstream-satellite-software-installation)
- [Receiver Configuration and Software Dependencies](#receiver-configuration-and-software-dependencies)
- [Further Information](#further-information)
  - [Installation via PyPI](#installation-via-pypi)
  - [Receiver Configuration using the CLI](#receiver-configuration-using-the-cli)
<!-- markdown-toc end -->

## Blockstream Satellite Software Installation

Please follow the installation instructions according to your Linux distribution.

Ubuntu:

```
add-apt-repository ppa:blockstream/satellite
apt-get update
apt-get install blockstream-satellite
```

> If command `add-apt-repository` is not available, install `software-properties-common`.

Fedora:

```
dnf copr enable blockstream/satellite
dnf install blockstream-satellite
```

> If command `dnf copr enable` is not available, install `dnf-plugins-core`.

Debian:

```
add-apt-repository https://aptly.blockstream.com/satellite/debian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt-get update
apt-get install blockstream-satellite
```

> Install `gnupg`, `apt-transport-https`, and `software-properties-common`, if necessary.

Raspberry Pi OS (formerly Raspbian):

```
add-apt-repository https://aptly.blockstream.com/satellite/raspbian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt-get update
apt-get install blockstream-satellite
```

> Install `gnupg`, `apt-transport-https`, and `software-properties-common`, if necessary.

## Receiver Configuration and Software Dependencies

Next, open the Blockstream Satellite GUI from the system applications menu.

> Alternatively, you can launch the GUI directly from the terminal by running the `blocksat-gui` application.

After opening it, the following home page should show up:

> Note: When opening the GUI for the first time, it may ask for permission to complete some initial configurations. Complete those first, then proceed.

![GUI home page](img/gui_home.png?raw=true)

Next, navigate to the "Receiver" tab at the top bar and click on "Create Receiver Configuration." After that, the configuration wizard will guide you through the remainder of the installation process, including the installation of software dependencies.

![GUI Receiver Configuration](img/gui_receiver_config.png?raw=true)

Finally, you can click on the "Run Receiver" button to start your receiver, as shown below. However, before doing so, make sure to connect the receiver appropriately, as discussed in the [next section](receiver.md).

![GUI Receiver Run](img/gui_receiver_run.png?raw=true)

## Further Information

### Installation via PyPI

The CLI and GUI are also available as Python3 packages from the Python Package Index (PyPI). You can install them by running the following command:

```
sudo pip3 install blocksat-cli blocksat-gui
```

> NOTE:
>
> 1. The above command requires the Python3 package installer ([pip3](https://pip.pypa.io/en/stable/installing/)) application.
>
> 2. If you prefer to install the CLI and GUI on your local user directory (without `sudo`) instead of installing it globally (with `sudo`), make sure to add `~/.local/bin/` to your path (e.g., with `export PATH=$PATH:$HOME/.local/bin/`).


### Receiver Configuration using the CLI

The same process described [above](#receiver-configuration-and-software-dependencies) for the GUI can be achieved directly on the terminal using the CLI.

First, run the configuration helper:

```
blocksat-cli cfg
```

Then, install the required software dependencies:

```
blocksat-cli deps install
```

Once the above command completes successfully, you can move on to the next section, which discusses the [receiver and host configuration](receiver.md).

---

Prev: [Hardware Components](hardware-components.md) - Next: [Receiver Setup](receiver.md)
