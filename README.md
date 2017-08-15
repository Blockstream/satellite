# Blockstream Satellite Receiver

This repository contains the development source of the GNU Radio-based 
satellite receiver.  See the Wiki for setup and configuration information. 

Go to the #blockstream-satellite IRC channel on freenode for additional help.

## Running from a Fresh Installation

This receiver has been developed and tested for GNU Radio version 3.7.10 or higher.

In order to run the receiver from a fresh GNU radio installation,
first of all the custom modules have to be installed. To do so, run:

```
./install_mods.sh
```

Also some flow-graphs rely on gr-framers, to install them for the first time run:

```
./install_gr_framers.sh
```

After that, the flowgraphs should be ready.
