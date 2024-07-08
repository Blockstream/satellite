---
parent: Hardware guide
nav_order: 5
---

# Hardware Components

This guide covers each hardware component in detail so you can assemble your receiver setup from scratch. It is an essential read if you are planning to assemble your setup by mixing and matching supported parts instead of purchasing a pre-assembled [Satellite Kit](https://store.blockstream.com/product-category/satellite_kits/). If that is not you, please feel free to skip this section.

The components that you need to understand are the following:

- [DVB-S2 Receiver](#dvb-s2-receiver)
  - [Software-defined Radio (SDR) Receiver](#software-defined-radio-sdr-receiver)
  - [Linux USB Receiver](#linux-usb-receiver)
  - [Standalone Receiver](#standalone-receiver)
  - [Sat-IP Receiver](#sat-ip-receiver)
- [Antenna](#antenna)
  - [Dish Antenna](#dish-antenna)
  - [Flat Panel Antenna](#flat-panel-antenna)
  - [Sat-IP Antenna](#sat-ip-antenna)
- [Low-noise Block Downconverter (LNB)](#low-noise-block-downconverter-lnb)
- [LNB Mounting Bracket](#lnb-mounting-bracket)
- [Cables](#cables)
- [Specific Parts for the SDR Setup](#specific-parts-for-the-sdr-setup)
- [Further Notes](#further-notes)
  - [Universal LNB](#universal-lnb)
  - [LNB vs. LNBF](#lnb-vs-lnbf)

## DVB-S2 Receiver

The receiver is the device or software application that processes the incoming satellite signal and decodes the data stream from it. There are four supported types of receivers. For each of them, specific hardware components are required.

The receiver options are summarized below. For further insights, please refer to the [satellite receiver comparison](hardware.md#satellite-kits) table presented previously.

### Software-defined Radio (SDR) Receiver

This receiver is entirely implemented in software. You will need an SDR interface connected to your PC (typically via USB). The SDR interface collects and feeds signal samples to the receiver application/software running on your PC. The application, in turn, decodes and outputs the data stream to be fed into [Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite). This is the most affordable option among the three, as it works with inexpensive RTL-SDR USB dongles. However, it is also the option expected to present the most limited performance and reliability among the three. Moreover, this option is CPU-intensive since the receiver application will run on the CPU.

The connections with the SDR receiver are as follows:

![SDR receiver connections](img/sdr_connections.png?raw=true "SDR receiver connections")

The supported SDR interface is an **RTL-SDR** of **model RTL2832U** with either the **R820T2** or the **E4000 tuner**, depending on your region. Also, you will need an independent LNB power supply when using an SDR receiver. More details on the specific parts required with this receiver option are available in the [SDR receiver parts section](#specific-parts-for-the-sdr-setup).

### Linux USB Receiver

In this setup, the demodulation is entirely carried out in hardware in the external receiver device connected to your host via USB. Hence, unlike the SDR receiver, the Linux USB receiver is not CPU-intensive. With this option, you will need to install specific drivers and Linux DVB-S2 apps on the host to configure the external receiver and get the data from it. Overall, this option is expected to perform well and with negligible CPU usage. On the other hand, it can require a time-consuming initial setup due to the driver installation. You can try the [driver installation](tbs.md#tbs-drivers) on your intended host before committing to this receiver option.

The supported Linux USB receivers are the [TBS 5927](https://www.tbsdtv.com/products/tbs5927-dvb-s2-tv-tuner-usb.html) and the [TBS 5520SE](https://www.tbsdtv.com/products/tbs5520se_multi-standard_tv_tuner_usb_box.html) models, which connect to the Linux PC via USB 2.0. These models are powered up either directly by the host via USB (TBS 5520SE) or with an included dedicated power supply (TBS 5927). Also, they can power up the LNB directly via the coaxial cable with no need for an external LNB supply.

The connections with the TBS 5927 and 5520SE receivers are illustrated below:

![Linux USB receiver connections](img/usb_connections.png?raw=true "Linux USB receiver connections")

> **Note:** Although the TBS 5927 and 5520SE receivers offer Windows support, we currently do not support Windows as an operating system for a Blockstream Satellite setup.

### Standalone Receiver

The standalone receiver is also a hardware-based receiver, with the difference that it is entirely independent of the host PC. It connects to the PC through the network with an Ethernet cable and can feed multiple PCs concurrently. It is also expected to be a great option in terms of performance. Also, it is the only receiver supporting [dual-satellite reception](dual-satellite.md) with a single receiver device.

The standalone receiver that is currently supported is the [Novra S400 PRO DVB satellite Receiver](https://novra.com/product/s400-pro-dvb-satellite-receiver). Other than the receiver itself, you only need an Ethernet Cable. The connections are as follows:

![Standalone receiver connections](img/standalone_connections.png?raw=true "Standalone receiver connections")

### Sat-IP Receiver

The Sat-IP Receiver is another hardware-based and standalone receiver option. The difference is that it is based on an all-in-one antenna with a built-in DVB-S2 receiver and integrated LNB (see the [Satellite Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/)). It is referred to as a Sat-IP receiver because it runs a [Sat-IP server](https://en.wikipedia.org/wiki/Sat-IP), to which your host will connect as a client. Overall, this option offers the easiest configuration and the most minimalist setup, given that it requires a single component (the all-in-one antenna). However, note it does not work with the Telstar 18V C band satellite covering the Asia-Pacific region.

The Sat-IP receiver that is currently supported is the all-in-one Selfsat>IP22 Sat-IP flat-panel antenna. It requires an Ethernet cable (Cat5e or superior) to connect to a switch, router, or directly to your host. Furthermore, it requires Power over Ethernet (PoE). Hence, you will need a PoE injector if the network adapter connecting to the Sat-IP antenna does not support PoE.

The connections with the Sat-IP receiver are as follows:

![Sat-IP receiver connections](img/sat-ip-connections.png "Sat-IP receiver connections")

## Antenna

In addition to the DVB-S2 receiver, you will always need an antenna to receive the satellite signal. The most widely available antenna option is the regular satellite TV dish with a conventional parabolic reflector. However, you can also use a flat panel antenna if you are looking for a more compact and stylish option. Also, you can use a Sat-IP antenna like the [Satellite Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/) with a built-in DVB-S2 receiver and integrated LNB. With a Sat-IP antenna, you don't need a separate DVB-S2 receiver. Instead, the receiver and antenna are all in one.

### Dish Antenna

Blockstream Satellite is designed to work with small dishes, with diameters as low as 45 cm in [Ku band](frequency.md#signal-bands) and 60 cm in [C band](frequency.md#signal-bands). However, we recommend checking our [Link Analyzer](https://satellite.blockstream.space/link-analyzer/) tool for more specific antenna recommendations. After inputting your coordinates, you can obtain the list of supported antennas for your location. Then, you can feel free to pick the smallest supported option. However, if you are looking to obtain the best performance, a larger antenna is always preferable.

Other than size, the only additional requirement is that the antenna works with the frequency band that suits your coverage region. You can always use antennas designed for higher frequencies. For example, an antenna designed for the Ka band will work for the Ku and C bands, as it is designed for higher frequencies than those used by Blockstream Satellite. However, a C-band antenna will not work in the Ku band, as it is designed for lower frequencies. For further information regarding frequency bands, please refer to [the frequency guide](frequency.md).

### Flat Panel Antenna

A flat panel antenna is generally more compact and stylish than a conventional dish. However, they are typically only available for Ku band.

A recommended flat panel model is the Selfsat H50D, which was previously available on Blockstream Store before being replaced by the all-in-one [Satellite Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/). The Selfsat H50D includes the LNB internally, so there is no need to purchase an LNB (nor an LNB bracket) when using it. However, note that this model has limited compatibility. It is an excellent option for:

1. **Linux USB** and **Standalone Receivers** in any Ku band region.
2. **SDR** receivers in Ku low band regions (Telstar 11N Africa, Telstar 11N Europe, and Telstar 18V Ku).

In contrast, the Selfsat H50D flat panel is **not** compatible with receivers (of any type) in the Telstar 18V C (C Band) region. It only works in [Ku band](frequency.md#signal-bands).

The flat panel requires an extra 22 kHz generator to work with **SDR** receivers in the Ku high band (Galaxy 18) since it includes a built-in [Universal LNB](#universal-lnb). Refer to further information and a solution for 22 kHz generation in [the Universal LNB section](#universal-lnb).

### Sat-IP Antenna

As mentioned earlier, a Sat-IP antenna has a built-in receiver and integrated LNB. Hence, if you go with this option, you do not need to purchase a separate DVB-S2 receiver or an LNB. With the [Satellite Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/), the only additional component you would need is an Ethernet cable to connect the antenna to your host and a PoE-capable host. More details on this option are available on the [Satellite Base Station page](base-station.md).

## Low-noise Block Downconverter (LNB)

Next, you will always need an LNB if you are using a regular satellite dish instead of a flat-panel antenna with an integrated LNB.

When choosing an LNB, the most relevant parameters are the following:

- Frequency range.
- Polarization.
- LO stability.

**In a nutshell,** you are advised to use a PLL LNB with linear polarization and LO stability within `+- 250 kHz` or less. Also, the LNB should be suitable for the frequency of the signal covering your location.

Regarding **frequency range**, you must verify that the input frequency range of the LNB encompasses the frequency of the Blockstream Satellite signal in your coverage area. For example, if you are located in North America and covered by the Galaxy 18 satellite, the downlink frequency of interest is 11913.4 MHz. In this case, an LNB that operates from 11.7 GHz to 12.2 GHz would work. In contrast, an LNB that operates from 10.7 GHz to 11.7 GHz would **not** work. You can check the signal frequencies of each region in the [frequency guide](frequency.md#signal-frequencies).

Regarding **polarization**, an LNB with **Linear Polarization** is required. While most Ku band LNBs are linearly polarized, some popular satellite TV services use circular polarization. A circularly polarized LNB will **not** work with Blockstream Satellite.

If an LNB is described to feature horizontal or vertical polarization, then it is linear. In contrast, if an LNB is described as Right-Hand or Left-Hand Circular Polarized (RHCP or LHCP), then it is circular and will **not** work with Blockstream Satellite.

Regarding **LO Stability**, a stability specification of `<= +/- 250 kHz` is preferable for better performance. Most LNBs will have a local oscillator (LO) stability parameter referred to as “LO stability” or metrics such as "LO accuracy" and "LO drift." These are usually specified in +/- XX Hz, kHz, or MHz. An LNB that relies on a phase-locked loop (PLL) frequency reference is typically more accurate and stable. Hence, we advise looking for a PLL LNB instead of a traditional dielectric oscillator (DRO) LNB.

If you would like (or you need) to use a less stable LNB, it can also be used. The disadvantage is that it will likely degrade your setup's reliability and performance (for example, increase the bit error rate).

A widely available LNB option is the so-called **Universal Ku band LNB**. However, please note that if you are using an SDR-based setup, a **Universal LNB** may pose extra difficulties. Please refer to the [explanation regarding Universal LNBs](#universal-lnb). This limitation **does not** apply when using the Linux USB or Standalone receiver options.

Besides, another parameter of interest is the so-called F/D ratio. This parameter refers to the ratio between the parabolic reflector's focal length and its diameter. As such, it is a parameter of the dish, not the LNB. Nevertheless, the LNB should be designed for an F/D ratio compatible with the reflector.

For example, an [offset dish](https://en.wikipedia.org/wiki/Offset_dish_antenna) (the most common dish type for Ku band) typically has an F/D ratio from 0.5 to 0.7. In contrast, a regular "front-fed" parabolic dish typically has an F/D in the 0.3 to 0.4 range. In any case, check the F/D specifications of your dish and make sure to use a compatible LNB. If necessary, attach a flat or conical scalar ring to change the F/D characteristics of the LNB.

Lastly, to avoid confusion, please note that *LNBF* and *LNB* often refer to the same thing. You can find further information [later in this guide](#lnb-vs-lnbf).

## LNB Mounting Bracket

The antenna dish likely comes with a mounting bracket, but you will need one designed to accept a generic LNB. Also, it is good to have a flexible bracket to facilitate the LNB rotation and control of its polarization angle. Although mounting brackets typically support rotation, some can be limited in the rotation range.

Such mounting brackets attach to the antenna's feed arm and have a circular ring that will accept a generic LNB.

## Cables

You will need a coaxial cable when using a satellite dish with an external LNB or a flat panel antenna with an integrated LNB. The coaxial cable will connect the receiver to the LNB. Alternatively, in the case of the SDR-based setup, the cable will connect the LNB to the power supply, and then another cable will connect the power supply to the SDR interface.

The most popular and recommended type of coaxial cable is the RG6 cable. Please choose one with the right length, considering how far the antenna will be from the receiver. Also, please note that the cable length will affect the signal strength. Hence, avoid unnecessarily long cables if possible.

In some cases, you may need to pass the cable through a window or door frame. For that, you can use a short, bendable, flat coaxial TV extension cable. Such an extension cable is typically a few centimeters long, just enough to pass through the window or door frame. Then, you connect the longer RG6 cables on both ends of it.

You will also need an Ethernet cable when using a standalone receiver or a Sat-IP receiver. The Ethernet cable will connect the receiver to the host PC or the network.

Also, with an SDR receiver, you will typically need SMA cable(s), as detailed in the next section.

## Specific Parts for the SDR Setup

The SDR setup is the most affordable option but also the one requiring the most parts. This section elaborates on parts used specifically with the SDR setup.

The main specific components are the following:

| Component        | Requirement                           |
| ---------------- | ------------------------------------- |
| SDR interface    | RTL-SDR dongle model RTL2832U w/ TCXO |
| LNB Power Supply | SWM Power Supply                      |
| SMA Cable        | Male to Male                          |
| SMA to F adapter | SMA Female, F Male                    |

The supported **SDR interface** is the RTL-SDR, which is a low-cost USB dongle. More specifically, an RTL-SDR of model RTL2832U.

There are two specifications to observe when purchasing an RTL-SDR:

1. Oscillator
2. Tuner

We recommend using an RTL-SDR with a temperature-controlled crystal oscillator (TCXO), as the TCXO has better frequency stability than a conventional crystal oscillator (XO). A few models in the market feature a TCXO with frequency accuracy within 0.5 ppm to 1.0 ppm, which are good choices.

Regarding the tuner, the choice depends on the satellite covering your location. The two recommended tuners are the R820T2 and the E4000. The table below summarizes which tuner to pick for each satellite:

| Satellite          | RTL-SDR Tuner |
| ------------------ | ------------- |
| Galaxy 18          | R820T2        |
| Telstar 11N Africa | E4000         |
| Telstar 11N Europe | E4000         |
| Telstar 18V Ku     | E4000         |
| Telstar 18V C      | R820T2        |

This tuner recommendation has to do with the L-band frequencies expected in each region, as summarized in the [frequency guide](frequency.md#l-band-frequencies). The E4000 tuner is recommended for the areas where the L-band frequency is close to the maximum tuning range of the R820T2 tuner (1766 MHz).

Hence, for example, if you are going to receive from Galaxy 18, you should get an RTL-SDR RTL2832U with tuner R820T2 and TCXO. In contrast, if you are going to receive from Telstar 11N Africa, you should get an RTL-SDR RTL2832U with tuner E4000 and TCXO. Note that the RTL-SDR models featuring the E4000 tuner are marketed as **extended tuning range RTL-SDR** or **XTR RTL-SDR**.

The next component of the SDR receiver setup is the **LNB Power Supply** (or Power Inserter). This component supplies a DC voltage to the LNB via the coaxial cable, typically of 13 VDC or 18 VDC. On a non-SDR setup, the receiver itself can provide power to the LNB, so there is no need for an external power supply. In contrast, this is not possible with an SDR-based setup using the SDR interface alone. Hence, an external supply is required.

The type of power supply that is easy to find in the market is called "Single Wire Multiswitch" (SWM) power supply. You can look for an SWM power inserter and use it, as illustrated below. The **non-powered** port of an SWM power supply is labeled "Signal to IRD," which means signal to integrated receiver/decoder. This is the port that should be connected to the SDR interface. The **powered** port, in turn, is labeled "Signal to SWM." This is the port that should be connected to the LNB.

![SDR receiver connections](img/sdr_connections.png?raw=true "SDR receiver connections")

**IMPORTANT**: Do **NOT** connect the powered port of the LNB power supply to the SDR interface. Permanent damage may occur to your SDR and/or your computer.

Also, please check the power/voltage requirement of your LNB and ensure that your power supply matches. It should be noted that some LNBs, known as **dual-polarization LNBs**, accept two DC voltage levels. Such LNBs use the supplied voltage to switch between vertical and horizontal polarization. A supplied DC voltage of +18 VDC sets the LNB to horizontal polarization, whereas +13 VDC sets the LNB to vertical polarization. Please keep this in mind when rotating the LNB for a specific polarization angle during the antenna pointing stage.

**Further notes**:

- **Alternative SDR interfaces**: the RTL-SDR is the supported SDR interface and the most popular among Blockstream Satellite users. Nevertheless, other SDR boards/interfaces can be used with minor tweaks, such as USRPs. The SDR interface must support L-band frequencies within the 1 GHz to 2 GHz range and sampling rates of 2 Msps (mega samples per second) or higher.

- **Connectors**: not every RTL-SDR has the same interface connector. Some use the SMA connector, while others use MCX. Be sure to order the correct cable and adapters to make the necessary connections. In the above table, we assume the RTL-SDR has an SMA female connector, while the power supply has two F female connectors. In this case, you need an SMA male-to-male cable and an SMA female-to-F male adapter to connect the RTL-SDR to the **non-powered** port (“Signal to IRD”) of the SWM power supply.

## Further Notes

### Universal LNB

A Universal LNB, also known as Universal Ku band LNB, is an LNB that supports both [Ku low and Ku high bands](frequency.md#signal-bands). With such an LNB, the receiver becomes responsible for switching the Ku sub-band as needed. More specifically, the receiver sends a 22 kHz tone to the LNB when tuning to a Ku high band carrier. Otherwise, when tuning to a Ku low-band carrier, the receiver simply does not send any tone. The absence of a 22 kHz tone configures the LNB to its default sub-band, the Ku low sub-band.

An important limitation applies to the SDR setup when using a Universal LNB. Note the SDR setup described in this guide is receiver-only. Hence, it cannot generate a 22 kHz tone to configure the Universal LNB. Consequently, a Universal LNB connected to an SDR receiver operates in Ku low band only. Thus, we recommend using this type of LNB only within [Ku low band regions](frequency.md#signal-frequencies), i.e., within the areas covered by Telstar 11N Africa, Telstar 11N Europe, or Telstar 18V Ku.

Meanwhile, in contrast to an SDR setup, both Linux USB and Standalone [receiver options](#dvb-s2-receiver) support the generation of 22 kHz. Hence, it is perfectly acceptable to use a Universal LNB in any Ku band region when using one of these receivers.

Besides, there are workarounds to switch the sub-band of a Universal LNB, even with an SDR setup. For instance, you can place a 22 kHz tone generator inline between the LNB and the power inserter. In this case, the tone generator will use power from the inserter while delivering the tone directly to the LNB. Such tone generators can be found in the market as pure generators. Alternatively, you can get a satellite finder device containing the 22 kHz generation functionality.

If choosing a satellite finder, it is essential to note that the finder must be one that can be used inline between the power supply and the LNB. In other words, it must be one with two connectors, one for signal input (from the LNB) and the other for output (towards the power inserter). Some finders contain a single connector, as they are not intended to be used inline. Furthermore, be aware that most finders do not include a 22 kHz generator. You must pick a satellite finder that supports the generation of a 22 kHz tone.

### LNB vs. LNBF

The feedhorn is the horn antenna that attaches to the LNB. It collects the signals reflected by the satellite dish and feeds them into the LNB towards the receiver. The acronym LNBF stands for "LNB with feedhorn" and refers to the LNB that already contains an integrated feedhorn. This is the most typical type of LNB nowadays. Hence, almost always, the term LNB already refers to an LNBF implicitly. To avoid confusion, we advise looking for an LNBF.

---

Prev: [SDR Setup](sdr-setup.md) - Next: [Software Requirements](software.md)