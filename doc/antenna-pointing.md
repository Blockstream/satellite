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
    - [Find the Satellite and Lock the Signal](#find-the-satellite-and-lock-the-signal)
        - [TBS5927](#tbs5927)
        - [Novra S400](#novra-s400)
        - [SDR-based](#sdr-based)
        - [Satellite Finder](#satellite-finder)
    - [Optimize the SNR](#optimize-the-snr)
    - [Next Steps](#next-steps)

<!-- markdown-toc end -->

## Mount the Antenna

First of all, you should obtain the pointing angles that are required for your
specific location using our [**Dish Alignment
Tool**](https://blockstream.com/satellite/#satellite-resources).

After entering your address or latitude/longitude, the tool will give you the
three parameters that are explained next:

- **Azimuth**: the side to side angle of your antenna. 0 degrees refers to
  North, 90 degrees points to East, 180 degrees to South and 270 degrees to
  West.

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
or smartphone app (e.g., Satellite Pointer for
[Android](https://play.google.com/store/apps/details?id=com.tda.satpointer&hl=pt_BR)
and [iOS](https://apps.apple.com/br/app/satellite-pointer/id994565490)) to
identify the direction. Ensure that there are no obstacles such as trees or
buildings in the path between your antenna location and the area of the sky that
your antenna must point to. It is important that you have clear line of sight to
that area of the sky.

**IMPORTANT:** If using a compass app on a smartphone, make sure to configure
the app such that it displays **true north**, instead of the **magnetic
north**. This is because the azimuth angle that is provided by our dish
alignment tool refers to true north. Also, if using an ordinary compass, or a
compass-based satellite finder, please make sure to convert the true azimuth
obtained from the dish alignment tool into magnetic azimuth. You can obtain both
true and magnetic azimuth angles using a tool such as [Dish
Pointer](https://www.dishpointer.com).

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

## Find the Satellite and Lock the Signal

Assuming that the receiver is properly configured and connected (refer to
[instructions](../README.md#software-and-setup-configuration) otherwise), your
next step is to find the satellite. You will adjust the antenna pointing until
the receiver can lock to Blockstream Satellite's signal. Please note that this
is expected to be the most time-consuming part of the setup process, especially
when pointing an antenna for the first time. Do note that a single degree
shifted on the dish represents a change of thousands of kilometers over the
geosynchronous orbit.

The process will be easier with a laptop than can be watched while moving the
antenna. If you are not able to watch the computer from the antenna site, you’ll
need two people: one to move the antenna and one to monitor the computer.

The instructions for locking to Blockstream Satellite's signal vary depending on
your hardware. Please refer to the specific instructions of your chosen
receiver:

- [TBS5927](#tbs5927)
- [Novra S400](#novra-s400)
- [SDR-based](#sdr-based)

As an alternative, if you prefer, you can try using a satellite finder prior to
locking the receiver. This is generally more useful for the TBS5927 and S400
receivers. In contrast, for SDR-based receivers, the SDR signal visualization
tools are sufficient for pointing. Refer to the instructions at the [satellite
finder section](#satellite-finder).


### TBS5927

Assuming the TBS5927 is launched after executing the command that follows (see
[launch instructions](tbs.md#launch)), you can check the logs that are printed
on the terminal.

```
blocksat-cli usb launch
```

Initially, while the TBS5927 is still searching for the Blockstream Satellite
signal, it will print only the signal level, on lines starting with `RF`, as
follows:

```
RF     (0x01) Signal= -48,41dBm
RF     (0x01) Signal= -48,28dBm
RF     (0x01) Signal= -47,70dBm
RF     (0x01) Signal= -48,05dBm
          Layer A: Signal= 52,05%
```

At this point, you can expect at least that the signal level is sufficiently
high, provided that the LNB is really on and connected. This is because the LNB
amplifies the signal received over satellite and feeds a reasonably high signal
level into the receiver. You can expect the level to be higher than -69 dBm,
which is the minimum supported level specified for the TBS5927, and not higher
than -23 dBm, which is TBS5927's maximum.

If your TBS5927 is indeed still printing logs like the ones above (i.e., not
locked yet), you should try to make adjustments to the antenna pointing. For
example, keep the elevation angle fixed and very slowly move the antenna side to
side (vary the azimuth angle). Alternatively, keep azimuth fixed and slowly vary
the elevation. Every time you make an adjustment, wait a few seconds and check
if the unit has found the signal in this position. If not, try another
adjustment and so on.

Once the receiver finds a carrier, it will print a line starting with `Carrier`,
as follows:

```
Carrier(0x03) Signal= -48,08dBm
          Layer A: Signal= 52,05%
```

Subsequently, it is expected to finally lock to the signal, in which case it
prints out the signal parameters, as follows:

```
Got parameters for DVBS2:
FREQUENCY = 12066900
INVERSION = AUTO
SYMBOL_RATE = 1000000
INNER_FEC = 2/3
MODULATION = PSK/8
PILOT = ON
ROLLOFF = AUTO
POLARIZATION = HORIZONTAL
```

> NOTE: depending on the C/N level, at this point you may either see `MODULATION
> = PSK/8` (as in the above example) or, in case your C/N is lower, `MODULATION
> = QPSK`, as shown below. This distinction is due to the two streams that are
> concurrently broadcast over the Blockstream Satellite network. More
> information [later along this guide](#optimize-the-snr).

```
Got parameters for DVBS2:
FREQUENCY = 12066900
INVERSION = AUTO
SYMBOL_RATE = 1000000
INNER_FEC = 1/2
MODULATION = QPSK
PILOT = ON
ROLLOFF = AUTO
POLARIZATION = HORIZONTAL
```

From this point on, the application will continuously print (and refresh) a line
starting with word `Lock`, which indicates the receiver is locked to the
signal. This line include receiver metrics of interest. For example:

```
Lock   (0x1f) Signal= -47,73dBm C/N= 7,20dB postBER= 0
          Layer A: Signal= 53,05% C/N= 36,04%
```

You should pay special attention to the carrier-to-noise ratio (C/N)
parameter. The higher the C/N value, the better. Given that the receiver is
locked already, you can infer that the antenna pointing is already very close to
the optimal position. At this point, you can experiment with gentle adjustments
to the pointing angles until you can maximize the C/N.

Further instructions for the target C/N levels are presented in the [next
section](#optimize-the-snr).

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
section](#optimize-the-snr).

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
> take note of the center frequency of both bands and try both of them in the
> next steps until you get a lock.
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
below, where the points are strongly scattered all around the two dimensions, it
is likely that the gain is too high. In this case, you can run with a lower gain
specified using option `-g`, like so:

![Pre-processed IQ](img/leandvb-pre-processed-iq.png?raw=true "Pre-processed IQ")

```
blocksat-cli sdr -g [gain]
```

The default gain is 40, and you can then experiment with lower values.

The IQ points should form a more compact cloud of points, such as the one below:

![Pre-processed IQ w/ lower Rx gain](img/leandvb-pre-processed-iq2.png?raw=true "Pre-processed IQ w/ lower Rx gain")

More information is available in [Section 9.2 of the leandvb application's
user guide](http://www.pabr.org/radio/leandvb/leandvb.en.html).

Next, observe the spectrum plots. The spectrum plot shows the limits of the
central band in red lines. In the example that follows, the signal presents the
frequency offset of roughly -300 kHz that we already knew about (from our
observation on gqrx):

![Leandvb spectrum w/ offset signal](img/leandvb-spectrum-offset.png?raw=true "Leandvb spectrum w/ offset signal")

> NOTE: each LNB introduces a unique frequency offset, which also varies over
> time. The value of -300 kHz above was specific to the setup that was used to
> acquire the figures that are shown in this guide. Your frequency offset will
> be different.

To correct the known offset, you can run with option `--derotate`, as follows:

```
blocksat-cli sdr -g [gain] --derotate [freq_offset]
```

where `freq_offset` represents the offset in kHz that you want to correct. With
that, the preprocessed spectrum plot should be reasonably centered, as follows:

![Leandvb spectrum w/ centered signal](img/leandvb-spectrum-centered.png?raw=true "Leandvb spectrum w/ centered signal")

At this point, if the antenna pointing is already reasonably good, you might see
the "PLS cstln" plot, particularly showing four visible clouds:

![PLS symbols](img/leandvb-pls-syms.png?raw=true "PLS symbols")

This plot indicates that the receiver application is locked to the Blockstream
Satellite signal. Note that, the more compact the four clouds of points are in
this plot (around the white `+` marker), generally the better the signal
quality.

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

After that, you should start seeing several underscores `_` printed
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

With this command, you should see logs including the MER information in dB. For
example, logs like the ones below, where the MER is of 6.4 dB in the first line.

```
PLS: mc=13, sf=0, pilots=1 llr=474  7.6 dB sr-6 fs=62  6.4 dB
modcod 13 size 0 rejected
PLS: mc=13, sf=0, pilots=1 llr=454  7.4 dB sr+0 fs=47  6.3 dB
modcod 13 size 0 rejected
PLS: mc=13, sf=0, pilots=1 llr=512  7.5 dB sr+0 fs=53  6.3 dB
modcod 13 size 0 rejected
PLS: mc=13, sf=0, pilots=1 llr=461  7.2 dB sr+0 fs=51  6.8 dB
modcod 13 size 0 rejected
PLS: mc=13, sf=0, pilots=1 llr=458  6.6 dB sr+0 fs=48  6.6 dB
modcod 13 size 0 rejected
PLS: mc=13, sf=0, pilots=1 llr=439  6.5 dB sr+0 fs=44  5.9 dB
modcod 13 size 0 rejected
PLS: mc=13, sf=0, pilots=1 llr=508  7.2 dB sr+0 fs=53  6.2 dB
modcod 13 size 0 rejected
```

To optimize the MER, you can try very fine adjustments to all three pointing
parameters. Typically it is easier to let two of them be fixed and try adjusting
only one of them at a time. Try to get a sense of the best MER values you can
get and then set the dish pointing fixed to the best direction.

### Satellite Finder

Prior to locking the satellite receiver (TBS5927, S400, or SDR receiver), you
can try to find the satellite using a satellite finder.

A satellite finder usually has two connections: one to the LNB (typically
labeled as *satellite*) and one to the receiver. The receiver connection is used
to provide power to the finder. However, some finder models come with an
alternative power supply, in which case the connection to the receiver is
unnecessary.

In terms of functionality, some finders only measure the signal level, whereas
other models are capable of demodulating signals and locking to them. We will
consider both of them next.

A basic finder model (such as the `SF-95DR`) does not have signal parameter
configurations and can only measure signal level. In this case, connect the
finder inline between the receiver (TBS5927 or S400) and the LNB. Run the
receiver normally, so that the receiver can power up the finder. Then, try to
point the antenna until you get good signal levels on the finder. Once you do
achieve good signal strength on the finder, check if the receiver is locked too,
following the instructions for your receiver:

- [TBS5927](#tbs5927)
- [Novra S400](#novra-s400)
- [SDR-based](#sdr-based)

Next, if you are using a satellite finder that supports DVB-S2 demodulation, you
can configure it to lock to a free-to-air (FTA) TV signal. The rationale is that
the Blockstream Satellite signal runs in a DVB-S2 mode (called VCM - *variable
coding and modulation*) that is not supported by most satellite finders that
support DVB-S2. Thus, a TV signal in the same satellite can be used as a
reference, to make sure that your antenna is pointed to the correct satellite.

For such models of satellite finders (with DVB-S2 demodulation), we recommend
that you run the finder standalone rather than inline with the receiver. In this
case, you would connect the `satellite` port of the finder directly to the LNB,
provided that the finder has a power supply. If your finder can only be powered
by a receiver, then connect to your receiver normally such that the finder is
inline between the receiver and the LNB.

Next, define the parameters of the reference FTA TV signal. There are lists of
signals available on the web. For example, refer to the following lists, for the
satellites that are used by the Blockstream Satellite network:
- [Galaxy 18](https://www.lyngsat.com/Galaxy-18.html)
- [Eutelsat 113](https://www.lyngsat.com/Eutelsat-113-West-A.html)
- [Telstar 18N](https://www.lyngsat.com/Telstar-11N.html)
- [Telstar 18V](https://www.lyngsat.com/Telstar-18-Vantage.html)

After choosing a TV signal, you need to configure the finder with the signal
parameters. Typically, you will need to set the following:

- LO Frequency: the frequency of your LNB. If you are unsure, run the CLI
  command below:

  ```
  blocksat-cli instructions
  ```

  The LO frequency will be displayed on the first page.

- Downlink Frequency: the downlink frequency of the FTA TV signal of choice.
- Symbol rate: the symbol rate of the FTA TV signal of choice. This is often
  abbreviated as `SR`. So, for example, on [this
  list](https://www.lyngsat.com/Eutelsat-113-West-A.html), you see a column
  labeled `SR-FEC`, which stands for the *symbol rate* and *FEC*.
- Polarity: whether the signal is horizontal or vertically polarized. This is
  usually informed next to the downlink frequency with letter `V` (for vertical)
  or `H` (for horizontal).
- 22 kHz: this refers to a 22 kHz signal that can be used to change the LO
  frequency of a Universal LNB. See [the notes regarding Universal
  LNBs](hardware.md#universal-lnb). You only need to enable this option if you
  are using a Universal LNB and if the FTA TV signal you selected is in [Ku high
  band](frequency.md). Otherwise, leave it disabled.

For example, the following table provides information of an FTA TV signal.

| Frequency | SR-FEC   |
|-----------|----------|
|  	11974 V | 3330-2/3 |

In this case, the signal has the following properties:
- The downlink frequency is 11974 MHz.
- The symbol rate is 3330 ksymbols/second (or kbaud).
- The downlink signal is vertically polarized (see the `V` next to the downlink
  frequency).

After you configure the satellite finder, you will typically be presented with a
signal strength and (or) quality indicator. Try to point your antenna until you
can maximize these levels.

Once you lock to the FTA TV signal on the satellite finder, you can infer that
you are pointed to the correct satellite. At this point, you can disconnect the
satellite finder and connect the LNB/antenna back to your receiver. Your next
step is to verify that your receiver can lock to the Blockstream Satellite
signal. Thus, follow the specific instructions of your receiver:

- [TBS5927](#tbs5927)
- [Novra S400](#novra-s400)
- [SDR-based](#sdr-based)


## Optimize the SNR

Blockstream Satellite's signal is composed by two multiplexed streams, one of
which requires higher signal quality to be decoded than the other. The two
streams are summarized next:

| Stream          | Throughput | Minimum SNR | Recommended SNR | Purpose       |
|-----------------|------------|-------------|-----------------|---------------|
| Low-throughput  | ~96 kbps   | 1 dB        | 4 dB            | Repeats the past 24h of blocks and keeps receiver nodes in sync  |
| High-throughput | ~1.55 Mbps | 6.62 dB     | 9 dB            | Broadcasts the entire blockchain and keeps receiver nodes in sync with lower latency |

As explained in the [hardware guide](hardware.md#satellite-dish), it may only be
feasible to receive the high-throughput stream with a dish of 90 cm or higher.

There are several related indicators of SNR and the measurement you will have
access to depends on your receiver. You can compare the recommended SNR in the
above table to any of the following (related) metrics that you can read from the
receiver:

- C/N (carrier-to-noise ratio)
- Es/No
- MER

For example, if using an SDR setup, you will see MER measurements and it is
recommended to have at least 7.5 dB of MER for reliable reception of the
high-throughput stream.

Note that, regardless of SNR, the USB and standalone receivers will continuously
try to receive both high and low-throughput streams. For example, if you start
with insufficient SNR for the high-throughput stream, but at some point the SNR
improves and becomes sufficient, then the receiver will start to get
high-throughput packets. This holds only for the TBS 5927 and the Novra S400
receivers. In contrast, this is **not currently possible** in the SDR setup. In
the SDR setup, you will need to specify which stream you want to try receiving,
as explained in the [SDR Guide](sdr.md#running).

## Next Steps

Well done. Your receiver is properly set-up and you are now ready to run the
Bitcoin Satellite application receiving data via the Blockstream Satellite
Network. Please refer to the [Bitcoin Satellite guide](bitcoin.md) for further
instructions.

