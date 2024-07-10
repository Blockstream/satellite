---
title: Home
nav_order: 1
---

# Blockstream Satellite

## Overview

The [Blockstream Satellite](https://blockstream.com/satellite/) network broadcasts the Bitcoin blockchain worldwide 24/7 for free, protecting against network interruptions and providing areas without reliable internet connection with the opportunity to use Bitcoin. You can join this network by running your own Blockstream Satellite receiver node. This document guides you through all the hardware options, software components, and assembly instructions.

In summary, the process requires the five steps below:

1. Check your coverage at our [Coverage Map](https://blockstream.com/satellite/#satellite_network-coverage).
2. Get the required hardware, such as a ready-to-use [Satellite Kit](https://store.blockstream.com/product-category/satellite_kits/).
3. Use the Blockstream Satellite command-line interface (CLI) to handle all the required software installations and configurations.
4. Align your satellite dish appropriately to receive the Blockstream Satellite signal.
5. Run the [Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite/) and [Satellite API](doc/api.md) applications.

When checking the coverage, ensure your view of the satellite has no obstacles, such as trees or buildings. You can find the target area in the sky using the antenna [pointing angles](doc/antenna-pointing.md#mount-the-antenna) provided by our coverage map or a mobile app such as the Satellite Finder (Pro) for [iOS](https://apps.apple.com/br/app/satellite-finder-pro/id1075788157) and the Satellite Pointer for [Android](https://play.google.com/store/apps/details?id=com.tda.satpointer).

Once you get your receiver node up and running, there is a lot that you can do with it. You can use it as a satellite-connected Bitcoin node, offering redundancy and protection from internet failures to connected peers. Alternatively, you can run it as your primary Bitcoin full node, with hybrid connectivity (internet and satellite) or only satellite connectivity. The satellite network broadcasts new blocks, transactions, and the complete block history. Hence, you can synchronize the entire blockchain from scratch using the satellite connection.

You can also send encrypted messages worldwide through the satellite network using our [Satellite API](doc/api.md) while paying for each transmission through the Lightning Network. Moreover, if you run a Lightning node, you can sync it faster through [Lightning gossip snapshots](doc/api.md#lightning-gossip-snapshots) sent over satellite. You can even [download the Bitcoin source code](doc/api.md#bitcoin-source-code-messages) over satellite and bootstrap the node without touching the internet.

The remainder of this guide covers all the above steps in detail, but a [quick reference guide](doc/quick-reference.md) is available if you are already familiar with the process. Also, a [PDF version](https://satellite.blockstream.space/docs/blocksat_manual.pdf) of the guide is available if you prefer.

If you have purchased a [satellite kit](https://store.blockstream.com/product-category/satellite_kits/), you can follow the kit-specific instructions available on [Blockstream's Help Center](https://help.blockstream.com/hc/en-us/articles/900001613686). Otherwise, we recommend continuing on this guide and proceeding to the next section, which covers the [hardware options](doc/hardware.md).

## Support

For additional help, you can join the **#blockstream-satellite** IRC channel on freenode or contact [Blockstream Support](https://help.blockstream.com/).
