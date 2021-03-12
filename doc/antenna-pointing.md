# Antenna Pointing

Aligning a satellite antenna is a precise procedure. Remember that the
satellites are over 35,000 km (22,000 mi) away. A tenth of a degree of error
will miss the satellite by more than 3500 km. Hence, this is likely the most
time-consuming step of the process. This page provides a step-by-step guide for
antenna alignment.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Antenna Pointing](#antenna-pointing)
    - [Mount the Antenna](#mount-the-antenna)
    - [Find the Satellite and Lock the Signal](#find-the-satellite-and-lock-the-signal)
    - [Optimize the SNR](#optimize-the-snr)
    - [Next Steps](#next-steps)
    - [Further Information](#further-information)
        - [Novra S400's User Interface](#novra-s400s-user-interface)
        - [Pointing with an SDR-based Receiver](#pointing-with-an-sdr-based-receiver)
        - [Pointing with a Satellite Finder](#pointing-with-a-satellite-finder)

<!-- markdown-toc end -->

## Mount the Antenna

First of all, you should obtain the pointing angles required for your specific
location using our [**Dish Alignment
Tool**](https://blockstream.com/satellite/#satellite-resources).

After entering your address or latitude/longitude, the tool will give you the
following parameters:

- **Azimuth**: the side-to-side angle of your antenna. 0 degrees refers to
  North, 90 degrees to East, 180 degrees to South, and 270 degrees to West.

- **Elevation**: the up and down adjustment of your antenna. The antenna aiming
  tool provides the number of degrees above the horizon to which your antenna
  must point. 0 degrees represents pointing at the horizon, and 90 degrees is
  pointing straight up.

- **Polarity**: determines the rotation of the LNB. It is the angle of the LNB
  within the LNB mounting bracket (or holder). Often this is referred to also as
  the LNB *rotational angle* or *LNB skew*.

The three angles are illustrated below:

Azimuth                                        |  Elevation                                           | Polarity                                                  |
:---------------------------------------------:|:----------------------------------------------------:|:---------------------------------------------------------:|
![Azimuth](img/azimuth.png?raw=true "Azimuth") | ![Elevation](img/elevation.png?raw=true "Elevation") | ![Polarity](img/lnb_polarization.png?raw=true "Polarity") |

Next, visually inspect the direction to which your antenna must point. Use a
compass or smartphone app (e.g., Satellite Pointer for
[Android](https://play.google.com/store/apps/details?id=com.tda.satpointer) and
[iOS](https://apps.apple.com/br/app/satellite-pointer/id994565490)) to identify
it. Ensure that there are no obstacles (like trees or buildings) between your
antenna and the target area in the sky. You must have a clear line of sight to
that area of the sky.

**IMPORTANT:** If using a compass app on a smartphone, make sure to configure
the app to display **true north** instead of the **magnetic north**. The azimuth
angle provided by our dish alignment tool refers to true north. Also, if using
an ordinary compass or a compass-based satellite finder, make sure to convert
the true azimuth obtained from the dish alignment tool into the magnetic
azimuth. You can get both the true and magnetic azimuth angles using a tool such
as the [Dish Pointer](https://www.dishpointer.com).

Next, install the satellite antenna according to the directions accompanying it,
or have it done professionally. If you install it yourself, proceed with the
following steps:

1. Certify that the pole on which the dish is mounted is entirely level.
2. Set the elevation of the antenna to the parameter provided by the antenna
   aiming tool (above). Many antennas will have an elevation scale on the back
   of the dish that you can use to set the approximate elevation.
3. Set the LNB polarization to the parameter provided by the antenna aiming
   tool. This involves rotating the LNB. There is typically a polarization
   rotation scale on the LNB or the LNB mounting bracket.
4. Set the azimuth angle to the value obtained from the aiming tool.


> Note: if using an [offset dish
> antenna](https://en.wikipedia.org/wiki/Offset_dish_antenna) (the most common
> dish type in Ku band), make sure to subtract the dish offset angle from the
> nominal elevation. You can check the offset angle in the dish
> specifications. For example, if the nominal elevation angle at your location
> is 20°, and your offset reflector has an offset angle of 25°, the resulting
> elevation becomes -5°. In this case, it will appear that the reflector is
> pointing down to the ground. In reality, however, the dish will be tilted
> correctly to receive the low-elevation signal at the offset focal point.

At this stage, you can leave the screws that control the azimuth angle slightly
loose so that you can adjust the azimuth for pointing. You can do the same for
elevation and polarization. Nevertheless, the azimuth is typically easier to
sweep as an initial pointing attempt.

## Find the Satellite and Lock the Signal

Assuming that the receiver is configured correctly and connected, your next step
is to find the satellite. You will adjust the antenna pointing until the
receiver can lock to the Blockstream Satellite signal. Please note that this is
likely the most time-consuming part of the setup process, especially when doing
it for the first time. As mentioned earlier, a single degree shifted on the dish
represents a change of thousands of kilometers over the geosynchronous orbit.

The process will be easier with a laptop than can be watched while moving the
antenna. If you cannot watch the computer, you’ll need two people: one to move
the antenna and one to monitor the computer.

To start, make sure that your receiver is running. Depending on your type of
receiver, this step involves one of the following commands:

- For the TBS 5927 USB ([Basic
Kit](https://store.blockstream.com/product/blockstream-satellite-basic-kit/))
Receiver: `blocksat-cli usb launch`.

- For the Novra S400 Standalone ([Pro
Kit](https://store.blockstream.com/product/blockstream-satellite-pro-kit/))
Receiver: `blocksat-cli standalone monitor` (see the [S400's
instructions](s400.md#monitoring)).

- For the SDR receiver: `blocksat-cli sdr`.

Next, you should monitor the receiver logs printed to the console. Initially,
while the antenna is not pointed correctly, the receiver will be unlocked. In
this case, the application will print logs like the following:

```
2020-10-23 14:26:14  Lock = False;
```

In this case, you should try to make adjustments to the antenna pointing. For
example, keep the elevation angle fixed and slowly move the antenna side to side
(vary the azimuth angle). Alternatively, keep the azimuth fixed and gradually
change the elevation. Every time you adjust an angle, wait a few seconds and
check if the receiver has found the signal in this position. If not, try another
adjustment and so on.

Once the receiver finds the signal, it will lock and print a line like the
following:

```
2020-10-23 14:32:25  Lock = True; Level = -47.98dBm; SNR = 11.30dB; BER = 0.00e+00;
```

From this point on, the application should remain locked.

You should pay special attention to the signal-to-noise ratio (SNR) parameter
printed on the console. The higher the SNR, the better. Given that the receiver
is already locked, you can infer that the antenna pointing is close to the
optimal position. Hence, at this point, you should experiment with gentle
adjustments to the pointing angles until you can maximize the SNR. The next
section discusses the target SNR levels.

Furthermore, you can check that the signal level is within acceptable
limits. The LNB amplifies the signal received over satellite and feeds a
reasonably high signal level into the receiver. However, the signal experiences
attenuation over the coaxial cable, connectors, and adapters. The expected
minimum and maximum signal levels are summarized below:

| Receiver   | Minimum Signal Level | Maximum Signal Level |
|------------|----------------------|----------------------|
| TBS 5927   | -69 dBm              | -23 dBm              |
| Novra S400 | -65 dBm              | -25 dBm              |

In the end, note that the antenna pointing procedure is entirely based on the
locking indicator printed to the console. Once you find the signal and the
receiver locks, the only remaining step is to [optimize the
SNR](#optimize-the-snr).

This approach works for all types of receivers. However, there are helpful
receiver-specific instructions for the pointing process, listed below:

- **Novra S400 Standalone receiver**: you can find various receiver status
metrics within the receiver's web interface. See [the
instructions](#novra-s400s-user-interface).
- **SDR receiver**: with an SDR receiver, you can visualize the signal spectrum
  and point the antenna more easily. See [the SDR
  instructions](#pointing-with-an-sdr-based-receiver).

Alternatively, you can try to point the antenna using a satellite finder. This
approach is generally more useful for the TBS5927 and S400 receivers. In
contrast, for SDR-based receivers, the [SDR signal visualization
tools](#pointing-with-an-sdr-based-receiver) are usually sufficient for
pointing. Refer to the instructions in the [satellite finder
section](#pointing-with-a-satellite-finder).

## Optimize the SNR

After the initial antenna pointing, we recommend experimenting with the pointing
until you achieve your maximum SNR. The SNR level should be at least 2.23
dB. However, we recommend trying to reach an SNR of 8 dB or higher in clear sky
conditions.

The SNR exceeding the minimum level determines the so-called link margin. For
example, if your receiver operates at 8.2 dB, it has a 6 dB margin relative to
the minimum SNR of roughly 2.2 dB. This margin means that your receiver can
tolerate up to 6 dB signal attenuation in case of bad weather (such as rain).

If your receiver is already locked, try gentle adjustments around the current
position and observe the SNR on the console. Stop once you find the pointing
that achieves the best SNR.

## Next Steps

Well done! You are now ready to run the Bitcoin Satellite application receiving
data via the Blockstream Satellite Network. Please refer to the [Bitcoin
Satellite guide](bitcoin.md) for further instructions.

## Further Information

### Novra S400's User Interface

The Novra S400 receiver features a [web-based user interface
(UI)](s400.md#s400s-web-user-interface-ui), which provides several receiver
metrics.

At the top, the web UI has an *LNB* indicator, which indicates whether the S400
is supplying power to the LNB. Furthermore, it shows whether the S400 is
locked. Assuming you have connected the LNB to input RF1, then the **RF1 Lock**
indicator will be green when the unit is locked.

![S400 Searching](img/s400_searching.png?raw=true "S400 Searching")

If the S400 is **not** locked yet, as depicted above (RF1 Lock indicator off),
you should [adjust the antenna
pointing](#find-the-satellite-and-lock-the-signal).

Once the S400 finally locks, the *RF1 Lock* indicator looks as follows:

![S400 Locked](img/s400_locked.png?raw=true "S400 Locked")

You can also find signal quality and status metrics on page `Interfaces > RF1`,
under *RF1 Detailed Status*. For example:

![S400 RF Status](img/s400_rf_status.png?raw=true "S400 RF Status")

Note that the carrier-to-noise ratio (C/N) parameter relates to the SNR
parameter that should be [optimized during the antenna
pointing](#optimize-the-snr).

### Pointing with an SDR-based Receiver

The SDR-based receiver offers additional visualization tools that are very
helpful for antenna pointing. With this receiver, the pointing procedure
consists of two steps:

1. Visualization using `gqrx`;
2. Locking using the actual receiver application.

In the first step, you should launch `gqrx` (check the gqrx [configuration
instructions](sdr.md#configuration)). Then, click the start icon ("Start DSP
Processing") and see if you can recognize the Blockstream Satellite
signal. Ideally, you would see a flat level spanning a frequency band (in the
horizontal axis) of approximately 1 MHz. Here is an example:

![Signal visible on Gqrx](img/gqrx-offset.png?raw=true "Signal visible on Gqrx")

With the [recommended gqrx configuration](sdr.md#configuration), gqrx should be
configured to the center frequency of the signal band (in this example, of
12066.9 MHz, where the red line is). However, the observed signal commonly is
offset from the nominal center frequency, given that LNBs introduce frequency
offset. In the above example, note the signal is around 12066.6 MHz, which means
a frequency offset of -300 kHz (to the left relative to the nominal center). If
gqrx's center frequency is re-configured to 12066.6 MHz, then we can see the 1
MHz band well centered, like so:

![Signal centered on Gqrx](img/gqrx-centered.png?raw=true "Signal centered on Gqrx")

If you cannot see the signal on gqrx, you should try to make adjustments to the
antenna pointing, as [described
earlier](#find-the-satellite-and-lock-the-signal).

> NOTE:
>
> If you see two similar signal bands near each other, try to identify which one
> is more likely to be the Blockstream Satellite signal. The correct signal
> should span a flat level of 1 MHz, with 100 kHz of roll-off on each side. If
> the two signal bands are close to 1 MHz, please take note of both center
> frequencies and try both of them in the next steps until you get a lock.
>
> Furthermore, please note that, in some cases, there can be similar signal
> bands among different (but nearby) satellites. In this case, you need to
> adjust the pointing until you get a lock.

Once you finally find the signal in gqrx, you can proceed to run the actual SDR
receiver application. As explained in the [SDR guide](sdr.md#running), you can
start it with:

```
blocksat-cli sdr
```

For pointing, however, it is helpful to run it in GUI mode, as follows:

```
blocksat-cli sdr --gui
```

At this point, before proceeding, we recommend inspecting whether the gain is
well configured. Check the preprocessed (iq) plot. If it looks like the one
below, with strongly scattered points around the two dimensions, the gain is
likely too high. In this case, you can run with a lower gain specified using
option `-g`, like so:

```
blocksat-cli sdr -g [gain]
```

![Pre-processed IQ](img/leandvb-pre-processed-iq.png?raw=true "Pre-processed IQ")

The default gain is 40, and you can then experiment with lower values.

The IQ points should form a more compact cloud of points, such as the one below:

![Pre-processed IQ w/ lower Rx gain](img/leandvb-pre-processed-iq2.png?raw=true "Pre-processed IQ w/ lower Rx gain")

More information is available in [Section 9.2 of the leandvb application's
user guide](http://www.pabr.org/radio/leandvb/leandvb.en.html).

Next, observe the spectrum plots. The spectrum plot shows the limits of the
central band in red lines. In the example that follows, the signal presents the
frequency offset of roughly -300 kHz that we already knew about from our
observation on gqrx:

![Leandvb spectrum w/ offset signal](img/leandvb-spectrum-offset.png?raw=true "Leandvb spectrum w/ offset signal")

> NOTE: each LNB introduces a unique frequency offset, which also varies over
> time. The above value of -300 kHz was specific to the example setup. Your
> frequency offset will be different.

To correct the known offset, you can run with option `--derotate`, as follows:

```
blocksat-cli sdr -g [gain] --derotate [freq_offset]
```

where `freq_offset` represents the offset in kHz that you want to correct.

With that, the preprocessed spectrum plot should be centered, as follows:

![Leandvb spectrum w/ centered signal](img/leandvb-spectrum-centered.png?raw=true "Leandvb spectrum w/ centered signal")

At this point, if the antenna pointing is already reasonably good, you might see
the "PLS cstln" plot showing four visible clouds:

![PLS symbols](img/leandvb-pls-syms.png?raw=true "PLS symbols")

This plot indicates that the receiver application is locked to the Blockstream
Satellite signal. Note that the more compact the four clouds of points are in
this plot (around the white `+` marker), the better the signal quality.

If you cannot see the "PLS cstln" plot, it means you are not locked to the
signal yet. You can troubleshoot further in debug mode by running like so (with
argument `-d`):

```
blocksat-cli sdr -g [gain] --derotate [freq_offset] --gui -d
```

If you see the following logs continuously printed in the console, it means you
are not locked to the signal yet:

```
DETECT
PROBE
```

When a lock is acquired, you will see the following log printed to the console:

```
LOCKED
```

After that, you should start seeing several underscores `_` printed
consecutively as indicators of successful data reception. The reception
indicator can be one of the three below:

- `_`: indicates a DVB-S2 frame received without errors.
- `.`: indicates an error-corrected DVB-S2 frame.
- `!`: indicates a DVB-S2 frame with remaining errors.

If you cannot lock to the signal, you should try further adjustments to the
antenna. Assuming you have identified the signal on gqrx before, you can infer
that the pointing is already very close. Therefore, only subtle adjustments are
required at this point.

Furthermore, if you cannot find the signal on gqrx, you can search for satellite
beacons instead. While the Blockstream Satellite signal is seen as a flat level
spanning approximately 1 MHz, a
[beacon](https://en.wikipedia.org/wiki/Radio_beacon#Space_and_satellite_radio_beacons)
is a very narrow signal seen as a narrow pulse (or peak) on gqrx. All you need
to do is change the frequency on gqrx to one of the beacon frequencies below:

| Satellite    | Beacons                                                                                                |
|--------------|--------------------------------------------------------------------------------------------------------|
| Galaxy 18    | 11701 MHz (Horizontal), 12195 MHz (Vertical)                                                           |
| Eutelsat 113 | 11701.5 MHz (Vertical), 12199 MHz (Horizontal)                                                         |
| Telstar 11N  | 11199.25 MHz (Vertical), 11699.50 MHz (Vertical), 11198.25 MHz (Horizontal), 11698.50 MHz (Horizontal) |
| Telstar 18V  | 3623 MHz (Vertical), 3625 MHz (Vertical), 4199 (Horizontal)                                            |

Make sure to select a beacon whose polarization matches your target signal
polarization, which you can check by running:

```
blocksat-cli cfg show
```

Once you find the beacon signal, make gentle adjustments to the pointing until
you can maximize the observed signal level. Then, change the frequency on gqrx
back to the original downlink frequency of interest (also printed by the above
command). You should be able to visualize the Blockstream Satellite signal now.

Ultimately, once the SDR receiver locks to the signal, you can still try to
improve the SNR. Observe the SNR values printed to the console and see if you
can get better values after subtle adjustments to the pointing.

In the end, once you are satisfied with the SNR (see the [target
levels](#optimize-the-snr)), you can monitor several aspects of your SDR
receiver. For example:

- To monitor the bitrate, run with option `--monitor-bitrate`.
- To monitor MPEG TS packet decoding errors, run with option `--monitor-ts`.
- For low-level debugging information, run with option `-dd`.

### Pointing with a Satellite Finder

In some cases, it is helpful to try pointing with a satellite finder instead of
using the satellite receiver directly.

A satellite finder usually has two connections: one to the LNB (typically
labeled *satellite*) and one to the receiver. The receiver connection is used to
provide power to the finder. However, some finders come with an alternative
power supply, in which case the connection to the receiver is unnecessary.

Some finders only measure the signal level, whereas other models can demodulate
signals and lock to them. Both approaches are considered in the sequel.

A basic finder model (such as the `SF-95DR` included on [satellite
kits](https://store.blockstream.com/product-category/satellite_kits/)) can only
measure signal level. In this case, connect the finder inline between the
receiver (TBS5927 or S400) and the LNB. Run the receiver normally so that the
receiver can power up the finder. Then, try to point the antenna until you get
adequate signal levels on the finder. Once you achieve good signal strength on
the finder, check if the receiver is locked ([see the previous
instructions](#find-the-satellite-and-lock-the-signal)).

Alternatively, if you are using a satellite finder that supports DVB-S2
demodulation, you can configure it to lock to the signal. To do so, you
typically need to configure the following signal parameters:

- Downlink frequency
- LNB local oscillator (LO) frequency
- Signal polarization

You can check the appropriate values by running:

```
blocksat-cli cfg show
```

Additionally, you will need to define:

- Symbol rate: set it to "1000 kbaud" (or "1000000 baud", or "1 Mbaud",
  depending on the units adopted by your finder).
- 22 kHz: enable only when using a Universal LNB and pointing to Galaxy 18 or
  Eutelsat 113 (i.e., when receiving in [Ku high
  band](frequency.md)). Otherwise, leave it disabled. See [the notes regarding
  Universal LNBs](hardware.md#universal-lnb).

After you configure the satellite finder, you will typically be presented with
signal strength and (or) quality indicators. Try to point your antenna until you
can maximize these levels.

Once you lock to the signal using the finder, check that your receiver can lock
too by following the [instructions presented
earlier](#find-the-satellite-and-lock-the-signal).

---

Prev: [Novra S400 Setup](s400.md) | [TBS5927 Setup](tbs.md) | [SDR Setup](sdr.md)
