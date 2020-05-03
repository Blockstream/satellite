# Antenna Pointing

Aligning a satellite antenna is a precise procedure. Remember that the
satellites are over 35,000 km (22,000 mi) away. A tenth of a degree of error
will miss the satellite by more than 3500 km. Hence, this is likely the most
time-consuming step of the process. The steps of the process are thoroughly
described next.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Antenna Pointing](#antenna-pointing)
    - [Mount the Antenna](#mount-the-antenna)
    - [Achieve Signal Lock](#achieve-signal-lock)
        - [TBS5927](#tbs5927)
        - [Novra S400](#novra-s400)
        - [SDR-based](#sdr-based)
    - [Optimize SNR](#optimize-snr)
    - [Next Steps](#next-steps)

<!-- markdown-toc end -->

## Mount the Antenna

First of all, you should obtain the pointing angles that are required for your
specific location using our [**Dish Alignment
Tool**](https://blockstream.com/satellite/#satellite-resources).

After entering your address or latitude/longitude, the tool will give you the
three parameters that are explained next:

- **Azimuth**: the side to side angle of your antenna. If you think of the
  antenna fixed within a vertical plane and loose such that it can be rotated
  from side to side (in the horizontal plane), the azimuth determines the
  direction to which it points after being rotated. 0 degrees refers to North,
  90 degrees points to East, 180 degrees to South and 270 degrees to West.

- **Elevation**: the up and down adjustment of your antenna. The antenna aiming
  tool provides the number of degrees above the horizon to which your antenna
  must point. 0 degrees represents pointing at the horizon and 90 degrees is
  pointing straight up.

- **Polarity**: determines the rotation of the LNB, rather than the dish. It is
  the angle of the LNB within the LNB mounting bracket (or holder). Often this
  is referred to also as the LNB *rotational angle* or *LNB skew*.

The three angles are illustrated below:

Azimuth                                        |  Elevation                                           | Polarity                                                  |
:---------------------------------------------:|:----------------------------------------------------:|:---------------------------------------------------------:|
![Azimuth](img/azimuth.png?raw=true "Azimuth") | ![Elevation](img/elevation.png?raw=true "Elevation") | ![Polarity](img/lnb_polarization.png?raw=true "Polarity") |

Next, visually inspect the direction your antenna must point to. Use a compass
or smartphone app to identify the direction. Ensure that there are no obstacles
such as trees or buildings in the path between your antenna location and the
area of the sky that your antenna must point to. It is important that you have
clear line of sight to that area of the sky.

**NOTE:** There are many useful smartphone apps that will aid in pointing your
antenna. Some even have augmented reality features that allow you to see the
satellites in the sky so that you can ensure you have good line of sight. We
advise to use such apps, as they can be quite helpful.

**IMPORTANT:** If using a compass app on a smartphone, make sure to configure
the app such that it displays **true north**, instead of the **magnetic
north**. This is because the azimuth angle that is provided by our dish
alignment tool refers to true north. Also, if using an ordinary compass, or a
compass-based satellite finder, please make sure to convert the true azimuth
obtained from the dish alignment tool into magnetic azimuth. To do so, you will
need to check the *magnetic declination* at your location.

Next, install the satellite antenna according to the directions accompanying it,
or have it done professionally. If you install it yourself, proceed with the
following steps:

1. Certify that the pole on which the dish is mounted is completely level.
2. Set the elevation of the antenna to the parameter provided by the antenna
   aiming tool (above). Remember this is the up and down angle. Many antennas
   will have an elevation scale on the back of the dish that you can use to set
   the approximate elevation.
3. Set the LNB polarization to the parameter provided by the antenna aiming
   tool. This involves rotating the LNB. There is typically a polarization
   rotation scale on the LNB or the LNB mounting bracket.
4. Set the azimuth angle to the value obtained from the aiming tool.

Initially, you can leave the screws that control the azimuth angle loose, so
that you can adjust the azimuth for pointing. You can do the same for elevation
and polarization, but the azimuth is typically easier to sweep as an initial
pointing attempt.

## Achieve Signal Lock

Assuming that the receiver is properly configured and connected (refer to
[instructions](../README.md#software-and-setup-configuration) otherwise), your
next step is to adjust the antenna pointing until the receiver can lock to
Blockstream Satellite's signal. Please note that this is expected to be the most
time-consuming part of the setup process, especially when pointing an antenna
for the first time. Do note that a single degree shifted on the dish represents
a change of thousands of kilometers over the geosynchronous orbit.

The process will be easier with a laptop than can be watched while moving the
antenna. If you are not able to watch the computer from the antenna site, you’ll
need two people: one to move the antenna and one to monitor the computer.

The instructions for locking to Blockstream Satellite's signal vary depending on
your hardware. Please refer to the specific instructions of your chosen
demodulator:

- [TBS5927](#tbs5927)
- [Novra S400](#novra-s400)
- [SDR-based](#sdr-based)


### TBS5927

Assuming the TBS5927 is launched after executing the command that follows (see
[launch instructions](tbs.md#launch)), you can check the logs that are printed
on the terminal.

```
blocksat-cli usb launch
```

Initially, while the TBS5927 is still searching for the Blockstream Satellite
signal, it will print only the `RF` metrics as follows:

![TBS 5927 Searching](img/tbs5927_searching.png?raw=true "TBS 5927 Searching")

At this point, you can expect at least that the signal level (after `Signal=`)
is sufficiently high, provided that the LNB is really on and connected. This is
because the LNB amplifies the signal received over satellite and feeds a
reasonably high signal level into the demodulator. You can expect the level to
be higher than -69 dBm, which is the minimum supported level specified for the
TBS5927, and not higher than -23 dBm, which is TBS5927's maximum.

If your TBS5927 is indeed still printing logs like the ones above (i.e. is not
locked yet), you should try to make adjustments to the antenna pointing. For
example, keep the elevation angle fixed and very slowly move the antenna side to
side (vary the azimuth angle). Alternatively, keep azimuth fixed and slowly vary
the elevation. Every time you make an adjustment, wait a few seconds and check
if the unit has found the signal in this position. If not, try another
adjustment and so on.

Once the demodulator finds a carrier, it will print a log as follows:

![TBS 5927 Carrier Found](img/tbs5927_carrier.png?raw=true "TBS 5927 Carrier Found")

Subsequently, it is expected to finally lock to the signal:

![TBS 5927 Locked - 8PSK](img/tbs5927_lock_8psk.png?raw=true "TBS 5927 Locked - 8PSK")

> NOTE: depending on the C/N level, at this point you may either see `MODULATION
> = PSK/8` (as in the above example) or, in case your C/N is lower, `MODULATION
> = QPSK`, as shown below. This distinction is due to the two streams that are
> concurrently broadcast over the Blockstream Satellite network. More
> information [later along this guide](#optimize-snr).

![TBS 5927 Locked - QPSK](img/tbs5927_lock_qpsk.png?raw=true "TBS 5927 Locked - QPSK")

At this point, you should check the carrier-to-noise ratio (C/N) parameter. The
higher the C/N value, the better. While the demodulator is locked, you can infer
that the pointing is already very close. Hence, now experiment with only gentle
adjustments to the pointing angles until you can maximize the C/N.

![TBS 5927 Locked - Improved C/N](img/tbs5927_lock_better_snr.png?raw=true "TBS 5927 Locked - Improved C/N")

Further instructions for the target C/N levels are presented in the [next
section](#optimize-snr).

### Novra S400

Assuming your Novra S400 receiver is configured and running (see
[instructions](s400.md)), you can now check that the unit is locked to
Blockstream Satellite's signal. This will be the case when the status LED in the
front panel of the unit is turned on. Assuming you have connected the LNB to
input RF1, then Status 1 will be lit when the unit is locked.

Alternatively, you can check the [S400's web
UI](s400.md#s400s-web-user-interface-ui). At the top of the page, there is a
panel with *Status*, *Lock* and *LNB* indicators. The *LNB* indicator should be
green when the S400 is properly supplying power to the LNB. Assuming you have
connected the LNB to input RF1, then the **RF1 Lock** indicator will be green
when the unit is locked.

![S400 Searching](img/s400_searching.png?raw=true "S400 Searching")

If the S400 is **not** locked yet, as depicted above (RF1 Lock indicator off),
you should try to make adjustments to the antenna pointing. For example, keep
the elevation angle fixed and very slowly move the antenna side to side (vary
the azimuth angle). Alternatively, keep azimuth fixed and slowly vary the
elevation. Every time you make an adjustment, wait a few seconds and check if
the S400 locks to the signal in this position. If not, try another adjustment
and so on.

![S400 Locked](img/s400_locked.png?raw=true "S400 Locked")

Once the S400 finally locks, as depicted above, you can try to maximize the
carrier-to-noise ratio (C/N) parameter. You can see this parameter on page
`Interfaces > RF1`, under *RF1 Detailed Status*. The example below shows an
initial C/N level of 3.9 dB:

![S400 RF Status](img/s400_rf_status.png?raw=true "S400 RF Status")

At this point, since the S400 is already locked, you should experiment with very
subtle adjustments to the pointing angles until you can maximize the C/N. The
higher the C/N, the better. The following example shows an example result, where
after improving the dish pointing the C/N level became approximately 3 dB
better:

![S400 RF Improved](img/s400_rf_status_better_snr.png?raw=true "S400 RF Improved")

See further instructions for the target C/N levels in the [next
section](#optimize-snr).

In terms of signal level, once the unit is locked, you can see the *signal
strength* also under *RF1 Detailed Status* of page `Interfaces > RF1`. The
signal strength that is fed to the S400 is expected to be within -65 dBm to -25
dBm.

### SDR-based

Assuming your SDR-based receiver is properly configured and running (see
[instructions](sdr.md)), you should now check that it can receive and lock to
Blockstream Satellite's signal.

It is helpful to break this in two steps: visualization using `gqrx` and locking
using the actual receiver application. In the first step, you should launch
`gqrx` (check gqrx [configuration instructions](sdr.md#configuration)). Then,
click the start icon on gqrx ("Start DSP Processing") and see if you can
recognize the Blockstream Satellite signal. Ideally, you would see a flat level
spanning a frequency band (in the horizontal axis) of approximately 1 MHz. Here
is an example:

![Signal visible on Gqrx](img/gqrx-offset.png?raw=true "Signal visible on Gqrx")

Note that in this case gqrx is configured to a center frequency of 12066.9 MHz,
and there is indeed a visible signal band of approximately 1 MHz. However, this
band is offset from the center, being located instead around 12066.6 MHz. This
is perfectly acceptable, since LNBs introduce frequency offset. With that, we
know that the dish is reasonably well pointed already, and that in this
particular setup there is a frequency offset around -300 kHz. If the center
frequency is re-configured to 12066.6 MHz, then we can see the 1 MHz band well
centered, like so:

![Signal centered on Gqrx](img/gqrx-centered.png?raw=true "Signal centered on Gqrx")

If you can't find the signal, you should try to make adjustments to the antenna
pointing. For example, keep the elevation angle fixed and very slowly move the
antenna side to side (vary the azimuth angle). Alternatively, keep azimuth fixed
and slowly vary the elevation. Every time you make an adjustment, check if the
signal band becomes visible in gqrx. If not, try another adjustment and so on.

> NOTE:
>
> If you see two similar signal bands near each other, try to identify which one
> is more likely to be the Blockstream Satellite signal. The correct signal
> should span a flat level of 1 MHz, with 100 kHz of roll-off on each side (our
> roll-off factor is 0.2). If the two signal bands are close to 1 MHz, please
> take note of the center frequency of both bands and try them both in the next
> steps.
>
> Furthermore, please note that in some cases not only there are similar signal
> bands on the same satellite, but also different satellites with similar bands.

Once you finally find the signal in gqrx, you can proceed to running the actual
receiver application. The next step is to try to lock the signal using the
receiver application. As explained in the [SDR guide](sdr.md#running), you can
start it with:

```
blocksat-cli sdr
```

For pointing, however, it is useful to run it in GUI mode, which will then open
up some real-time plots. Run:

```
blocksat-cli sdr --gui
```

At this point, before proceeding, it is helpful to inspect whether the gain is
well configured. Check the preprocessed (iq) plot. If it looks like the one
below, where the points are heavily scattered all around the two dimensions, it
is likely that the gain is too high. In this case, you can run with a lower gain
specified using option `-g`, like so:

![Pre-processed IQ](img/leandvb-pre-processed-iq.png?raw=true "Pre-processed IQ")

```
blocksat-cli sdr -g [gain]
```

The default gain is 30, and you can then experiment with lower values.

The IQ points should form a more compact cloud of points, such as the one below:

![Pre-processed IQ w/ lower Rx gain](img/leandvb-pre-processed-iq2.png?raw=true "Pre-processed IQ w/ lower Rx gain")

More information is available in [Section 9.2 of the leandvb application's
user guide](http://www.pabr.org/radio/leandvb/leandvb.en.html).

Next, observe the spectrum plots. The spectrum plot shows the central band
limits in red lines, and hence in the example that follows the signal presents
the frequency offset of roughly -300 kHz that we already knew about (from gqrx):

![Leandvb spectrum w/ offset signal](img/leandvb-spectrum-offset.png?raw=true "Leandvb spectrum w/ offset signal")

> NOTE: each LNB introduces a unique frequency offset, which also varies over
> time. The value of -300 kHz above was specific to the setup that was used to
> acquire the figures shown in this guide. Your offset will be different.

To correct the known offset, you can run with option `--derotate`, as follows:

```
blocksat-cli sdr -g [gain] --derotate [freq_offset]
```

where `freq_offset` represents the offset in kHz that you want to correct. With
that, the preprocessed spectrum plot should be reasonably centered, as follows:

![Leandvb spectrum w/ centered signal](img/leandvb-spectrum-centered.png?raw=true "Leandvb spectrum w/ centered signal")

At this point, if the antenna pointing is already reasonably good, you might see
the "PLS cstln" plot, showing four visible clouds:

![PLS symbols](img/leandvb-pls-syms.png?raw=true "PLS symbols")

This indicates the receiver application is locked to Blockstream Satellite
signal. Note that, the more compact the four clouds of points are in this plot
(around the white `+` marker), generally the better the signal quality.

If you cannot see the PLS symbols nor the *timeline plot*, it means you are not
locked to the signal yet. You can troubleshoot further in debug mode, by running
like so (with argument `-d`):

```
blocksat-cli sdr -g [gain] --derotate [freq_offset] --gui -d
```

If you see the following logs continuously being printed in the console, it
means you are not locked to the signal yet.

```
DETECT
PROBE
```

When a lock is acquired, while running in debug mode (with option `-d`), you
will see the following log printed to the console:

```
LOCKED
```

And after that you will start to see several underscores `_` printed
consecutively as indicators of successful data reception. The reception
indicator can be one of the three indicators that follow, and they are printed
only in debug mode (again, option `-d`). Also, you should see periodic `*
bitrate_monitor` logs.

```
Output:
  '_': S2 frame received without errors
  '.': error-corrected S2 frame
  '!': S2 frame with remaining errors
```

If you are not able to lock to the signal, you should try further adjustments to
the antenna.  Assuming you have identified the signal on gqrx before, you can
infer that the pointing is already very close and, therefore, only subtle
adjustments are required at this point in order for the signal quality to become
sufficient for locking. Try fine adjustments until you are able to get a lock on
the receiver application.

Finally, once you are locked, you can still try to improve the signal
quality. There are a few ways in which you can obtain an indication of signal
quality. One way is to look at the timeline plot, like the one below:

![leandvb timeline metrics](img/leandvb-timeline.png?raw=true "leandvb timeline metrics")

The higher the value of the modulation error ratio (MER) printed on the top left
corner, the better. Alternatively, you can inspect MER values directly from the
console in non-GUI mode. To do so, run with option `-dd` (debug level 2), as
follows:

```
blocksat-cli sdr -g [gain] --derotate [freq_offset] -dd
```

As a result, you should see a large amount of logs including the MER information
in dB. For example, logs like the ones below, where for example the MER is of
8.0 dB in the first line.

```
PLS: mc=12, sf=0, pilots=1 ( 0/90)  8.0 dB sr+6 fs=30
modcod 12 size 0 rejected
PLS: mc=12, sf=0, pilots=1 ( 0/90)  8.3 dB sr-6 fs=33
modcod 12 size 0 rejected
PLS: mc= 1, sf=0, pilots=1 ( 0/90)  9.2 dB sr+0 fs=45
PLS: mc=12, sf=0, pilots=1 ( 0/90)  8.4 dB sr+0 fs=72
modcod 12 size 0 rejected
PLS: mc=12, sf=0, pilots=1 ( 0/90)  8.9 dB sr+0 fs=43
modcod 12 size 0 rejected
PLS: mc= 1, sf=0, pilots=1 ( 0/90)  8.0 dB sr-4 fs=37
PLS: mc=12, sf=0, pilots=1 ( 0/90)  8.3 dB sr+0 fs=58
```

To optimize the MER, you can try very fine adjustments to all three pointing
parameters. Typically it is easier to let two of them be fixed and try adjusting
only one of them at a time. Try to get a sense of the best MER values you can
get and then set the dish pointing fixed to the best direction.

## Optimize SNR

Blockstream Satellite's signal is composed by two multiplexed streams, one of
which requires higher signal quality to be decoded than the other. The two
streams are summarized next:

| Stream          | Throughput | Minimum SNR | Recommended SNR | Purpose       |
|-----------------|------------|-------------|-----------------|---------------|
| Low-throughput  | ~64 kbps   | -1.24 dB    | 3 dB            | Repeats the past 24h of blocks and keeps receiver nodes in sync  |
| High-throughput | ~1.5 Mbps  | 6.62 dB     | 7.5 dB          | Broadcasts the entire blockchain and keeps receiver nodes in sync with lower latency |

As explained in the [hardware guide](hardware.md#satellite-dish), it may only be
feasible to receive the high-throughput stream with a dish of 90 cm or higher.

There are several related indicators of SNR and the measurement you will have
access to depends on your demodulator. You can compare the recommended SNR in
the above table to any of the following (related) metrics that you can read from
the demodulator:

- C/N (carrier-to-noise ratio)
- Es/No
- MER

For example, if using an SDR setup, you will see MER measurements and it is
recommended to have at least 7.5 dB of MER for reliable reception of the
high-throughput stream.

Note that, regardless of SNR, the USB and standalone demodulators will
continuously try to receive both high and low-throughput streams. For example,
if you start with insufficient SNR for the high-throughput stream, but at some
point the SNR improves and becomes sufficient, then the demodulator will start
to get high-throughput packets. This holds only for the TBS 5927 and the Novra
S400 demodulators. In contrast, this is **not currently possible** in the SDR
setup. In the SDR setup, you will need to specify which stream you want to try
receiving, as explained in the [SDR Guide](sdr.md#running).

## Next Steps

Well done. Your receiver is properly set-up and you are now ready to run the
Bitcoin Satellite application receiving data via the Blockstream Satellite
Network. Please refer to the [Bitcoin Satellite guide](bitcoin.md) for further
instructions.

