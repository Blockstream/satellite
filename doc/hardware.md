# Hardware Guide

This page explains the hardware components required to assemble a Blockstream
Satellite receiver setup.

There are three alternatives to collect the required hardware. The first and
quickest option is to purchase a ready-to-use [Satellite
Kit](#satellite-kits). Alternatively, you can buy the [Satellite Kit
Components](#satellite-kit-components) on your own. Lastly, you can opt for a
completely DIY setup, where you pick a combination of compatible parts on your
own. To do so, you will need to understand the [hardware
requirements](#diy-hardware-requirements). This page covers the three
approaches.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Hardware Guide](#hardware-guide)
    - [Satellite Kits](#satellite-kits)
        - [Satellite Kit Comparison](#satellite-kit-comparison)
    - [Satellite Kit Components](#satellite-kit-components)
        - [Blockstream Satellite Basic Kit](#blockstream-satellite-basic-kit)
        - [Blockstream Satellite Pro Kit](#blockstream-satellite-pro-kit)
        - [Blockstream Satellite Base Station](#blockstream-satellite-base-station)
    - [DIY Hardware Requirements](#diy-hardware-requirements)
        - [Supported Receiver Options](#supported-receiver-options)
        - [Common Required Components](#common-required-components)
            - [Satellite Antenna](#satellite-antenna)
            - [LNB](#lnb)
            - [LNB Mounting Bracket](#lnb-mounting-bracket)
            - [Coaxial Cables](#coaxial-cables)
        - [Setup-Specific Components](#setup-specific-components)
            - [Software-defined Radio (SDR) Setup](#software-defined-radio-sdr-setup)
            - [Linux USB Receiver Setup](#linux-usb-receiver-setup)
            - [Standalone Receiver Setup](#standalone-receiver-setup)
            - [Sat-IP Receiver Setup](#sat-ip-receiver-setup)
    - [Further Notes](#further-notes)
        - [Universal LNB:](#universal-lnb)
        - [LNB vs. LNBF:](#lnb-vs-lnbf)

<!-- markdown-toc end -->


## Satellite Kits

As mentioned earlier, the quickest alternative to gather the required parts for
a Blockstream Satellite setup is by purchasing a satellite kit. Check the kits
available on the [Blockstream
Store](https://store.blockstream.com/product-category/satellite_kits/).

There are two main *satellite kits*:

1. [Pro Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/) (Standalone Receiver).
2. [Satellite Base Station](https://store.blockstream.com/product/blockstream-satellite-base-station/) (Sat-IP Receiver).

The Base Station is our go-to receiver choice. Its minimalist design, simplified
setup, and high performance will fit most Bitcoin users' needs.

The Blockstream Satellite Pro Kit is available for:

- Users in some areas of the Asia-Pacific region covered only by the Telstar 18V
  C band satellite (and not covered by the Telstar 18V Ku band beam).
- Users who want to use their own dish antennas.
- Users who wish to use larger dish antennas.

Note the Satellite Base Station is not compatible with the C band. That is, it
does not work with the Telstar 18V C band satellite covering the Asia-Pacific
region. If you are in a C band location, you will need a Pro Kit or a DIY
receiver option.

If you have decided to go with a satellite kit and selected the Pro Kit
receiver, note you still need a satellite antenna and coaxial cables (not
included). Please refer to the requirements for [antennas](#satellite-antenna)
and [coaxial cables](#coaxial-cables). After that, you can proceed to the next
section, which explains the [receiver setup](receiver.md).

If you selected the Blockstream Satellite Base Station (again, compatible with
Ku band only), you are all set. Proceed to the [next section](receiver.md).

Otherwise, you can proceed to assemble a satellite receiver on your own. Aside
from the Pro Kit and Satellite Base Station options, you can gather the required
components for the Basic Kit (formerly sold on [Blockstream
Store](https://store.blockstream.com/product/blockstream-satellite-basic-kit/))
based on a Linux USB Receiver. Refer to the list of [Basic Kit
components](#blockstream-satellite-basic-kit). Alternatively, you can find
detailed information in this guide to put together an affordable SDR receiver
with just under $100.

### Satellite Kit Comparison

The following table summarizes the different features offered by each of the
satellite receiver options:

|                                       | SDR                | Basic Kit          | [Pro Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/) | [Base Station](https://store.blockstream.com/product/blockstream-satellite-base-station/) |
|---------------------------------------|:------------------:|:------------------:|:------------------:|:------------------:|
| Blockstream Kit Available             |                    | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| USB Interface                         | :heavy_check_mark: | :heavy_check_mark: |                    |                    |
| Ethernet Interface                    |                    |                    | :heavy_check_mark: | :heavy_check_mark: |
| Requires LNB Power Supply             | :heavy_check_mark: |                    |                    |                    |
| Support for Universal LNB<sup>1</sup> |                    | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| Dual-Satellite Capable<sup>2</sup>    |                    |                    | :heavy_check_mark: |                    |
| CPU Utilization                       | High               | Low                | None               | None               |
| Multiple Host Connections<sup>3</sup> |                    |                    | :heavy_check_mark: | :heavy_check_mark: |
| Optional Rack Mountable               |                    |                    | :heavy_check_mark: |                    |
| Compatible with C-band                | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    |

<sup>1</sup> Support means that the interface provides a 22 kHz signal for
switching the Universal LNB between Ku low and Ku high bands. This feature is
required to use Universal LNBs when receiving from the Galaxy 18 or Eutelsat 113
satellites.

<sup>2</sup> The device can receive from two satellites simultaneously in areas
with overlapping coverage. This feature enables greater redundancy, higher
bitrate, and faster blockchain sync times.

<sup>3</sup> The receiver can feed the data stream received over satellite to
multiple hosts simultaneously over the local network.

## Satellite Kit Components

Instead of purchasing a satellite kit, you can buy the individual components on
your own. The elements of each kit are summarized in this section.

If you have decided to buy the satellite kit components on your own, you can
proceed to the [receiver setup](receiver.md) once you collect them. Otherwise,
if you would still like to learn more about hardware requirements or search for
alternative compatible parts, including the affordable SDR receiver option,
refer to the [DIY hardware requirements](#diy-hardware-requirements).

### Blockstream Satellite Basic Kit

This kit is no longer available on the Blockstream Store. It has been replaced
by the [Satellite Base Station](#blockstream-satellite-base-station).

Components:

- TBS 5927 DVB-S2 Tuner.
- GEOSATpro UL1PLL Universal Ku Band PLL LNB.
- Titanium C1-PLL C Band PLL LNB.
- Titanium CS1 Conical Scalar Kit.
- Ku Band LNB mounting bracket.
- C Band LNB mounting bracket.
- 32 cm flat, bendable flat coaxial TV extension cable used to pass through
  window and door frames.

> Note: the kit includes two LNBs so that it works in C and Ku band. You can
> purchase only the LNB that you need in your location. If you are in a C band
> location (Telstar 18V C Asia-Pacific region), you will need the Titanium
> C1-PLL LNB or similar, as well as the optional CS1 Conical Scalar Kit or
> similar if using an offset dish. Otherwise (in all other regions), you can
> purchase the GEOSATpro UL1PLL Universal LNB or similar.

The above list does not include the antenna nor the required coaxial cables.
Please refer to the requirements for [antennas](#satellite-antenna) and [coaxial
cables](#coaxial-cables).

### Blockstream Satellite Pro Kit

Available on [Blockstream Store](https://store.blockstream.com/product/blockstream-satellite-pro-kit/).

Components:

- Novra S400 Professional DVB-S2 Receiver.
- GEOSATpro UL1PLL Universal Ku Band PLL LNB.
- Titanium C1-PLL C Band PLL LNB.
- Titanium CS1 Conical Scalar Kit.
- Ku Band LNB mounting bracket.
- C Band LNB mounting bracket.
- 32 cm flat, bendable flat coaxial TV extension cable used to pass through
  window and door frames.

> Note: the kit includes two LNBs so that it works in C and Ku band. You can
> purchase only the LNB that you need in your location. If you are in a C band
> location (Telstar 18V C Asia-Pacific region), you will need the Titanium
> C1-PLL LNB or similar, as well as the optional CS1 Conical Scalar Kit or
> similar if using an offset dish. Otherwise (in all other regions), you can
> purchase the GEOSATpro UL1PLL Universal LNB or similar.

Note the kit does not include the antenna nor the required coaxial cables.
Please refer to the requirements for [antennas](#satellite-antenna) and [coaxial
cables](#coaxial-cables).

### Blockstream Satellite Base Station

Available on [Blockstream
Store](https://store.blockstream.com/product/blockstream-satellite-base-station/).

Components:

- Selfsat>IP22 all-in-one Sat-IP flat-panel antenna.
- Power over Ethernet injector.
- Ethernet Cat5e cable.

## DIY Hardware Requirements

This section explains the requirements to assemble a satellite receiver setup
entirely on your own. Nevertheless, note this process can be time-consuming. If
you prefer a faster solution, check out the available [Satellite
Kits](#satellite-kits).

### Supported Receiver Options

The receiver is the device or software application that processes the incoming
satellite signal and decodes the data stream from it. There are four supported
types of receivers. For each of them, specific hardware components are required.

The receiver options are summarized below:

- **Software-defined Radio (SDR)**: this receiver is entirely implemented in
  software. You will need an SDR interface connected to your PC (typically via
  USB). The SDR interface collects and feeds signal samples to the receiver
  application/software running on your PC. The application, in turn, decodes and
  outputs the data stream to be fed into [Bitcoin
  Satellite](https://github.com/Blockstream/bitcoinsatellite). This is the most
  affordable option among the three, as it works with inexpensive RTL-SDR USB
  dongles. However, it is also the option expected to present the most limited
  performance and reliability among the three. Moreover, this option is
  CPU-intensive since the receiver application will run in the CPU.

- **Linux USB Receiver**: in this setup, the demodulation is entirely carried
  out in hardware, in the external receiver device connected to your host via
  USB. Hence, unlike the SDR receiver, the Linux USB receiver is not
  CPU-intensive. With this option, you will need to install specific drivers and
  Linux DVB-S2 apps on the host to configure the external receiver and get the
  data from it. Overall, this option is expected to perform exceptionally and
  with negligible CPU usage. On the other hand, it can require a time-consuming
  initial setup due to the driver installation. You can try the [driver
  installation](tbs.md#tbs-5927-drivers) on your intended host before committing
  to this receiver option.

- **Standalone Receiver**: this is also a hardware-based setup, with the
  difference that it is entirely independent of the host PC. It connects to the
  PC through the network and can potentially feed multiple PCs
  concurrently. This is also expected to be a great option in terms of
  performance. Besides, this is the only option capable of [dual-satellite
  reception](dual-satellite.md) using a single receiver device.

- **Sat-IP Receiver**: this is another hardware-based and standalone receiver
  option. The difference is that it is based on an all-in-one antenna with a
  built-in DVB-S2 receiver and integrated LNB (see the [Satellite Base
  Station](https://store.blockstream.com/product/blockstream-satellite-base-station/)). It
  is referred to as a Sat-IP receiver because it runs a [Sat-IP
  server](https://en.wikipedia.org/wiki/Sat-IP), to which your host will connect
  as a client. Overall, this option offers the easiest configuration and the
  most minimalist setup, given that it requires a single component (the
  all-in-one antenna). However, note it does not work with the Telstar 18V C
  band satellite covering the Asia-Pacific region.

For further insights, refer to the [satellite receiver
comparison](#satellite-kit-comparison) table presented earlier.

Once you pick your preferred receiver option, you should gather all of its
required components. The following section explains the [common
elements](#common-required-components) required for all types of
receivers. Then, the subsequent section covers the [specific
parts](#setup-specific-components) for each receiver option.

### Common Required Components

In addition to the DVB-S2 receiver, you will need an antenna and a low-noise
block downconverter (LNB) to receive the satellite signal. Furthermore, you will
need cables to connect them to each other.

The antenna and LNB components are required in all setups other than the
all-in-one [Satellite Base
Station](https://store.blockstream.com/product/blockstream-satellite-base-station/). The
latter, in contrast, consists of an antenna with an integrated receiver and LNB,
all in one device.

Refer to the following requirements to select the appropriate antenna, LNB, and
cables.

#### Satellite Antenna

The most widely available antenna option is the regular satellite TV dish with a
conventional parabolic reflector.

Blockstream Satellite is designed to work with small dishes. In [Ku
band](frequency.md#signal-bands), it is expected to work with antennas of only
45 cm in diameter, while in the C band, it is designed to work with 60 cm or
higher. However, a larger antenna is always better. When possible, we recommend
installing an antenna larger than the referred minimum if one is readily
available. Antennas of 60 cm, 90 cm, and 1.2 m are readily available.

Other than size, the only additional requirement is that the antenna works with
the frequency band that suits your coverage region. You can always use antennas
designed for higher frequencies. For example, an antenna designed for Ka band
will work for Ku and C bands, as it is designed for higher frequencies than
those used by Blockstream Satellite. However, a C band antenna will not work in
Ku band, as it is designed for lower frequencies. For further information
regarding frequency bands, please refer to [the frequency guide](frequency.md).

An alternative to conventional satellite dishes is a flat panel antenna, which
is generally more compact and stylish. A recommended flat panel model is the
Selfsat H50D, which was previously [available at our
store](https://store.blockstream.com/product/flat-panel-antenna/) before being
replaced by the all-in-one [Satellite Base
Station](https://store.blockstream.com/product/blockstream-satellite-base-station/).
The Selfsat H50D includes the LNB internally, and so there is no need to
purchase an LNB (nor an LNB bracket) when using it. However, note that this
model has limited compatibility. It is an excellent option for:

1. **Linux USB** and **Standalone Receivers** in any Ku band region.
2. **SDR** receivers in Ku low band regions (Telstar 11N Africa, Telstar 11N
Europe, and Telstar 18V Ku).

In contrast, the Selfsat H50D flat panel is **not** compatible with receivers
(of any type) in the Telstar 18V C (C Band) region. It only works in [Ku
band](frequency.md#signal-bands).

The flat panel requires an extra 22 kHz generator to work with **SDR** receivers
in Ku high band regions (Galaxy 18 and Eutelsat 113). This antenna includes a
built-in [Universal LNB](#universal-lnb), which, as explained [later](#lnb),
requires a 22 kHz tone generated by the receiver specifically for the reception
in Ku high band (i.e., the band used by G18 and E113). Refer to further
information and a solution for 22 kHz generation on an SDR setup in [the
Universal LNB section](#universal-lnb).

#### LNB

When choosing a low-noise block downconverter (LNB), the most relevant
parameters are the following:

- Frequency range
- Polarization
- LO Stability

**In a nutshell,** you are advised to use a PLL LNB with linear polarization and
LO stability within `+- 250 kHz` or less. Also, the LNB should be suitable for
the frequency of the signal covering your location.

Regarding **frequency range**, you must verify that the input frequency range of
the LNB encompasses the frequency of the Blockstream Satellite signal in your
coverage area. For example, if you are located in North America and covered by
the Eutelsat 113 satellite, the downlink frequency of interest is 12066.9
GHz. In this case, an LNB that operates from 11.7 GHz to 12.2 GHz would work. In
contrast, an LNB that operates from 10.7 GHz to 11.7 GHz would **not** work. You
can check the signal frequencies of each region in [the frequency
guide](frequency.md#signal-frequencies).

Regarding **polarization**, an LNB with **Linear Polarization** is
required. While most Ku band LNBs are linearly polarized, some popular satellite
TV services use circular polarization. A circularly polarized LNB will **not**
work with Blockstream Satellite.

If an LNB is described to feature horizontal or vertical polarization, then it
is linear. In contrast, if an LNB is described as Right-Hand or Left-Hand
Circular Polarized (RHCP or LHCP), then it is circular and will **not** work
with Blockstream Satellite.

Regarding **LO Stability**, a stability specification of `<= +/- 250 kHz` is
preferable for better performance. Most LNBs will have a local oscillator (LO)
stability parameter referred to as “LO stability,” or metrics such as "LO
accuracy" and "LO drift." These are usually specified in +/- XX Hz, kHz, or
MHz. An LNB that relies on a phase-locked loop (PLL) frequency reference is
typically more accurate and stable. Hence, we advise looking for a PLL LNB
instead of a traditional dielectric oscillator (DRO) LNB.

If you would like (or you need) to use a less stable LNB, it can also be
used. The disadvantage is that it will likely degrade your setup's reliability
and performance (for example, increase the bit error rate).

A widely available LNB option is the so-called **Universal Ku band
LNB**. However, please note that if you are using an SDR-based setup, a
**Universal LNB** may pose extra difficulties. Please refer to the [explanation
regarding Universal LNBs](#universal-lnb). This limitation **does not** apply
when using the Linux USB or Standalone receiver options.

Besides, another parameter of interest is the so-called F/D ratio. This
parameter refers to the ratio between the parabolic reflector's focal length and
its diameter. As such, it is a parameter of the dish, not the LNB. Nevertheless,
the LNB should be designed for an F/D ratio compatible with the reflector.

For example, an [offset dish](https://en.wikipedia.org/wiki/Offset_dish_antenna)
(the most common dish type for Ku band) typically has an F/D ratio from 0.5 to
0.7. In contrast, a regular "front-fed" parabolic dish typically has an F/D in
the 0.3 to 0.4 range. In any case, check the F/D specifications of your dish and
make sure to use a compatible LNB. If necessary, attach a flat or conical scalar
ring to change the F/D characteristics of the LNB.

Lastly, to avoid confusion, please note that *LNBF* and *LNB* often refer to the
same thing. You can find further information [later in this
guide](#lnb-vs.-lnbf).

#### LNB Mounting Bracket

The antenna dish likely comes with a mounting bracket, but you will need one
designed to accept a generic LNB. Also, it is good to have a flexible bracket to
facilitate the LNB rotation and control of its polarization angle. Although all
mounting brackets do allow rotation, some can be limited in the rotation range.

Such mounting brackets attach to the antenna's feed arm and have a circular ring
that will accept a generic LNB.

#### Coaxial Cables

You will need a coaxial cable to connect the LNB to the receiver or, in the case
of the SDR-based setup, to connect the LNB to the power supply. The most popular
and recommended type of coaxial cable is the RG6 cable.

### Setup-Specific Components

This section summarizes the additional components required for each type of
setup, according to the receiver choice.

#### Software-defined Radio (SDR) Setup

| Component        | Requirement                            |
|------------------|----------------------------------------|
| SDR interface    | RTL-SDR dongle model RTL2832U w/ TCXO  |
| LNB Power Supply | SWM Power Supply                       |
| SMA Cable        | Male to Male                           |
| SMA to F adapter | SMA Female, F Male                     |

The supported **SDR interface** is the RTL-SDR, which is a low-cost USB
dongle. More specifically, an RTL-SDR of model RTL2832U.

There are two specifications to observe when purchasing an RTL-SDR:

1. Oscillator
2. Tuner

We recommend using an RTL-SDR with a temperature-controlled crystal oscillator
(TCXO), as the TCXO has better frequency stability than a conventional crystal
oscillator (XO). A few models in the market feature a TCXO with frequency
accuracy within 0.5 ppm to 1.0 ppm, which are good choices.

Regarding the tuner, the choice depends on the satellite covering your
location. The two recommended tuners are the R820T2 and the E4000. The table
below summarizes which tuner to pick for each satellite:

| Satellite          | RTL-SDR Tuner |
|--------------------|---------------|
| Galaxy 18          | R820T2        |
| Eutelsat 113       | R820T2        |
| Telstar 11N Africa | E4000         |
| Telstar 11N Europe | E4000         |
| Telstar 18V Ku     | E4000         |
| Telstar 18V C      | R820T2        |

This tuner recommendation has to do with the L-band frequencies expected in each
region, as summarized in the [frequency
guide](frequency.md#l-band-frequencies). The E4000 tuner is recommended for the
areas where the L-band frequency is close to the maximum tuning range of the
R820T2 tuner (1766 MHz).

Hence, for example, if you are going to receive from Galaxy 18, you should get
an RTL-SDR RTL2832U with tuner R820T2 and TCXO. In contrast, if you are going to
receive from Telstar 11N Africa, you should get an RTL-SDR RTL2832U with tuner
E4000 and TCXO. Note that the RTL-SDR models featuring the E4000 tuner are
marketed as **extended tuning range RTL-SDR** or **XTR RTL-SDR**.

The next component of the SDR receiver setup is the **LNB Power Supply** (or
Power Inserter). This component supplies a DC voltage to the LNB via the coaxial
cable, typically of 13 VDC or 18 VDC. On a non-SDR setup, the receiver itself
can provide power to the LNB, so there is no need for an external power
supply. In contrast, this is not possible with an SDR-based setup using the SDR
interface alone. Hence, an external supply is required.

The type of power supply that is easy to find in the market is named "Single
Wire Multiswitch" (SWM) power supply. You can look for an SWM power inserter and
use it as illustrated below. The **non-powered** port of an SWM power supply is
labeled "Signal to IRD," which means signal to integrated receiver/decoder. This
is the port that should be connected to the SDR interface. The **powered** port,
in turn, is labeled "Signal to SWM." This is the port that should be connected
to the LNB.

![SDR receiver connections](img/sdr_connections.png?raw=true "SDR receiver
connections")

**IMPORTANT**: Do **NOT** connect the powered port of the LNB power supply to
the SDR interface. Permanent damage may occur to your SDR and/or your computer.

Also, please check the power/voltage requirement of your LNB and ensure that
your power supply matches. It should be noted that some LNBs known as
**dual-polarization LNBs** accept two DC voltage levels. Such LNBs use the
supplied voltage to switch between vertical and horizontal polarization. A
supplied DC voltage of +18 VDC sets the LNB to horizontal polarization, whereas
+13 VDC sets the LNB to vertical polarization. Please keep this in mind when
rotating the LNB for a specific polarization angle during the antenna pointing
stage.

**Further notes**:

- **Alternative SDR interfaces**: the RTL-SDR is the supported SDR interface and
the most popular among Blockstream Satellite users. Nevertheless, other SDR
boards/interfaces can be used with minor tweaks, such as USRPs. The SDR
interface must support L-band frequencies within the 1 GHz to 2 GHz range and
sampling rates of 2 Msps (mega samples per second) or higher.

- **Connectors**: not every RTL-SDR has the same interface connector. Some use
the SMA connector, while some others use MCX. Be sure to order the correct cable
and adapters to make the necessary connections. In the above table, we assume
the RTL-SDR has SMA female connector, while the power supply has two F female
connectors. In this case, you need an SMA male-to-male cable and an SMA female
to F male adapter to connect the RTL-SDR to the **non-powered** port (“Signal to
IRD”) of the SWM power supply.

#### Linux USB Receiver Setup

The only specific component in this setup is the external USB-based DVB-S2
receiver. The supported receiver is the [TBS5927 Professional DVB-S2 TV Tuner
USB](https://www.tbsdtv.com/products/tbs5927-dvb-s2-tv-tuner-usb.html), which
connects to the Linux PC via a USB2.0 connection. The LNB, in turn, connects
directly to the *LNB IN* interface of the TBS5927. The TBS5927 package includes
both the USB cable and a power supply for the receiver.

![Linux USB receiver connections](img/usb_connections.png?raw=true "Linux USB
receiver connections")

> NOTE: although the TBS5927 receiver offers Windows support, we currently do
> not support Windows as an operating system for a Blockstream Satellite setup.

#### Standalone Receiver Setup

In this setup, a standalone DVB-S2 receiver connects to the host PC (or to the
network) through an Ethernet cable. The standalone receiver that is currently
supported is the [Novra S400 PRO DVB satellite
Receiver](https://novra.com/product/s400-pro-dvb-satellite-receiver). Other than
this receiver, you only need an Ethernet Cable.

![Standalone receiver connections](img/standalone_connections.png?raw=true
"Standalone receiver connections")

#### Sat-IP Receiver Setup

The Sat-IP receiver that is currently supported is the all-in-one Selfsat>IP22
Sat-IP flat-panel antenna. It requires an Ethernet cable (Cat5e or superior) to
connect to a switch/router or directly to your host. Furthermore, it requires
Power over Ethernet (PoE). Hence, you will need a PoE injector if the
switch/router or network adapter connecting to the Sat-IP antenna does not
support PoE.

## Further Notes

### Universal LNB:

A Universal LNB, also known as Universal Ku band LNB, is an LNB that supports
both [Ku low and Ku high bands](frequency.md#signal-bands). With such an LNB,
the receiver becomes responsible for switching the Ku sub-band as needed. More
specifically, the receiver sends a 22 kHz tone to the LNB when tuning to a Ku
high band carrier. Otherwise, when tuning to a Ku low band carrier, the receiver
simply does not send any tone. The absence of a 22 kHz tone configures the LNB
to its default sub-band, the Ku low sub-band.

An important limitation applies to the SDR setup when using a Universal LNB.
Note the SDR setup described in this guide is receiver-only. Hence, it cannot
generate a 22 kHz tone to configure the Universal LNB. Consequently, a Universal
LNB connected to an SDR receiver operates in Ku low band only. Thus, we
recommend using this type of LNB only within [Ku low band
regions](frequency.md#signal-frequencies), i.e., within the areas covered by
Telstar 11N Africa, Telstar 11N Europe, or Telstar 18V Ku.

Meanwhile, in contrast to an SDR setup, both Linux USB and Standalone [receiver
options](#supported-receiver-options) support the generation of 22 kHz. Hence,
it is perfectly acceptable to use a Universal LNB in any Ku band region when
using one of these receivers.

Besides, there are workarounds to switch the sub-band of a Universal LNB even
with an SDR setup. For instance, you can place a 22 kHz tone generator inline
between the LNB and the power inserter. In this case, the tone generator will
use power from the inserter while delivering the tone directly to the LNB. Such
tone generators can be found in the market as pure generators. Alternatively,
you can get a satellite finder device containing the 22 kHz generation
functionality.

If choosing a satellite finder, it is essential to note that the finder must be
one that can be used inline between the power supply and the LNB. In other
words, it must be one with two connectors, one for signal input (from the LNB)
and the other for output (towards the power inserter). Some finders contain a
single connector, as they are not intended to be used inline. Furthermore, be
aware that most finders do not include a 22 kHz generator. You must pick a
satellite finder that supports the generation of a 22 kHz tone.

### LNB vs. LNBF:

The feedhorn is the horn antenna that attaches to the LNB. It collects the
signals reflected by the satellite dish and feeds them into the LNB towards the
receiver. The acronym LNBF stands for "LNB with feedhorn" and refers to the LNB
that already contains an integrated feedhorn. This is the most typical type of
LNB nowadays. Hence, almost always, the term LNB already refers to an LNBF
implicitly. To avoid confusion, we advise looking for an LNBF.

---

Prev: [Frequency Bands](frequency.md) - Next: [Receiver Setup](receiver.md)
