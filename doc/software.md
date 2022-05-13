---
title: Software Requirements
nav_order: 3
---

# Software Requirements

The Blockstream Satellite command-line interface (CLI) is required to configure and run your receiver. You can install it by executing the following command on the terminal:

```
sudo pip3 install blocksat-cli
```

> NOTE:
>
> 1. The CLI requires Python 3 and the above command requires Python3's package installer ([pip3](https://pip.pypa.io/en/stable/installing/)).
>
> 2. If you prefer to install the CLI on your local user directory (without `sudo`) instead of installing it globally (with `sudo`), make sure to add `~/.local/bin/` to your path (e.g., with `export PATH=$PATH:$HOME/.local/bin/`).

Next, run the configuration helper:

```
blocksat-cli cfg
```

Then, check out the instructions for your setup by running:

```
blocksat-cli instructions
```

Within the set of instructions, one of the required steps is the installation of software dependencies, which is accomplished by the following command:

```
blocksat-cli deps install
```

Once the above command completes successfully, you can move on to the next section, which discusses the [receiver and host configuration](receiver.md).

---

Prev: [Hardware Guide](hardware.md) - Next: [Receiver Setup](receiver.md)
