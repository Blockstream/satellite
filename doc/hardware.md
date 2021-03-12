# Hardware Guide

This page explains all hardware components required for assembling a Blockstream
Satellite receiver setup.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Hardware Guide](#hardware-guide)
    - [Satellite Kits](#satellite-kits)
        - [Blockstream Satellite Basic Kit](#blockstream-satellite-basic-kit)
        - [Blockstream Satellite Pro Kit](#blockstream-satellite-pro-kit)
    - [Satellite Kit Comparison](#satellite-kit-comparison)
- [Hardware Requirements](#hardware-requirements)
    - [Receiver Options](#receiver-options)
    - [Common Components](#common-components)
        - [Satellite Dish](#satellite-dish)
        - [LNB](#lnb)
        - [LNB Mounting Bracket](#lnb-mounting-bracket)
        - [Coaxial Cables](#coaxial-cables)
    - [Setup-Specific Components](#setup-specific-components)
        - [Components for a Software-defined Radio (SDR) Setup](#components-for-a-software-defined-radio-sdr-setup)
        - [Components for a Linux USB Receiver Setup](#components-for-a-linux-usb-receiver-setup)
        - [Components for a Standalone Receiver Setup](#components-for-a-standalone-receiver-setup)
    - [Further Notes](#further-notes)
        - [“Universal” LNB:](#universal-lnb)
        - [LNB vs. LNBF:](#lnb-vs-lnbf)

<!-- markdown-toc end -->


## Satellite Kits

There are three main *satellite kits*:

1. SDR Kit (w/ SDR-based Receiver)
2. [Basic USB Kit](https://store.blockstream.com/product/blockstream-satellite-basic-kit/). (w/ Linux USB Receiver)
3. [Pro Ethernet Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/). (w/ Standalone Receiver)

Kits #2 and #3 are available at the [Blockstream
Store](https://store.blockstream.com/product-category/satellite_kits/), whereas
Kit 1 is DIY.

Users can also purchase the individual components of the kits, which are
detailed next.

### Blockstream Satellite Basic Kit

Available at the [Blockstream Store](https://store.blockstream.com/product/blockstream-satellite-basic-kit/).

Components:

- TBS 5927 DVB-S2 Tuner
- Universal Ku Band PLL LNB
    - Universal 9750/10600 LO.
    - Phase-locked loop design.
    - Single Output Ku LNBF.
    - Frequency: 10.7-12.75 GHz.
    - 0.5 dB Noise Figure.
    - 60 dB conversion gain.
    - +/- 300 kHz Stability.
- Universal C Band PLL LNB
    - Low-band filtering to provide exceptional performance.
    - Frequency: 3.7 GHz - 4.2 GHz range.
    - Phase-locked loop design.
    - 15°K noise figure.
    - 65 dB conversion gain.
    - +/- 50 Khz Stability.
- Ku Band LNB Mounting Bracket
    - Bracket to support the Universal Ku Band PLL LNB.
    - Compatible with any 18" DTV dish, Dishnetwork Dish, Super Dish, and 33",
      36", or 39" FTA Dishes.
    - Has molded in LNB rotation and vertical height adjust scale.
- C Band LNB Scalar ring
    - Provides optimal offset dish illumination.
- C Band LNB Mounting Bracket
    - Universal poly 50 - 68mm feed horn clamp for mounting on many
      brands/models of offset dishes. Options for bottom or side mounting holes
      are provided for attachment to the many varied feed support arm designs.
- 32cm flat coax jumper
    - Flat, bendable flat coaxial TV extension cable used to pass through window
      and door frames.

### Blockstream Satellite Pro Kit

Available at the [Blockstream Store](https://store.blockstream.com/product/blockstream-satellite-pro-kit/).

Components:

- Novra S400 Professional DVB-S2 Receiver
    - Dual-satellite capable.
    - Input Signal Level: -65 dBm to -25 dBm.
    - Receiving Frequency: 950 to 2150 MHz.
    - Connectivity:
        - 2 L-band input connectors (F-type and 75 ohms).
        - 1 Ethernet GbE RJ-45 LAN interface for data output.
        - 1 Ethernet 100Base-T interface for monitor/control.
        - Micro SD Slot.
- Universal Ku Band PLL LNB
    - Universal 9750/10600 LO.
    - Phase-locked loop design.
    - Single Output Ku LNBF.
    - Frequency: 10.7-12.75 GHz.
    - 0.5dB Noise Figure.
    - 60 dB conversion gain.
    - 300 kHz Stability.
- Universal C Band PLL LNB
    - Low-band filtering to provide exceptional performance.
    - Frequency: 3.7 GHz - 4.2 GHz range.
    - Phase-locked loop design.
    - 15°K noise figure.
    - 65 dB conversion gain.
    - +/- 50 khz Stability.
- Ku Band LNB Mounting Bracket
    - Bracket to support the Universal Ku Band LNB.
    - Compatible with any 18" DTV dish, Dishnetwork Dish, Super Dish, and 33",
      36", or 39" FTA Dishes.
    - Has molded in LNB rotation and vertical height adjust scale.
- C Band LNB Scalar ring
    - Provides optimal offset dish illumination.
- C Band LNB Mounting Bracket
    - Universal poly 50 - 68mm feed horn clamp for mounting on many
      brands/models of offset dishes. Options for bottom or side mounting holes
      are provided for attachment to the many varied feed support arm designs.
      -32cm flat coax jumper Flat, bendable flat coaxial TV extension cable used
      to pass through window and door frames.
- 32cm flat coax jumper
    - Flat, bendable flat coaxial TV extension cable used to pass through window
      and door frames.

## Satellite Kit Comparison

The following table summarizes the different features offered by each of them:

|                                       | SDR                | [Basic USB Kit](https://store.blockstream.com/product/blockstream-satellite-basic-kit/)      | [Pro Ethernet Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/)   |
|---------------------------------------|:------------------:|:------------------:|:------------------:|
| Blockstream Kit Available             | DIY                | :heavy_check_mark: | :heavy_check_mark: |
| USB Interface                         | :heavy_check_mark: | :heavy_check_mark: |                    |
| Ethernet Interface                    |                    |                    | :heavy_check_mark: |
| LNB Power Supplied by Interface       |                    | :heavy_check_mark: | :heavy_check_mark: |
| Support for Universal LNB<sup>1</sup> |                    | :heavy_check_mark: | :heavy_check_mark: |
| Dual-Satellite Capable<sup>2</sup>    |                    |                    | :heavy_check_mark: |
| CPU Utilization                       | High               | Low                | None               |
| Multiple Host Connections<sup>3</sup> |                    |                    | :heavy_check_mark: |
| Optional Rack Mountable               |                    |                    | :heavy_check_mark: |
| Compatible with the [Flat Panel](https://store.blockstream.com/product/flat-panel-antenna/) | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |

<sup>1</sup> Support means that the interface provides a 22 kHz signal for
switching the band of a Universal LNB between Ku low and Ku high bands. This
feature is required to use Universal LNBs when receiving from the Galaxy 18 or
Eutelsat 113 satellites.

<sup>2</sup> Ability to receive from two satellites simultaneously in areas with
overlapping coverage from satellites. This feature enables greater redundancy,
higher bitrate, and faster sync times.

<sup>3</sup> The receiver can feed the data stream received over satellite to
multiple hosts at the same time. The receiver decodes multicast-addressed
packets sent over DVB-S2 and relays the multicast packets to multiple hosts
listening to them in the network.

All features and specifications mentioned thus far are thoroughly explained in
the remainder of this page.

# Hardware Requirements

## Receiver Options

The receiver is the device or software application that processes the incoming
satellite signal and decodes the data stream from it. There are three supported
types of receivers. For each of them, specific hardware components are required.

The three receiver options are summarized below:

- **Software-defined Radio (SDR)**: this receiver is entirely implemented in
  software. You will need an SDR interface connected to your PC (typically via
  USB). The SDR interface collects and feeds signal samples to the receiver
  application/software running in your PC, which then decodes and outputs the
  data stream to be fed into [Bitcoin
  Satellite](https://github.com/Blockstream/bitcoinsatellite). This is the most
  affordable option among the three, as it works with inexpensive RTL-SDR USB
  dongles. However, it is also the option that is expected to present the most
  limited performance and reliability among the three. Moreover, this option is
  CPU-intensive since the receiver application will run in the CPU.

- **Linux USB Receiver**: in this setup, the demodulation is entirely carried
  out in hardware, in the external receiver device connected to your host via
  USB. In this option, you will need to install specific drivers and Linux
  DVB-S2 apps that will allow the host to configure the external receiver and
  get the data from it. This option is expected to perform greatly and with a
  negligible CPU usage of the host.

- **Standalone Receiver**: this is also a hardware-based setup, with the
  difference that it is entirely independent of the host PC. It connects to the
  PC through the network and can potentially feed multiple PCs
  concurrently. This is also expected to be a great option in terms of
  performance.

## Common Components

These are the hardware components that are required in all setups, regardless of
the receiver choice.

### Satellite Dish

Blockstream Satellite is designed to work with small antennas. In [Ku
band](frequency.md#signal-bands), it is expected to work with antennas of only
45cm in diameter, while in the C band, it is expected to work with 60cm or
higher. However, a larger antenna is always better. When possible, we recommend
installing an antenna larger than the referred minimum if one is readily
available. Antennas of 60cm, 90cm, and 1.2m are readily available.

An alternative to conventional satellite dishes is a flat panel antenna, which
is generally more compact and stylish. A recommended flat panel model is
[available at our
store](https://store.blockstream.com/product/flat-panel-antenna/). This antenna
includes the LNB internally, and so there is no need to purchase an LNB (nor an
LNB bracket) when using a flat panel. However, note that this model has limited
compatibility. The flat-panel is an excellent option for:

1. **Linux USB** and **Standalone Receivers** in any Ku band region.
2. **SDR** receivers in Ku low band regions (Telstar 11N Africa, Telstar 11N
Europe, and Telstar 18V Ku).

In contrast, the flat-panel is **not** compatible with receivers (of any type)
in the Telstar 18V C (C Band) region. This is because it only works in [Ku
band](frequency.md#signal-bands).

The flat-panel requires an extra 22 kHz generator to work with **SDR** receivers
in Ku high band regions (Galaxy 18 and Eutelsat 113). This antenna includes a
built-in [Universal LNB](#universal-lnb), which, as explained [later](#lnb),
requires a 22 kHz tone generated by the receiver specifically for the reception
in Ku high band (i.e., the band used by G18 and E113). Refer to further
information and a solution for 22 kHz generation on an SDR setup in [the
Universal LNB section](#universal-lnb).

Other than size, the only additional requirement is that the antenna will work
with the frequency band that suits your coverage region. You can always use
antennas designed for higher frequencies. For example, an antenna designed for
Ka band will work for Ku and C bands, as it is designed for higher frequencies
than those used by Blockstream Satellite. However, a C band antenna will not
work in Ku band, as it is designed for lower frequencies. For further
information regarding frequency bands, please refer to [the frequency
guide](frequency.md).

### LNB

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
accuracy" and "LO drift". These are usually specified in +/- XX Hz, kHz, or
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

Lastly, to avoid confusion, please note that *LNBF* and *LNB* often refer to the
same thing. You can find further information [later on this
guide](#lnb-vs-lnbf).

### LNB Mounting Bracket

The antenna dish likely comes with a mounting bracket, but you will need one
designed to accept a generic LNB. Also, it is good to have a flexible bracket to
facilitate the LNB rotation and control of its polarization angle. Although all
mounting brackets do allow rotation, some can be limited in the rotation range.

Such mounting brackets attach to the feed arm of the antenna and have a circular
ring that will accept a generic LNB.

### Coaxial Cables

You will need a coaxial cable to connect the LNB to the receiver or, in the case
of the SDR-based setup, to connect the LNB to the power supply. The most popular
and recommended type of coaxial cable is an RG6.

## Setup-Specific Components

This section summarizes the additional components required for each type of
setup, according to the receiver choice.

### Components for a Software-defined Radio (SDR) Setup

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
oscillator (XO). There are a few models in the market featuring TCXO with
frequency accuracy within 0.5 ppm to 1.0 ppm, which are good choices.

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

The type of power supply that is easy to find in the market is known as "Single
Wire Multiswitch" (SWM) power supply. You can look for an SWM power inserter and
use it as illustrated below. The **non-powered** port of an SWM power supply is
labeled "Signal to IRD," which means signal to integrated receiver/decoder. This
is the port that should be connected to the SDR interface. The **powered** port,
in turn, is labeled "Signal to SWM." This is the port that should be connected
to the LNB.

![SDR Connections](img/sdr_connections.png?raw=true "SDR Connections")

**IMPORTANT**: Do **NOT** connect the powered port of the LNB power supply to
the SDR interface. Permanent damage may occur to your SDR and/or your computer.

Also, please check the power/voltage requirement of your LNB and ensure that
your power supply matches. It should be noted that some LNBs known as
**dual-polarization LNBs** accept two DC voltage levels. Such LNBs use the
supplied voltage to switch between vertical and horizontal polarization. A
supplied DC voltage of +18 VDC sets the LNB to horizontal polarization, whereas
a voltage of +13 VDC sets the LNB to vertical polarization. Please keep this in
mind when rotating the LNB for a specific polarization angle during the antenna
pointing stage.

**Further notes**:

- **Alternative SDR interfaces**: the RTL-SDR is the supported SDR interface and
the most popular among Blockstream Satellite users. Nevertheless, other SDR
boards/interfaces can be used with minor tweaks, such as USRPs. The requirement
for the SDR interface is that it is able to receive L-band frequencies within
the 1 GHz to 2 GHz range and that it supports sampling rates of 2 Msps (mega
samples per second) or higher.

- **Connectors**: not every RTL-SDR has the same interface connector. Some use
the SMA connector, while some others use MCX. Be sure to order the correct cable
and adapters to make the necessary connections. In the above table, we assume
the RTL-SDR has SMA female connector, while the power supply has two F female
connectors. In this case, you need an SMA male-to-male cable and an SMA female
to F male adapter to connect the RTL-SDR to the **non-powered** port (“Signal to
IRD”) of the SWM power supply.

### Components for a Linux USB Receiver Setup

The only specific component in this setup is the external USB-based DVB-S2
receiver. The supported receiver is the [TBS5927 Professional DVB-S2 TV Tuner
USB](https://www.tbsdtv.com/products/tbs5927-dvb-s2-tv-tuner-usb.html). It
connects to the Linux PC via a USB2.0 connection, and the package includes both
the USB cable and a power supply for the receiver. The LNB, in turn, connects
directly to interval *LNB IN* interface of the TBS5927.

![USB Connections](img/usb_connections.png?raw=true "USB Connections")

> NOTE: although the TBS5927 receiver offers Windows support, we do not
> support Windows as operating system for a Blockstream Satellite setup.

### Components for a Standalone Receiver Setup

In this setup, a standalone DVB-S2 receiver connects to the host PC (or to the
network) through an Ethernet cable. The supported standalone receiver is the
[Novra S400 PRO DVB satellite
Receiver](https://novra.com/product/s400-pro-dvb-satellite-receiver). Other than
the receiver, you only need an Ethernet Cable.

![Standalone Connections](img/standalone_connections.png?raw=true "Standalone Connections")

## Further Notes

### “Universal” LNB:

A Universal LNB, also known as Universal Ku band LNB, is an LNB that supports
both Ku low and Ku high bands. In SDR-based setups, we recommend using this type
of LNB only within [Ku low band region](frequency.md#signal-frequencies), namely
to receive from Telstar 11N Africa, Telstar 11N Europe, or Telstar 18V Ku.

The rationale is that a 22 kHz tone must be sent to the Universal LNB in order
to switch its sub-band. However, the SDR setup described in this guide is
receiver-only, so it cannot generate the 22 kHz tone by itself. Yet, since the
default Ku sub-band of Universal LNBs is typically the low band, it is often
acceptable to use such LNBs within Ku low band region without a 22 kHz tone
generator.

Note that, in contrast to an SDR setup, both Linux USB and Standalone [receiver
options](#receiver-options) support the generation of 22 kHz. Hence, with these
receivers, it is acceptable to use a Universal LNB in any Ku band region.

In case you do want to switch the sub-band of a Universal LNB with an SDR setup,
you will need to place a 22 kHz tone generator inline between the LNB and the
power inserter. This is because the tone generator uses power from the inserter
while delivering the tone directly to the LNB.

Such tone generators can be found in the market as pure
generators. Alternatively, you can get a satellite finder device containing the
22 kHz generation functionality.

If choosing a satellite finder, it is essential to note that the finder must be
one that can be used inline between the power supply and the LNB. That is, it
must be one with two connectors, one for signal input (from the LNB) and the
other for output (towards the power inserter). Some finders contain a single
connector, as they are not intended to be used inline. Furthermore, be aware
that most finders do not contain a 22 kHz generator. You must pick a satellite
finder that supports the generation of a 22 kHz tone.

### LNB vs. LNBF:

The feedhorn is the horn antenna that attaches to the LNB. It collects the
signals reflected by the satellite dish and feeds them into the LNB towards the
receiver. The acronym LNBF stands for "LNB with feedhorn" and refers to the LNB
that already contains an integrated feedhorn. This is the most typical type of
LNB nowadays. Hence, almost always, the term LNB already refers to an LNBF
implicitly. To avoid confusion, we advise looking for an LNBF.

---

Prev: [Frequency Bands](frequency.md) - Next: [Receiver Setup](receiver.md)
