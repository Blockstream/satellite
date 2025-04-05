---
title: Software Requirements
nav_order: 3
---

# Software Requirements

The next step is to install the Blockstream Satellite graphical user interface (GUI) and command-line interface (CLI) applications. Then, using either of the two interfaces, you can install the other software applications (the *dependencies*) required to configure and run your receiver.

<!-- markdown-toc start -->
**Table of Contents**

- [Software Installation](#software-installation)
- [Receiver Configuration and Software Dependencies](#receiver-configuration-and-software-dependencies)
- [Further Information](#further-information)
  - [Receiver Configuration using the CLI](#receiver-configuration-using-the-cli)
<!-- markdown-toc end -->

## Software Installation

The user interface applications are provided within a single package called `blockstream-satellite`, which is available on multiple Linux distributions. Please follow the installation instructions according to your Linux distribution.

**Ubuntu:**

```bash
add-apt-repository ppa:blockstream/satellite
apt-get update
apt-get install blockstream-satellite
```

> If command `add-apt-repository` is not available, install the `software-properties-common` package.

**Fedora:**

```bash
dnf copr enable blockstream/satellite
dnf install blockstream-satellite
```

> If command `dnf copr enable` is not available, install the `dnf-plugins-core` package.

**Debian:**

```bash
add-apt-repository https://aptly.blockstream.com/satellite/debian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt-get update
apt-get install blockstream-satellite
```

> Install `gnupg`, `apt-transport-https`, and `software-properties-common`, if necessary.

**Raspberry Pi OS (formerly Raspbian):**

```bash
add-apt-repository https://aptly.blockstream.com/satellite/raspbian/
apt-key adv --keyserver keyserver.ubuntu.com \
    --recv-keys 87D07253F69E4CD8629B0A21A94A007EC9D4458C
apt-get update
apt-get install blockstream-satellite
```

> Install `gnupg`, `apt-transport-https`, and `software-properties-common`, if necessary.

Alternatively, the CLI and GUI applications can be installed as Python3 packages fetched from the Python Package Index (PyPI). For more information, see the [PyPI Python3 package installation section](#python3-package-installation-from-pypi).

## Receiver Configuration and Software Dependencies

Next, open the Blockstream Satellite GUI from the system applications menu or directly from the terminal by running the `blocksat-gui` application.

After opening it, the following home page should show up:

> Note: When opening the GUI for the first time, it may ask for permission to complete some initial configurations. Complete those first, then proceed.

![GUI home page](img/gui_home.png?raw=true)

Next, navigate to the "Receiver" tab at the top bar and click on "Create Receiver Configuration." After that, the configuration wizard will guide you through the remainder of the installation process, including the installation of software dependencies.

![GUI Receiver Configuration](img/gui_receiver_config.png?raw=true)

Finally, you can click on the "Run Receiver" button to start your receiver, as shown below. However, before doing so, make sure to connect the receiver appropriately, as discussed in the [next section](receiver.md).

![GUI Receiver Run](img/gui_receiver_run.png?raw=true)

## Further Information

### Python3 Package Installation from PyPI

You can install the CLI and GUI as Python3 packages by running the following command:

```bash
sudo pip3 install blocksat-cli blocksat-gui
```

> NOTE:
>
> 1. The above command requires the Python3 package installer ([pip3](https://pip.pypa.io/en/stable/installing/)) application.
>
> 2. If you prefer to install the CLI and GUI on your local user directory (without `sudo`) instead of installing it globally (with `sudo`), make sure to add `~/.local/bin/` to your path (e.g., with `export PATH=$PATH:$HOME/.local/bin/`).

### Receiver Configuration using the CLI

The same process described [above](#receiver-configuration-and-software-dependencies) can be achieved directly on the terminal using the CLI.

First, run the configuration helper:

```bash
blocksat-cli cfg
```

Then, install the required software dependencies:

```bash
blocksat-cli deps install
```

Once the above command completes successfully, you can move on to the next section, which discusses the [receiver and host configuration](receiver.md).

---

Prev: [Hardware Components](hardware-components.md) - Next: [Receiver Setup](receiver.md)
