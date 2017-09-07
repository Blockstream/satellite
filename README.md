# Blockstream Satellite Receiver

This repository contains the development sources of the GNU Radio-based receiver
for the Blockstream Satellite network.

In order to set up your receiver system, please read the following information
carefully and follow the instructions outlined in the [wiki](../../wiki). For
additional help, go to the #blockstream-satellite IRC channel on freenode.

This is an initial release and regular improvements will be made to make
Blockstream Satellite more user friendly and less technically complex.

# Getting Started

During your initial set-up, you will need to go through the following steps:

1. Check your coverage at Blockstream's
   [Interactive Coverage Map](http://www.blockstream.com/satellite/satellite).
2. Gather the required hardware - appropriate satellite dish, low-noise block
   downconverter (LNB), power supply, mounting hardware, SDR interface, cables
   and connectors.
3. Download the required software - Bitcoin FIBRE, GNU Radio and GR OsmoSDR.
4. Install the receiver and software dependencies.
5. Align your satellite dish with the help of the receiver application.

All of these steps are thoroghly explained in [**the wiki**](../../wiki), which
you should read next.

# Receiver Startup

After successful set-up of your receiver, change to the `satellite/grc`
directory and run the receiver application with:

```
python rx.py --freq [freq_in_hz] --gain [gain]
```

**Parameters:**

- `freq_in_hz`: the frequency parameter, **specified in units of Hz**.  This
parameter should be equal to the difference between your satellite's frequency
and the frequency of your LNB local oscillator (LO).  For more details on how to
compute it, see the
[Antenna Alignment guide](../../wiki/Antenna-Alignment#freq_param).
- `gain`: the gain value **between 0 and 50**. See more information in the
[Antenna Alignment guide](../../wiki/Antenna-Alignment#rx_parameters).

**Example:**

```
python rx.py --freq 1276150000 --gain 40
```

**NOTE:**: The frequency parameter is specified in Hz. So 1276.15 MHz would be
specified as 1276150000 Hz, as in the above example.

# Bitcoin FIBRE Startup

Bitcoin FIBRE uses the same `bitcoin.conf` configuration file as Bitcoin Core.
Configure as needed and start `bitcoind` with the following parameters after the
receiver (above) is running:

```
./bitcoind -fecreaddevice=/tmp/async_rx
```

>Note: The Blockstream Satellite receiver will create the `/tmp/async_rx` file.

# Setup Complete

Once both the Blockstream Satellite Receiver and Bitcoin FIBRE are running, your
node will stay in sync!

