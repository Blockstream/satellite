# Blockstream Satellite

## Overview

The [Blockstream Satellite](https://blockstream.com/satellite/) network broadcasts the Bitcoin blockchain worldwide 24/7 for free, protecting against network interruptions and providing areas without reliable internet connection with the opportunity to use Bitcoin. You can join this network by running your own Blockstream Satellite receiver node. The [user guide](https://blockstream.github.io/satellite/) covers all the hardware options, software components, and assembly instructions.

In summary, the process requires the five steps below:

1. Check your coverage at our [Coverage Map](https://blockstream.com/satellite/#satellite_network-coverage).
2. Get the required hardware, such as a ready-to-use [Satellite Kit](https://store.blockstream.com/product-category/satellite_kits/).
3. Use the Blockstream Satellite command-line interface (CLI) to handle all the required software installations and configurations.
4. Align your satellite dish appropriately to receive the Blockstream Satellite signal.
5. Run the [Bitcoin Satellite](https://github.com/Blockstream/bitcoinsatellite/) and [Satellite API](https://blockstream.github.io/satellite/doc/api.html) applications.

When checking the coverage, ensure your view of the satellite has no obstacles, such as trees or buildings. You can find the target area in the sky using the antenna [pointing angles](https://blockstream.github.io/satellite/doc/antenna-pointing.html#mount-the-antenna) provided by our coverage map or a mobile app such as the Satellite Finder (Pro) for [iOS](https://apps.apple.com/br/app/satellite-finder-pro/id1075788157) and the Satellite Pointer for [Android](https://play.google.com/store/apps/details?id=com.tda.satpointer).

Once you get your receiver node up and running, there is a lot that you can do with it. You can use it as a satellite-connected Bitcoin node offering redundancy and protection from internet failures to connected peers. Alternatively, you can run it as your primary Bitcoin full node, with hybrid connectivity (internet and satellite) or only satellite connectivity. The satellite network broadcasts new blocks, transactions, and the complete block history. Hence, you can synchronize the entire blockchain from scratch using the satellite connection.

You can also send encrypted messages worldwide through the satellite network using our [Satellite API](https://blockstream.github.io/satellite/doc/api.html) while paying for each transmission through the Lightning Network. Moreover, if you run a Lightning node, you can sync it faster through [Lightning gossip snapshots](https://blockstream.github.io/satellite/doc/api.html#lightning-gossip-snapshots) sent over satellite. You can even [download the Bitcoin source code](https://blockstream.github.io/satellite/doc/api.html#bitcoin-source-code-messages) over satellite and bootstrap the node without touching the internet.

To get started, please follow the [user guide](https://blockstream.github.io/satellite/), also available in [PDF format](https://satellite.blockstream.space/docs/blocksat_manual.pdf). For further information, refer to the following links:

- [Satellite kits](https://store.blockstream.com/product-category/satellite_kits/) and [satellite kit setup instructions](https://help.blockstream.com/hc/en-us/articles/900001613686).
- [Articles and frequently asked questions](https://help.blockstream.com/hc/en-us/categories/900000061466-Blockstream-Satellite/).
- [How the Bitcoin Satellite application works](https://github.com/Blockstream/bitcoinsatellite/wiki/doc/bitcoin-satellite.pdf).

## Support

For additional help, you can join the **#blockstream-satellite** IRC channel on freenode or contact [Blockstream Support](https://help.blockstream.com/).
