---
title: Hardware guide
has_children: true
nav_order: 2
has_toc: false
---

# Hardware Guide

This section introduces the hardware required to set up a Blockstream Satellite receiver.

There are three alternatives to collecting the required hardware. The first and quickest option is to purchase a ready-to-use [Satellite Kit](#satellite-kits). For that, please check the kits available on the [Blockstream Store](https://store.blockstream.com/product-category/satellite_kits/). The second alternative is to buy the [Satellite Kit Components](#purchasing-the-kit-components) on your own. Lastly, the third alternative is to pick a combination of compatible parts, not necessarily following any kit recipe. To do so, you will need to understand the [hardware components](hardware-components.md) in detail.

In the sequel, we briefly discuss the differences between the kits so that you can make an informed decision.

## Satellite Kits

There are four broad categories of receiver setups and kits:

1. Satellite Base Station Setup.
2. Standalone Receiver Setup (Pro Kit).
3. Linux USB Receiver Setup (Basic Kit).
4. Software-defined Radio (SDR) Receiver Setup.

Only two of those are currently available on Blockstream Store:

1. [Satellite Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/).
2. [Pro Kit](https://store.blockstream.com/products/blockstream-satellite-pro-kit/).

The following table summarizes the key differences between them:

|                                       |        SDR         |     Basic Kit      |      Pro Kit       |    Base Station    |
| ------------------------------------- | :----------------: | :----------------: | :----------------: | :----------------: |
| Blockstream Kit Available             |                    |                    | :heavy_check_mark: | :heavy_check_mark: |
| USB Interface                         | :heavy_check_mark: | :heavy_check_mark: |                    |                    |
| Ethernet Interface                    |                    |                    | :heavy_check_mark: | :heavy_check_mark: |
| Requires External LNB Power Supply    | :heavy_check_mark: |                    |                    |                    |
| Support for Universal LNB<sup>1</sup> |                    | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| Dual-Satellite Capable<sup>2</sup>    |                    |                    | :heavy_check_mark: |                    |
| CPU Utilization<sup>3</sup>           |        High        |        Low         |        None        |        None        |
| Multiple Host Connections<sup>4</sup> |                    |                    | :heavy_check_mark: | :heavy_check_mark: |
| Optional Rack Mountable               |                    |                    | :heavy_check_mark: |                    |
| C-band Compatibility<sup>5</sup>      | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    |
| Performance<sup>6</sup>               |      Limited       |     Excellent      |     Excellent      |     Excellent      |
| Budget                                |    Low (< $150)    |       Medium       |   High (> $900)    |   Medium ($500)    |

<sup>1</sup> A Universal LNB needs a 22 kHz signal to switch between Ku low and Ku high bands. This feature is required when using Universal LNBs and receiving from the Galaxy 18 satellite. The SDR receiver cannot generate such a tone to the LNB, so it is not natively compatible with Universal LNBs. All other receivers can generate the 22 kHz tone.

<sup>2</sup> A dual-satellite receiver is one capable of receiving from two satellites simultaneously in areas with overlapping coverage. This feature enables greater redundancy, higher bitrate, and faster blockchain sync times. Only the Pro Kit receiver can receive from two satellites simultaneously.

<sup>3</sup> The SDR receiver is implemented in software and runs on the host computer, using significant CPU resources. The Basic Kit receiver uses a dedicated receiver chip and only minimal resources from the host CPU. The Pro Kit and Base Station receivers are entirely standalone.

<sup>4</sup> A multi-host receiver is one capable of feeding the received data to multiple hosts simultaneously on the local network. Only the Pro Kit and Base Station receivers can do so. In contrast, the SDR and Basic Kit receivers connect over USB to a single host and feed received data to this host only.

<sup>5</sup> C band support is required to receive the Telstar 18V C band beam in the Asia-Pacific region. The Base Station receiver is not compatible with the C band because it is an all-in-one integrated receiver and antenna designed for Ku band only.

<sup>6</sup> The SDR receiver is an excellent option for a budget-limited setup. However, it is expected to have inferior performance due to software limitations.

## Choosing the Right Kit

As mentioned, only two kits are currently available on the Blockstream Store: the [Base Station](https://store.blockstream.com/products/blockstream-satellite-base-station/) and the [Pro Kit](https://store.blockstream.com/products/blockstream-satellite-pro-kit/).

For most users, we recommend the Base Station receiver. Its minimalist design, simplified setup, and high performance will fit most Bitcoin users' needs.

The main reason to consider an alternative to the Base Station is if you are in a location with [C band](frequency.md#signal-bands) coverage only (i.e., without Ku band coverage). In that case, you will need an alternative option, like the Pro kit. The Base Station does not work with the Telstar 18V C band beam covering the Asia-Pacific region.

We recommend considering the Pro Kit if one of the following conditions apply to you:

- You are covered only by the Telstar 18V C band beam and not covered by the Telstar 18V Ku band beam.
- You would like to use a dish antenna instead of the Base Station antenna.
- The [Link Analyzer](https://satellite.blockstream.space/link-analyzer/) tool indicates the base station will not work well in your location.
- Two satellite beams cover your location, and you would like to receive from both simultaneously using two independent antennas.

If you conclude you need the Pro Kit, but the price is out of your budget, you can consider the Basic Kit or the SDR receiver as alternatives. However, please note the Basic Kit and SDR setups do not support dual-satellite reception.

The Basic Kit offers similar performance and convenience as the Pro Kit but with more affordable components. Please refer to the list of [Basic Kit components](basic-kit.md).

Meanwhile, the SDR setup is the most affordable option. Generally, an SDR setup will cost between $100 and $150 (USD). However, note the SDR setup needs a host computer to run the CPU-intensive receiver software. So please take the CPU into account when considering this option.

Also, we recommend the SDR setup for tech-savvy individuals or anyone interested in understanding more about satellite communications or experimenting with SDR technology. The SDR setup has the most flexibility and room for experimentation. Also, it offers the broadest range of inspection tools and graphical user interfaces (GUIs) to monitor the received signal and many low-level parameters. For instance, such visualizations can be very handy when pointing the antenna for the first time. If that appeals to you, please refer to the [SDR setup](sdr-setup.md) parts list.

## Purchasing the Kit Components

After reading the above description, you may be inclined to purchase the kit components on your own instead of ordering a kit from Blockstream Store. If that is your case, please refer to the parts list for your selected setup:

- [Basic USB Kit](basic-kit.md).
- [Standalone Pro Kit](pro-kit.md).
- [Satellite Base Station](base-station.md).
- [SDR Setup](sdr-setup.md).

Lastly, if you would like to mix and match various supported parts, please proceed to the in-depth coverage of the [hardware components](hardware-components.md).

---

Prev: [Home](../index.md) - Next: [Basic Kit](basic-kit.md)
