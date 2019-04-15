# Blockstream Satellite Receiver

This repository contains the development sources of the GNU Radio-based receiver
for the Blockstream Satellite network.

In order to set up your receiver system, please read the following information
carefully. For additional help, go to the #blockstream-satellite IRC channel on
freenode.

## Required Version

**IMPORTANT:** Please note that the Blockstream Satellite network was updated
with backwards incompatible changes on March 11, 2019. From this date on, the
required Blockstream Satellite receiver version should be greater than or equal
to `v1.3.0`. The most recent version is `v1.4.0`, which is the recommended one.
Meanwhile, Bitcoin FIBRE should be the version from [the master
branch](https://github.com/bitcoinfibre/bitcoinfibre/tree/master).

# Getting Started

During your initial set-up, you will need to go through the following steps:

1. Check your coverage at Blockstream's
   [Interactive Coverage Map](https://blockstream.com/satellite/#satellite_network-coverage).
2. Get the required hardware - software defined radio (SDR) interface, satellite
   dish/antenna, low-noise block downconverter (LNB), power supply, mounting
   hardware, cables and connectors.
3. Install the required software - Bitcoin FIBRE, GNU Radio and GR OsmoSDR.
4. Install the satellite receiver.
5. Align your satellite dish with the help of the receiver application.

All of these steps are thoroughly explained next.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
# Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Software Installation](#software-installation)
    - [From Binary Packages](#from-binary-packages)
    - [From Source](#from-source)
- [Installation on Raspberry Pi](#installation-on-raspberry-pi)
- [Antenna Pointing](#antenna-pointing)
    - [1. Ideal Mounting Location](#1-ideal-mounting-location)
    - [2. Mount the Antenna](#2-mount-the-antenna)
    - [3. Prepare to Locate the Blockstream Satellite Signal](#3-prepare-to-locate-the-blockstream-satellite-signal)
    - [4. Connect the Equipment](#4-connect-the-equipment)
    - [5. Compute the receiver frequency](#5-compute-the-receiver-frequency)
    - [6. Search for the Blockstream Satellite Signal](#6-search-for-the-blockstream-satellite-signal)
    - [7. Next Steps](#7-next-steps)
- [Run the Receiver](#run-the-receiver)
  	- [GUI Mode](#gui-mode)
    - [Console-only Mode](#console-only-mode)
    - [Frequency Scan Mode](#frequency-scan-mode)
    - [Split Receiver Mode](#split-receiver-mode)
- [Run Bitcoin FIBRE](#run-bitcoin-fibre)
- [Satellite API](#satellite-api)
- [Frequent issues and questions](#frequent-issues-and-questions)

<!-- markdown-toc end -->

# Hardware Requirements

To utilize the Blockstream Satellite network, you must have the following
hardware at a minimum:
1. [Satellite dish (antenna)](#dish)
2. [LNB (linear polarization w/ LO stability <= 200 kHz)](#lnb)
3. [LNB power supply](#power)
4. [LNB mounting bracket](#mount)
5. [Software Defined Radio (SDR) interface](#sdr)
6. [Cables, connectors, and mounting hardware](#cable_conn)

These items are available from resellers around the world and we are currently
working with a vendor to provide complete kits and components.

## <a name="dish"></a> 1. Minimum 45cm/60cm Satellite Dish (bigger is better)

Blockstream Satellite is designed to work with small antennas. In Ku band, it is
expected to work with antennas of only 45cm in diameter, while in C band it is
expected to work with 60cm or higher. However, a larger antenna is always
better. When possible, we recommend installing an antenna larger than the
referred minimum if one is readily available. 60cm, 90cm, and 1.2m antennas are
readily available.

Other than size, the only additional requirement is that the antenna will work
with the frequency band that suits your coverage region.

### Satellite Frequency Bands

Blockstream Satellite operates in Ku high band, Ku low band and C band,
depending on region. Ku high band is used in North America and South America. Ku
low band is used in Africa and Europe. C band is used in Asia-Pacific region.

>C band: 3.7 GHZ - 4.2 GHz
>
>Ku low band: 10.7 to 11.7 GHz
>
>Ku high band: 11.7 to 12.75 GHz

You can always use antennas designed for higher frequencies. For example, an
antenna designed for Ka band will work for Ku bands and C band, as it is
designed for higher frequencies than the ones used by Blockstream
Satellite. However, a C band antenna will not work for Ku bands, as it is
designed for lower frequencies.

The following table summarizes the transmission bands of the satellites we use:

| Satellite          | Band    |
|--------------------|---------|
| Galaxy 18          | Ku High |
| Eutelsat 113       | Ku High |
| Telstar 11N Africa | Ku Low  |
| Telstar 11N Europe | Ku Low  |
| Telstar 18V        | C       |


## <a name="lnb"></a> 2. LNB

There are 3 parameters of an LNB that must be met in order to use
Blockstream Satellite:

### Frequency Range

First, you must verify that the input frequency range of the LNB encompasses the
frequency of the Blockstream Satellite signal in your coverage area. For
example, if you are located in North America and you are covered by the Galaxy
18 satellite, your Blockstream Satellite frequency is 12.02285 GHz. Thus, an LNB
that operates from 11.7 GHz to 12.2 GHz would work. In contrast, an LNB that
operates from 10.7 GHz to 11.7 GHz would NOT work.

**Note on “Universal” LNB:**

>A Universal LNB, also known as Universal Ku band LNB, is an LNB that supports
>both "Ku low" and "Ku high" bands. We recommend using this type of LNB only
>within Ku low band region, that is, within coverage of either Telstar 11N
>Africa or Telstar 11N Europe.
>
>The rationale is that a 22 kHz tone must be sent to the Universal LNB in order
>to switch its sub-band. However, since the setup described in this guide is
>receiver-only, it is not able to generate the 22 kHz tone by itself. Now,
>because the default Ku sub-band of Universal LNBs is typically the low band, it
>is often acceptable to use these within Ku low band region, as the 22 kHz tone
>generator won't be necessary.
>
>In case you do want to switch the sub-band of an Universal LNB in order to use
>it within Ku high band region, you will need to place a 22 kHz tone generator
>inline between the LNB and the power inserter. This is because the tone
>generator uses power from the inserter while delivering the tone directly to
>the LNB.
>
>Such tone generators can be found in the market as pure
>generators. Alternatively, you can get a "satellite finder" device that embeds
>a 22 kHz generator internally. If choosing the latter, it is important to note
>that the satellite finder must be one that can be used inline between the power
>supply and LNB, namely one with signal input (from LNB) and output (towards
>power inserter), i.e. with two connectors. Some finders have just a single
>connector as they are not intended to be used inline.

### Polarization

Blockstream Satellite requires an LNB with **Linear Polarization**. While most
Ku band LNBs are linearly polarized, some popular satellite TV services use
circular polarization. A circularly polarized LNB will NOT work with Blockstream
Satellite.

If an LNB is described to feature horizontal or vertical polarization, then it
is linear. In contrast, if an LNB is described as Right Hand or Left Hand
Circular Polarized (RHCP or LHCP), then it is circular and will NOT work with
Blockstream Satellite.

### LO Stability

Most LNBs will have a local oscillator (LO) stability parameter referred to as
“LO stability”, or metrics such as "LO accuracy" and "LO drift". These are
normally specified in +/- XX Hz, kHz or MHz. A stability specification of `<=
+/- 200 kHz` is preferable for better performance. However, if you would like
(or you need) to use a less stable LNB, it can also be used. The difference is
that, in this case, you will need to run the system in **Scan Mode**, as
described in [Frequency Scan Mode](#frequency-scan-mode).

An LNB that relies on a phase-locked loop (PLL) frequency reference is typically
more accurate and stable. Hence, we advise to look for a PLL LNB, instead of a
traditional dielectric oscillator (DRO) LNB.

**Note on LNBF:**

> The feedhorn is the horn antenna that attaches to the LNB. It collects the
> signals reflected by the satellite dish and feeds them into the LNB, towards
> the receiver. The acronym LNBF stands for "LNB with feedhorn" and refers to
> the LNB that already contains an integrated feedhorn. This is the most typical
> nowadays and, for this reason, almost always the term LNB already refers to a
> LNBF implicitly. To avoid confusion, we advise to look for an LNBF.

**In Summary:**

You are advised to use a PLL LNBF with linear polarization and LO stability
ideally within `+- 200 kHz` or less. The LNB should be suitable for the
frequency of the satellite covering your location. Also, to avoid the need of a
tone generator, Universal LNBs are not recommended within Ku high band region.

## <a name="power"></a>  3. LNB Power Inserter

Most LNBs require anywhere from 13 VDC to 30 VDC to be injected on its coaxial
port. For TV receivers, it is normally the receiver that provides power to the
LNB directly via the coaxial cable, so you wouldn't see an external power supply
in such setups. However, there are systems that rely on external power injectors
and, for this reason, these can be found easily in the market.

One particular technology that requires a power supply is the one known as
"Single Wire Multiswitch" (SWM). You can look for an SWM power inserter and use
it in your setup.

Just be sure to check the power/voltage requirement of your LNB and ensure that
your power injector matches. Also, note that some LNBs known as "dual
polarization LNBs" use the supplied voltage to switch between polarization
options. For instance, in the case of dual polarization linear LNB, to switch
between horizontal and vertical polarization. Thus, for example, by supplying 13
VDC you have horizontal, while with 18 VDC you have vertical
polarization. Please consider this when pointing your antenna if that is your
case.

## <a name="mount"></a> 4. LNB Mounting Bracket

The dish likely comes with a mounting bracket, but you’ll need one designed to
accept a generic LNB. Also, it is good to have a bracket that is flexible for
rotation of the LNB, so that you can control its "skew". Although all mounting
brackets do allow rotation, some can be limited in the rotation range.

Such mounting brackets attach to the feed arm of the antenna and have a circular
ring that will accept a generic LNB.

## <a name="sdr"></a>  5. Software Defined Radio Interface

There are many Software Defined Radio (SDR) interfaces in the market today.
Blockstream Satellite is currently predominantly used with the RTL-SDR, model
RTL2832U & R820T2, which is a low-cost SDR dongle. This is the SDR interface
that is mostly supported and the one that we recommend.

We recommend specifically an RTL-SDR dongle that features a
temperature-controlled crystal oscillator (TCXO), since this type of oscillator
promotes better frequency stability. There are a few models in the market
featuring TCXO with frequency accuracy within 0.5 ppm to 1.0 ppm.

**IMPORTANT:** For users within the coverage of satellite **Telstar 11N
Europe**, we recommend purchasing an RTL-SDR with **extended tuning range**. The
reason is that the satellite frequency in this area is such that, when using an
LNB for Ku low band (with `9.75` GHz LO), the RTL-SDR needs to be configured
with a frequency that is too close to the maximum supported frequency of the
RTL-SDR model that is recommended for other regions (with the R820T2 tuner). The
extended range RTL-SDR uses another tuner (the E4000), whose frequency range is
more than sufficient to cover the frequency that is necessary for Telstar 11N
Europe.

In addition to the RTL-SDR, there is also support for USRP SDRs, which is a
higher-cost SDR product family from Ettus Research. Besides, any other SDR
platform supported by [GNU Radio](https://www.gnuradio.org) can be used,
provided that it is able to receive frequencies within roughly the 1 GHz to 2
GHz range. Note, however, that in this case the Receiver's source code must be
modified to include the given SDR interface.

## <a name="cable_conn"></a>  6. Cables, Connectors and Mounting Hardware.

You’ll need to connect your SDR to a non-powered port on the LNB power
supply. The powered port of the power supply, in turn, will be connected to the
LNB. You’ll need to ensure that you have the necessary coaxial cables and
connectors to make these interfaces. The connections are illustrated below:

![Hardware Connections](doc/hardware_connections.png?raw=true "Hardware Connections")

**Note**: Not every RTL-SDR has the same interface connector. Some use the SMA
connector and some use MCX. Be sure to order the correct cable and adapters to
make the necessary connections.

# Software Installation

## From Binary Packages

There are currently binary packages to facilitate the installation in the
following distribution/releases:

- Ubuntu bionic (18.04)
- Fedora 28
- CentOS 7<sup>*</sup>

If using Ubuntu bionic, you can install the packages by running:

```
add-apt-repository ppa:blockstream/satellite
apt-get update
apt-get install satellite
```

This should install all dependencies, including GNU Radio and GrOsmoSDR. In case
the `add-apt-repository` command is not available in your system, you will need
to run `apt install software-properties-common`.

If using Fedora 28, run:

```
dnf copr enable blockstream/satellite
dnf install satellite
```

If the command `copr enable` is not available, you will need to install
`dnf-plugins-core`.

Lastly, if using CentOS 7, assuming you have EPEL package installed, run:

```
yum copr enable blockstream/satellite
yum install satellite
```

Similarly, if `copr enable` is not available in your system, you need to install
`yum-plugin-copr`.

Note that, if you don't have the EPEL package (or another source) installed in
your CentOS 7 system, the above won't find the `gnuradio` and `gr-osmosdr`
dependencies and consequently will fail. You can install EPEL using:

```
yum install epel-release
```

> <sup>*</sup>Note regarding CentOS 7: at the moment, the binary package for
> this distribution/release installs solely the console-only receiver
> applications. It does not install the applications that feature a GUI.

## From Source

### Dependencies

#### GNU Radio and GrOsmoSDR

The two main prerequisites to build and install the Blockstream Satellite
receiver from source are:

- GNU Radio: http://gnuradio.org (Version 3.7.10 or greater)
- gr-osmosdr: https://github.com/osmocom/gr-osmosdr

When installing these, just make sure to pick suitable versions. Blockstream
Satellite works with GNU Radio version 3.7.10 or later.

In case you are flexible with the distribution/release that you can use, we
advise using one of the following, where GNU Radio 3.7.11 is available:

- Ubuntu bionic (18.04)
- Fedora 28
- CentOS 7

The following commands attempt to install GNU Radio version 3.7.11, but you can
try 3.7.10 or any later version in case 3.7.11 is not available in your system:

**Debian/Ubuntu**:
```
apt install gnuradio=3.7.11* gr-osmosdr
```

**Fedora**

```
dnf install gnuradio-3.7.11 gr-osmosdr gnuradio-devel
```

**RHEL/CentOS**

```
yum install gnuradio-3.7.11 gr-osmosdr gnuradio-devel
```

**NOTE 1:** For the Fedora/RHEL/CentOS distributions, note that the GNU Radio
development package (`gnuradio-devel`) package is also needed. It is included in
the above commands.

**NOTE 2:** In CentOS, you need the EPEL package (or another source) in order to
find the `gnuradio` and `gr-osmosdr` packages. You can install it using:

```
yum install epel-release
```

#### Other Dependencies

Aside from GNU Radio and GrOsmoSDR, you should have `make`, `cmake` and
`swig`. For completeness, install the following packages before proceeding:

**Debian/Ubuntu**:
```
apt install make cmake swig pkg-config doxygen graphviz
```

**Fedora**
```
dnf install make cmake swig pkg-config doxygen graphviz gcc-c++ cppunit-devel
```

**RHEL/CentOS**

```
yum install make cmake swig pkg-config doxygen graphviz gcc-c++ cppunit-devel
```

### Build from Source and Install

#### Build and install gr-blocksat and gr-framers

After installing prerequisites, the next step is to build and install the
building blocks of the Blockstream Satellite receiver, that is, the GNU Radio
Out-of-Tree (OOT) modules named `gr-blocksat` and `gr-framers`. To do so, at the
root folder of the `satellite` repository, run:

```
$ make framers
$ sudo make install-framers
$ make blocksat
$ sudo make install-blocksat
```

#### Verify the Python packages

Before proceeding, ensure that the installed Python packages for *framers* and
*blocksat* can be found:

```
python -c "import framers; help(framers)"
python -c "import blocksat; help(blocksat)"
```

If nothing is displayed, then follow the solution in
[Import Error (FAQ section)](#import_error).
If you are on Fedora or CentOS, you will likely need to include the path as
follows:

```
export PYTHONPATH=/usr/local/lib64/python2.7/site-packages:$PYTHONPATH
```

#### Verify the shared libraries

Also, to prevent any errors on the next steps, make sure that the shared
libraries from `framers` and `blocksat` that were installed above can indeed be
located by your system.

If your are on Ubuntu, you will likely need to run:

```
ldd /usr/local/lib/python2.7/dist-packages/blocksat/_blocksat_swig.so  | grep blocksat
```

Meanwhile, if you are on Fedora/CentOS, you will probably need to run:

```
ldd /usr/local/lib64/python2.7/site-packages/blocksat/_blocksat_swig.so | grep blocksat
```

If the result is `not found`, then follow the solution in
[Segmentation Fault (FAQ section)](#seg_fault). This
will involve adding a path like `/usr/local/lib` (on Ubuntu) or
`/usr/local/lib64` (on Fedora/CentOS) to the search path of shared libraries,
as follows:

```
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# or

export LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH
```

Once the Python packages and the shared libraries are within reach, move on to
the next step.

#### Build and install the receiver applications

To do so, run:
```
$ make
$ sudo make install
```

> NOTE: In CentOS, depending on your GNU Radio installation, it is possible that
> you are only able to build and install the receiver applications that are
> console-only (without the GUI). This is the case when you see `Block key
> "qtgui_xxx" not found` during the `make` step.
>
> To do so, run:
> ```
> make GUI=0
> sudo make install
> ```
>
> Also, on a headless setup, you will need a virtual display server in order to
> build. You can follow the details on the [FAQ section](#display_server), but
> in summary you can overcome this by installing `xorg-x11-server-Xvfb` and
> running the build/install steps as follows:
>
> ```
> xvfb-run make GUI=0
> sudo make install
> ```

### Possible Issues:

1. `blocksat` or `framers` cannot be found ("ImportError")

   Ensure that Python can load modules from the location where `gr-framers` and
   `gr-blocksat` were installed. See the information in the
   [FAQ section](#import_error).

2. *Block key "blocksat_xxx" not found*

   The above solution is applicable.

3. Segmentation fault

   If running the system on a Red Hat-derived distributions, a quick test is to
   set the `LD_LIBRARY_PATH` environment variable to include the
   `/usr/local/lib` (or `/usr/local/lib64`) path. If this is not the case or if
   this does not solve the segmentation fault, please refer to the debugging
   information in the [FAQ section](#seg_fault).

4. GNU Radio development package

    If you see the error *Could not find a package configuration file provided
    by "Gnuradio"* during the `cmake` step of the above build, meaning
    `GnuradioConfig.cmake` or `gnuradio-config.cmake` files were not found, make
    sure to install the `gnuradio-devel` or `gnuradio-dev` package.

Further issues are listed at the [FAQ section](#frequent-issues-and-questions).

# Installation on Raspberry Pi

Blockstream Satellite v1.4.0 or later is confirmed to work with Raspberry Pi 3
B+ using Ubuntu MATE 18.04.02 for 64-bit architecture. To install on Raspberry,
proceed with the following steps:

1. Download [Ubuntu MATE Bionic for aarch64 (ARMv8)](https://ubuntu-mate.org/download/)
2. Flash the Ubuntu MATE OS into your microSD card. You can use a tool such as
   [balenaEtcher](https://www.balena.io/etcher/)
3. Follow the installation instructions for Ubuntu. Choose either to:
    - [Install from binary packages](#from-binary-packages)
    - [Build and install from Source](#from-source)

# Antenna Pointing

Aligning a satellite antenna is a precise procedure. Remember that the
satellites are over 35,000 km (22,000 mi) away. A tenth of a degree of error
will miss the satellite by more than 3500 km.

## 1. Ideal Mounting Location

Before mounting your satellite dish, it is important to consider the antenna
alignment angles required for your specific location of interest. To obtain
these, first use the tool below, available within Blockstream's coverage page:

[Dish Alignment Tool](https://blockstream.com/satellite/#satellite-resources)

After entering your address or latitude/longitude, this tool will give you three
parameters, azimuth, elevation and polarization angles, explained next.

> ### Azimuth
>
> The azimuth is the side to side adjustment angle of your antenna. If you think
> of the antenna fixed within a vertical plane and loose such that it can be
> rotated from side to side, the azimuth determines the direction to which it
> points after being rotated. 0 degrees refers to North, 90 degrees points to
> East, 180 degrees to South and 270 degrees to West.

> ### Elevation
>
> The elevation is the up and down adjustment of your antenna. The antenna
> aiming tool provides the number of degrees above the horizon to which your
> antenna must point. 0 degrees represents pointing at the horizon and 90
> degrees is pointing straight up.

> ### Polarity
>
> The polarization parameter is how many degrees your LNB will need to be
> rotated. Many LNBs will provide a scale of degrees to assist in setting the
> LNB skew.

Once you have your azimuth, elevation, and polarization, you can identify the
general direction your antenna must point. Use a compass or smartphone app to
visually check the direction. Ensure that there are no obstacles such as trees
or buildings in the path between your antenna location and the area of the sky
that your antenna will point. It is important that you have clear line of sight
to that area of the sky.

**NOTE:** There are many useful smartphone apps available for Android and iOS
that will aid in pointing your antenna. Some even have augmented reality
features that allow you to see the satellite in the sky so that you can ensure
you have good line of sight. We advise to use such apps, as they can be quite
helpful.

**IMPORTANT:** If using a compass app on a smartphone, make sure to configure
the app such that it displays "true north", instead of the "magnetic north".

## 2. Mount the Antenna

Now that you have verified you have clear line of sight, it is time to mount
your antenna. Install the satellite antenna according to the directions
accompanying it, or have it done professionally.

If you install it yourself, proceed with the following steps:

1. Certify that the pole on which the dish is mounted is completely level.
2. Set the elevation of the antenna to the parameter provided by the antenna
aiming tool (above). Remember this is the up and down angle. Many antennas will
have an elevation scale on the back of the dish that you can use to set the
approximate elevation.
3. Set the LNB polarization to the parameter provided by the antenna aiming
tool. This involves rotating the LNB. There is typically a polarization rotation
scale on the LNB or the LNB mounting bracket.

## 3. Prepare to Locate the Blockstream Satellite Signal

To locate the Blockstream Satellite signal and perform fine adjustments to your
antenna alignment, you will need:

- Computer connected to an SDR interface and with both GNU Radio and Blockstream
  Satellite Receiver installed.
- LNB power supply with electricity to power it.
- Coax cable to connect LNB to LNB power supply.
- Cable/adapters to connect the SDR to the LNB power supply. If using an RTL-SDR
that has SMA output and a power supply with F female connector in the input (the
most typical case), use a cable that has SMA male on one end and F male on the
other, or use a normal SMA cable (male on both ends) together with an SMA female
to F male adapter.

**NOTE:** This process is more easily performed with a laptop than can be
watched while moving the antenna. If you are not able to have a computer at the
antenna site, you’ll need two people: one to move the antenna and one to monitor
the laptop.

## 4. Connect the Equipment

1. With power disconnected from the LNB power supply, connect the SDR to the
**non-powered** port on the LNB power supply.

**IMPORTANT**: Do NOT connect the powered port of the LNB power supply to the
SDR interface. Permanent damage may occur to your SDR and/or your computer.

2. Connect the **powered** port of the LNB power supply to the LNB using coaxial
cable.

3. Turn the LNB power supply on.

>NOTE: If using a power injector designed for "Single Wire Multiswitch" (SWM)
>systems, the ports are typically labeled as follows. The **non-powered** port
>is labeled as “Signal to IRD”, which means "signal to integrated
>receiver/decoder". This is the port that should be connected to the
>RTL-SDR. The **powered** port, in turn, is labeled “Signal to SWM”. This is the
>port that should be connected to the LNB.

## 5. Compute the receiver frequency

You are almost ready to run the receiver. The only missing step is to compute
the frequency to be passed as argument to the receiver application.

The frequency parameter is computed based on the frequency of the satellite
covering your location and the frequency of your LNB's local oscillator (LO)
frequency, so it is specific to your setup.  In particular, it is given by the
difference between the two frequencies, as follows:

```
frequency_parameter = your_satellite_frequency - your_lnb_lo_frequency
```

To find your satellite's frequency, first go to
[blockstream.com/satellite](https://blockstream.com/satellite/#satellite_network-coverage)
and understand which one is your satellite (covering your location). You should
see the frequency listed in MHz. Then adjust for your LNB LO frequency.

For example, if your LNB has an LO frequency of 10750 MHz and you're connecting
to Eutelsat 113 at 12026.15 MHz, the frequency parameter becomes 1276.15 MHz,
that is:

```
12026.15 - 10750.00 = 1276.15 MHz.
   ^            ^          ^
   ^            ^          ^
sat_freq - lnb_freq = freq_param
```

The following table summarizes the frequencies that are required for the SDR
when considering the typical LNB LO frequencies:


|       LO Frequency |   5.15 GHz |   9.75 GHz |  10.60 GHz |  10.75 GHz |
| ------------------ | ---------- | ---------- | ---------- | ---------- |
|          Galaxy 18 |            |            | 1422850000 | 1272850000 |
|       Eutelsat 113 |            |            | 1426150000 | 1276150000 |
| Telstar 11N Africa |            | 1726750000 |            |            |
| Telstar 11N Europe |            | 1754020000 |            |            |
|        Telstar 18V | 1092500000 |            |            |            |

The above frequencies are within the following frequency bands:

|       LO Frequency |   5.15 GHz |   9.75 GHz |  10.60 GHz |  10.75 GHz |
| ------------------ | ---------- | ---------- | ---------- | ---------- |
|               Band |          C |     Ku Low |    Ku High |    Ku High |

### Run the Receiver application (GUI mode)

Assuming you have built and installed the receiver, now you can run:

```
blocksat-rx-gui -f [freq_in_hz] -g [gain]
```

<a name="rx_parameters"></a> **Parameters:**

- `freq_in_hz`: the frequency parameter, **specified in units of Hz**. That is,
in the previous example where the computed frequency was 1276.15 MHz, the
parameter would be specified as 1276150000 Hz.
- `gain`: the gain parameter is a value between 0 and 50. Higher gain values may
be required for long cable runs or LNBs with weak output. Some experimentation
may be required to identify the best value for your application, explained
later.

**Example:**

```
blocksat-rx-gui -f 1276150000 -g 40
```

### Possible Issues

- Ensure that your `PYTHONPATH` environment variable is set to the installed
location of `gr-framers` and `gr-blocksat`. Usually
`/usr/local/lib64/python2.7/site-packages` on RedHat/Fedora or
`/usr/local/lib64/python2.7/dist-packages` on Ubuntu.
- Ensure your `LD_LIBRARY_PATH` environment variable is set. Typically
`/usr/local/lib64`.

## 6. Search for the Blockstream Satellite Signal

1. Once `blocksat-rx-gui` is running, the first objective is to recognize the
   Blockstream Satellite signal band on the Overview tab of the GUI. Ideally,
   you would see a flat level spanning a frequency band (in the horizontal axis)
   of approximately 250 kHz, which corresponds to Blockstream Satellite's
   nominal system bandwidth.

2. If you cannot see the signal using your initial pointing parameters, try
   several small adjustments of elevation and azimuth around the angles that
   were given to you by the dish alignment tool. For example, keep the elevation
   angle fixed and very slowly move the antenna side to side (vary the azimuth
   angle). Alternatively, keep azimuth fixed and slowly vary the elevation.

>You can organize the procedure as follows. First change your elevation by 1
>degree. Then, sweep the antenna left and right through a wide azimuth
>range. Repeat this until you are able to find the signal.

**REMEMBER:**

>Even though a single degree may seem like a minuscule movement, each degree
>represents thousands of kilometers over the geosynchronous orbit.

The screenshot below illustrates the signal band visible at both the "Spectrum"
and "Spectrogram" plots of the Overview GUI tab. The signal on the right-hand
side is roughly from 50 kHz to 300 kHz, so it looks like our
signal. Importantly, note that in this case (captured on Eutelsat 113) there is
also a nearby transmission on the left-hand side of the plot. Although by
inspection we can tell that this other signal is not ours, the only way to
really know this is by checking the frame synchronization, which is the next
step.

![Signal visible on Spectrogram](doc/overview_page_signal.png?raw=true "Signal visible on Spectrogram")

3. Switch to the `Frame Sync` tab in the GUI. You should expect to see a clear peak
   there, as follows.

![Frame Timing Peak](doc/pmf_peak.png?raw=true "Frame Timing Peak")

The peak can be toggling up and down and alternating colors, blue and red. What
is really important is that it is strong and remains steadily in the same
position. It can be in any position within the plot window, but it must remain
in the same position for the system to be reliable.

If a steady peak has indeed been achieved, it is very likely that your receiver
has acquired the so-called "frame synchronization" state. Have a look at the
logs in the terminal. You should see the following message:

```
##########################################
-- Frame synchronization acquired
```

Furthermore, at this point, the following message is expected to be printed
periodically in the console:

```
--------------------------------------------------------------------------------
[Timestamp] Frame Timing => LOCKED	 Timing Indicator: STRONG
--------------------------------------------------------------------------------
```

If frame synchronization has not yet been acquired, you can do some
troubleshooting. If you see a clear signal in the Overview tab of the GUI, first
check the frequency offset of the signal. The receiver can correct a frequency
offset within `+- 250 kHz`. If the signal band is centered at a frequency beyond
this range, the options are **1)** to re-launch the receiver with a different
frequency; or **2)** to re-launch the receiver in *scan mode*, specifically by
adding `-s` flag to the `blocksat-rx-gui` command, as follows:

```
blocksat-rx-gui -f 1276150000 -s
```

![High frequency offset seen on Spectrogram](doc/overview_page_signal_offset.png?raw=true "High frequency offset seen on Spectrogram")

The scenario of a frequency offset exceeding the correction range is illustrated
in the screenshot above. Note that the signal band is clearly visible. However,
it is centered at approximately `-325` kHz. Thus, the frequency recovery
algorithm cannot correct the frequency and, as a result, frame synchronization
is not acquired. This situation can also be diagnosed by looking at the
"Freq. Sync" page of the GUI. The goal is to have the "red curve" (spectrum
after frequency correction) centered around the origin of the horizontal axis,
as illustrated below. However, if the signal center frequency is beyond the
correction limit, this won't be the case. As mentioned earlier, either adjust
the frequency parameter of the receiver or re-launch it in scan mode.

![Spectrum Found](doc/spectrum_found_bpsk.png?raw=true "Spectrum Found")

Now, if the signal band is clear and centered within `+-250` kHz, but you still
can't see a peak in the "Frame Sync" page or, correspondingly, you can't get
`Frame synchronization acquired` log in the console, it is possible that you are
seeing the wrong signal or pointed to the wrong satellite. If you see two
similar signal bands, both with an apparent `250` kHz flat level span, try
adjusting the frequency parameter such that only one of them is "visible" at a
time, based on the spectrum plots of the Overview tab. If that doesn't work,
then it is likely not a signal problem, but rather a satellite problem. Try
adjusting azimuth and/or elevation again to see if you can find a different
satellite near the nominal angles that you got from the dish alignment tool.

**ATTENTION:**

In Europe, there is a nearby satellite that transmits a similar signal band on a
similar frequency. Use the above instructions and particularly the "Frame Sync"
tab of the GUI in order to know when pointed correctly.

4. Now that frame synchronization has been acquired, we are mostly done. At this
   point, we can only pursue some improvements to the signal quality.

As a sanity check, switch to the `Phase Sync` page. You should see a
constellation composed by two clouds of points, one close to "-1" and the other
close to "+1". The more compact the point clouds are, the better your signal
quality.

![Constellation Diagram](doc/da_phase_rec_syms_bpsk.png?raw=true "Constellation")

To evaluate signal quality, the easiest way is to check the SNR that is being
printed in the console, as below:

```
[Timestamp] SNR [================                        ] 7.4401 dB
[Timestamp] SNR [================                        ] 7.5041 dB
[Timestamp] SNR [================                        ] 7.3762 dB
[Timestamp] SNR [================                        ] 7.3644 dB
[Timestamp] SNR [================                        ] 7.4068 dB
```

Keep an eye on these logs and then make very gentle adjustments to elevation,
azimuth and/or LNB skew. You can try adjusting all three parameters, but the
recommended approach is to try adjusting only one of them at a time. Make a
small change and check whether it has improved the SNR. Try to stop at the
optimal point in all of them.

6. Lastly, with the antenna pointing and LNB polarization fixed, we recommend
performing some quick experiments with the gain parameter of the receiver. This
is a command line argument to the receiver application. Try different values
between 0 and 50 and see if the SNR improves, for example:

```
# Attempt 1
blocksat-rx-gui --freq 1276150000 --gain 35

# Attempt 2
blocksat-rx-gui --freq 1276150000 --gain 45
```

## 7. Next Steps

Well done. Your receiver is properly set-up and you are now ready to run it
continuously. You have two options now:

1. Continue running in GUI mode, namely the above `blocksat-rx-gui` application.
2. Run the lightweight non-GUI receiver application, named `blocksat-rx`.

> If running on [Raspberry Pi](#installation-on-raspberry-pi), we recommend
> using the non-GUI `blocksat-rx` application.

Once the receiver is up and running, you can run the Bitcoin FIBRE application
receiving data via the Blockstream Satellite Network.

# Run the Receiver

After installing the Blockstream Satellite receiver, a few receiver applications
become available in the system. The two main applications are named
`blocksat-rx-gui` and `blocksat-rx`. These run the full receiver, with and
without the GUI, respectively. The other applications are explained later in
this guide.

## GUI Mode

In order to launch the receiver in GUI mode, run:

```
blocksat-rx-gui -f [freq_in_hz]
```

`freq_in_hz` is the frequency parameter, **specified in units of Hz**.

See the [Antenna Pointing Section](#5-run-the-blockstream-satellite-receiver)
for the computation of the frequency parameter.

**Example:**

```
blocksat-rx-gui -f 1276150000
```

You can see a full list of optional parameter using the help:
```
blocksat-rx-gui -h
```

## Console-only Mode

In order to run the lighter receiver that does not provide any GUI (only console
logs), execute:

```
blocksat-rx -f [freq_in_hz]
```

**Example:**

```
blocksat-rx -f 1276150000
```

## Frequency Scan Mode

The above frequency passed as argument `-f` to the receiver application
corresponds to the nominal (the ideal) frequency for your receiver. However, in
practice, the LNB deviates and does not place the satellite signal in this exact
frequency. This behavior is perfectly acceptable and is solved by the frequency
correction algorithm that runs in the Blockstream Satellite receiver, which can
correct up to an error of approximately `+- 200` kHz.

However, depending on the quality of your LNB, it is possible that the error
exceeds the correctable range. In this case, in order to find the satellite
signal during the receiver initialization, you should run in **scan mode**. This
will sweep a wider range of frequencies and stop as soon as the Blockstream
Satellite signal is found. By default, this procedure can take up to a bit more
than a minute, but will likely complete earlier, depending on the magnitude of
the frequency error introduced by your hardware. Also, by default it sweeps a
range of approximately `3.5` MHz around the nominal frequency.

To run in scan mode, use the `-s` flag in either the `blocksat-rx-gui`,
`blocksat-rx` or `blocksat-rx-lower` (see below) application:

```
blocksat-rx -f 1276150000 -s
```

If the specs of your LNB guarantee an error/stability that is less than `+- 1.75
MHz` (check the specification for “Stability” or “L.O. Stability”), then you can
configure a narrower search range to ensure a faster scan. For example:

```
blocksat-rx -f 1276150000 -s -n 4
```

Argument `-n` above determines the number of scan iterations. In this
case, it is reduced from 8 (default value) to 4, so that a range of
approximately `1.75` MHz (`+- 0.875` MHz) is scanned.

For more options, check the help:

```
blocksat-rx -h
```

## Split Receiver Mode

The split receiver mode is intended to support the case where one computer (SDR
host) is connected to the SDR/LNB/dish and the data is ultimately supposed to be
processed at another host. This can be useful when, due to space and cabling
limitations, it is preferable to use a small form factor computer connected to
the antenna.

In this mode, the receiver stack is split between the SDR host and the PC. The
SDR host implements the lower part of the stack, namely the layer that is closer
to the physical medium. The other host, then, implements the upper part of the
stack and delivers the data to the Bitcoin FIBRE application. They communicate
to each other via TCP/IP.

To use this setup, first, in the SDR host, run:
```
blocksat-rx-lower -f [freq_in_hz] -i [IP] -p [Port]
```
where `[ip]` should be set to the IP address of the local
network interface and port is the TCP port to be used.

**NOTE**:

> 1. The `blocksat-rx-lower` application behaves as TCP server, so it should be
> executed first.
> 2. In case multiple network interfaces are used in the SDR host, make sure to
> use the IP address of the interface that is in the same network of the PC.

Then, in the PC, run:
```
blocksat-rx-upper -i [Server IP] -p [Server Port]
```
where `[Server IP]` and `[Server Port]` are the ones that were used for the
`blocksat-rx-lower` application (i.e. the TCP server address/port).

**NOTE**:
> 1. The upper Rx behaves as client to the TCP server opened in the lower Rx.
> 2. The receive data flow streamed from the SDR host to the PC requires around
> 10 to 12 Mbps.

**Example:**

SDR host:
```
blocksat-rx-lower -f 1276150000 -i 10.0.0.1 -p 5201
```

PC:
```
blocksat-rx-upper -i 10.0.0.1 -p 5201
```

**GUI Mode:**

There are also Rx Lower and Rx Upper applications featuring a real-time GUI for
debugging and monitoring. These are named with `-gui` suffix. Following the
above example, the GUI applications would be launched similarly by:

SDR host:
```
blocksat-rx-lower-gui -f 1276150000 -i 10.0.0.1 -p 5201
```

PC:
```
blocksat-rx-upper-gui -i 10.0.0.1 -p 5201
```

# Run Bitcoin FIBRE

In case you don't have Bitcoin FIBRE installed, do so before proceeding. Make
sure to use [the master
branch](https://github.com/bitcoinfibre/bitcoinfibre/tree/master), which is the
one currently being used by the Blockstream Satellite transmitter.

For more information about Bitcoin FIBRE, refer to:

>Bitcoin FIBRE: http://bitcoinfibre.org

Note that the Blockstream Satellite receiver feeds received data into an output
named pipe that is supposed to be read by the Bitcoin FIBRE application. Hence,
you need to point FIBRE to the named pipe file accordingly. You can start
`bitcoind` with the following parameters:

```
./bitcoind -fecreaddevice=/tmp/blocksat/bitcoinfibre
```

> **NOTE 1:** The Blockstream Satellite receiver will create the
> `/tmp/blocksat/bitcoinfibre` file.

> **NOTE 2:** Bitcoin Fibre uses the same `bitcoin.conf` configuration file as
> Bitcoin Core. Configure as needed.

# Satellite API

Example Python applications for interaction with the Satellite API are available
in the `api/examples` directory. Please refer to the [documentation
there](api/examples/).

For more information regarding the Satellite API, please visit
[blockstream.com/satellite-api](https://blockstream.com/satellite-api/) or the
documentation in the [`api` directory](api/).

# Frequent issues and questions

### Build and Installation

1. No binary package available for GNU Radio 3.7.10 or later

    If a package is not available for 3.7.10+, we recommend either looking for a
    repository that includes such a version or installing via PyBOMBS. For the
    latter, see the instructions in the
    [PyBOMBS repository](https://github.com/gnuradio/pybombs#quickstart).

2. Error during build: could not find `GnuradioConfig.cmake` or
   `gnuradio-config.cmake`.

    The complete error is *Could not find a package configuration file provided
    by "Gnuradio" with any of the following names: `GnuradioConfig.cmake,
    gnuradio-config.cmake`*.

    These tools are needed in order to build the modules that are used by the
    receiver (at `satellite/gr-blocksat/`). The role of these scripts is
    thoroughly described in the
    [GNU Radio wiki](https://wiki.gnuradio.org/index.php/OutOfTreeModulesConfig)
    . As explained there, these files are found in
    `$prefix/lib/cmake/gnuradio`, where `$prefix` is the path where GNU Radio is
    installed (e.g. `/usr/local`). If not sure about your own prefix, run:

    ```
    gnuradio-config-info --prefix
    ```

    Then, check whether `GnuradioConfig.cmake` or `gnuradio-config.cmake` is
    available there in the `lib/cmake/gnuradio` folder. If not, it is likely
    that you need to install a separate GNU Radio development package. These are
    named `gnuradio-devel` or `gnuradio-dev`, depending on distro. For example,
    on Fedora, use:

   ```
   sudo dnf install gnuradio-devel
   ```

3. `Block key "rtlsdr_source" not found`

    This can occur in case the `gr-osmosdr` package is not installed, so you
    should double check this first.

    Also, it can happen in case you have multiple GNU Radio installations, with
    conflicting `grc.conf` files. To verify whether this is the case, first
    check if "rtlsdr_source" is indeed missing. Search for `rtlsdr_source.xml`:

    ```
    sudo find / -name *rtlsdr_source.xml
    ```

    If GNU Radio is installed in prefix `/usr/local`, you would see it there:
    ```
    /usr/local/share/gnuradio/grc/blocks/rtlsdr_source.xml
    ```

    Now, check the paths for GNU Radio blocks in each of your `grc.conf`
    files. In particular, check if the above `rtlsdr_source` path is
    included. You can use:

    ```
    sudo find / -name grc.conf -exec \
        echo -e "\nBlock paths at {}:\n" \;\
        -exec grep "blocks_path" {} \;
    ```

    If `rtlsdr_source.xml` exists and a `grc.conf` points to its path, ensure
    that your GNU Radio Companion instance is loading this `grc.conf`.

4. Error during build *No rule to make target `swig/framers_swig.py`*:

    The complete error message is: `No rule to make target
    'swig/framers_swig.py', needed by 'swig/framers_swig.pyc'. Stop`.
    This refers to the `framers_swig.pyc` file, which is built and
    installed by `make framers; make install framers`. If you are
    seeing this error and you can confirm that the referred file
    exists within your Python `site-packages` or `dist-packages`
    folder (depending on distro), try building the Rx applications
    using parallel recipe execution, that is, using for example:

    ```
    make -j4
    ```

5. "CppUnit" required to compile blocksat

    Install the development CppUnit library. For example, on CentOS,
    run:

    ```
    sudo yum install cppunit-devel
    ```

6. <a name="display_server"></a> Error `‘list’ object has no attribute ‘get’` on headless CentOS build.

    The build of the Rx applications (launched by `make`) relies on
    the GNU Radio Companion Compiler ("grcc") tool, which in turn
    requires a display server. To overcome this on a headless
    environment, you can build using X virtual framebuffer (Xvfb).

    On CentOS, you can install Xvfb using:
    ```
    sudo yum install xorg-x11-server-Xvfba
    ```

    Then, run "make" from inside a virtual window server using:
    ```
    xvfb-run make
    ```

    Furthermore, note that, in a headless environment, it is possible
    that your GNU Radio installation does not include
    [QT GUI](https://www.gnuradio.org/doc/doxygen/page_qtgui.html). You
    can double check that by launching an interactive Python shell and
    trying to import QT GUI:
    ```
    from gnuradio import qtgui
    ```

    If the above does not work, meaning you don't have QT GUI
    installed, the above build using `make` is still prone to
    failure. This is because the GUI-based Rx applications rely on QT
    GUI and the "grcc" tool attempts to find the GUI blocks during
    build. However, note that you can still build solely the non-GUI
    Rx applications. You can do so using:
    ```
    xvfb-run make GUI=0
    ```

7. Unable to locate gnuradio via `apt-get`

    When trying to install `gnuradio` in Ubuntu via `apt-get`, you see:

    ```
    $ sudo apt-get install gnuradio
    Reading package lists... Done
    Building dependency tree
    Reading state information... Done
    E: Unable to locate package gnuradio
    ```

    This is likely because "Universe" Ubuntu repositories are disabled. Proceed
    with the following steps:

    1. Open "System Settings", then "Software & Updates".
    2. Enable downloads from "Community-maintained free and open-source software (universe)".
    3. Close and reload.

### Receiver Execution

1. Permission to access the RTL-SDR dongle

    When running the receiver, your user needs to have permission to access the
    RTL-SDR. Try running `rtl_test` and check if it works. If it does not, but
    `sudo rtl_test` does work, you should configure your udev rules for your
    RTL-SDR device, see [the list of rules in the RTL-SDR repository](
    https://github.com/osmocom/rtl-sdr/blob/master/rtl-sdr.rules). If after that
    it still does not work for your user, you can try adding your user to the
    `rtlsdr` group. That is:

    ```
    usermod -a -G rtlsdr your_user`
    ```

2. <a name="import_error"></a>ImportError: No module named xxx (for example
   "ImportError: No module named framers")

   Make sure that the Blockstream Satellite receiver Python modules can be found
   in your system. Assuming 64-bit systems, the default path will either be
   `/usr/local/lib64/python2.7/site-packages` on RedHat/Fedora or
   `/usr/local/lib/python2.7/dist-packages` on Ubuntu. Double check by looking
   into one of these directories and searching for `framers` and `blocksat`
   folders.

   In case you can't find these folders, you can manually discover where the
   modules are located. For example, by running:

   ```
   sudo find / -name *framers_swig.py*
   ```

   If, for instance, you verify that the modules are indeed located at
   `/usr/local/lib64/python2.7/site-packages/`, then Python must be able to find
   modules in this path. You can check the directories on your Python path
   (including default paths) by running:

   ```
   python -c "import sys; print '\n'.join(sys.path)"
   ```

   In case the directory of interest is not included in the list by default, you
   can add it using the `PYTHONPATH` environmental variable. This variable holds
   a colon-separated list of directories. In the given example, you would add
   the directory by executing:

   ```
   export PYTHONPATH=/usr/local/lib64/python2.7/site-packages:$PYTHONPATH
   ```

3. <a name="seg_fault"></a>Segmentation fault

    If when running the receiver the program exits due to `segmentation fault`,
    you can check whether this is related to the Blockstream Satellite GNU Radio
    out-of-tree (OOT) modules. By OOT modules, we mean the `framers` and
    `blocksat` modules, the former within the `gr-framers` folder and the latter
    within the `gr-blocksat` folder of the root folder in this project. In the
    sequel, we will take the `blocksat` module as reference in the examples, but
    the same procedure applies to the `framers` module.

    Before starting to debug, ensure that `ldconfig` is (or was) executed after
    module installation. This step is automatically executed when running `sudo
    make install-blocksat` or `sudo make install-framers`. Hence, it can be
    skipped in case you installed the modules using the instructed "make
    install" commands (check the install logs).

    Next, you should verify that the "blocksat" (or "framers") module can be
    successfully imported in Python. To do so, run:

    ```
    python2.7 -c "import blocksat"
    ```

    If nothing is printed, it means that the module can indeed be imported. The
    segmentation fault is likely not related to this module, so try the same on
    the other module ("framers"). In contrast, if you see segmentation fault, we
    advise to debug shared libraries.

    There are two things to verify regarding shared libraries: 1) that they can
    be located and 2) that they can be correctly loaded. To double check that
    the *blocksat* shared libraries can be found, you can inspect the `ldd`
    output on the swig-generated shared library files. For example, assuming
    that your library path is at `/usr/local/lib/python2.7/dist-packages`
    (e.g. on Ubuntu), you can run:

    ```
    ldd /usr/local/lib/python2.7/dist-packages/blocksat/_blocksat_swig.so  | grep blocksat
    ```

    If your library is instead at `/usr/local/lib64/python2.7/site-packages`
    (e.g. on Fedora), run:

    ```
    ldd /usr/local/lib64/python2.7/site-packages/blocksat/_blocksat_swig.so | grep blocksat
    ```

    The above command should point to the shared library `.so` file. If,
    instead, you see "not found", double check that the location of the module's
    library is indeed being searched by the Linux program loader. First, check
    the directories listed or included in `/etc/ld.so.conf`. If the directory of
    interest is not in this list, you can include it by using the
    `LD_LIBRARY_PATH` environmental variable. This variable is a colon-separated
    set of directories, so that, for example, to add the path `/usr/local/lib`
    you can run:

    ```
    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
    ```

    When the above `ldd` command already points to the shared library file, but
    the `import blocksat` Python command still fails, then it is likely that
    the problem is in the library itself. This can be inspected by looking at
    the library loading logs. To do so, set the `LD_DEBUG` environmental
    variable to `libs` and then attempt to import the module in Python. For
    example, for the `blocksat` module, run:

    ```
    LD_DEBUG=libs python -c "import blocksat" 2>&1 | grep "blocksat"
    ```

    Subsequently, check the occurrences of "blocksat" in the logs and check
    whether they are error-free. If not, then there is probably a problem in the
    source code. In this case, please feel free to raise an issue or contact us
    directly.

