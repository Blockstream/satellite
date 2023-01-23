# Blockstream Satellite

## Overview

The [Blockstream Satellite](https://blockstream.com/satellite/) network broadcasts the Bitcoin blockchain worldwide 24/7 for free, protecting against network interruptions and providing areas without reliable internet connection with the opportunity to use Bitcoin. You can join this network by running your own Blockstream Satellite receiver node. The [user guide](https://blockstream.github.io/satellite/) covers all the hardware options, software components, and assembly instructions.

The first step to get started is to verify whether your location has satellite coverage and a clear view of the satellite in the sky. You can confirm the coverage by looking at our [Coverage Map](https://blockstream.com/satellite/#satellite_network-coverage). After that, ensure your satellite view has no obstacles, such as trees or buildings. You can find the target area in the sky using the antenna pointing angles provided by our coverage map or an augmented reality app such as the Satellite Pointer (available for [iOS](https://apps.apple.com/th/app/satellite-pointer/id994565490) and [Android](https://play.google.com/store/apps/details?id=com.tda.satpointer)).

The second step is to get the required hardware. The quickest option is to purchase a ready-to-use [Satellite Kit](https://store.blockstream.com/product-category/satellite_kits/). Alternatively, you can find several other [hardware options](https://blockstream.github.io/satellite/doc/hardware.html) in the user guide.

Third, you need to prepare a host computer with a few software components. One of them is the [Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite/) application, a fork of Bitcoin Core with custom capabilities to receive the Bitcoin blocks and transactions arriving from space. As detailed in the [user guide](https://blockstream.github.io/satellite/#software-and-setup-configuration), the Blockstream Satellite command-line interface (CLI) tool handles all the necessary software installations and configurations.

Once you get your receiver node up and running, there is a lot that you can do with it. You can use it as a satellite-connected Bitcoin node offering redundancy and protection from internet failures to connected peers. Alternatively, you can run it as your primary Bitcoin full node, with hybrid connectivity (internet and satellite) or only satellite connectivity. The satellite network broadcasts new blocks, transactions, and the complete block history. Hence, you can synchronize the entire blockchain from scratch using the satellite connection.

You can also send encrypted messages worldwide through the satellite network using our [Satellite API](https://blockstream.github.io/satellite/doc/api.html) while paying for each transmission through the Lightning Network. Moreover, if you run a Lightning node, you can sync it faster through [Lightning gossip snapshots](https://blockstream.github.io/satellite/doc/api.html#lightning-gossip-snapshots) sent over satellite. You can even [download the Bitcoin source code](https://blockstream.github.io/satellite/doc/api.html#bitcoin-source-code-messages) over satellite and bootstrap the node without touching the internet.

To get started, please follow the [user guide](https://blockstream.github.io/satellite/). For further information, refer to the following links:

- [Satellite kits](https://store.blockstream.com/product-category/satellite_kits/) and [satellite kit setup instructions](https://help.blockstream.com/hc/en-us/articles/900001613686).
- [Articles and frequently asked questions](https://help.blockstream.com/hc/en-us/categories/900000061466-Blockstream-Satellite/).
- [How the Bitcoin Satellite application works](https://github.com/Blockstream/bitcoinsatellite/wiki/doc/bitcoin-satellite.pdf).

## Support

For additional help, you can join the **#blockstream-satellite** IRC channel on freenode or contact [Blockstream Support](https://help.blockstream.com/).
