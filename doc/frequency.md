# Satellite Frequency Bands

Blockstream Satellite operates in Ku high band, Ku low band and C band,
depending on region. Ku high band is used in North America and South America. Ku
low band is used in Africa and Europe. C band is used in Asia-Pacific region.

| Band         | Frequency Range   |
|--------------|-------------------|
| C band       | 3.7 GHZ - 4.2 GHz |
| Ku low band  | 10.7 to 11.7 GHz  |
| Ku high band | 11.7 to 12.75 GHz |

You can always use antennas designed for higher frequencies. For example, an
antenna designed for Ka band will work for Ku bands and C band, as it is
designed for higher frequencies than the ones used by Blockstream
Satellite. However, a C band antenna will not work for Ku bands, as it is
designed for lower frequencies.

The following table summarizes the transmission bands of the satellites we use:

| Satellite          | Band    |
|--------------------|---------|
| Galaxy 18          | Ku High |
| Eutelsat 113       | Ku High |
| Telstar 11N Africa | Ku Low  |
| Telstar 11N Europe | Ku Low  |
| Telstar 18V        | C       |

## <a name="l_band"></a> L-band frequency

The demodulator or SDR device receives the signal on a frequency band that is
already different than the frequency received from the satellite. This is the
so-called L-band frequency. The LNB downconverts the signal from the satellite
band (Ku or C) to L-band, and so the demodulator receives the signal in L-band.

The L-band frequency depends on the frequency of the satellite covering your
location and the frequency of your LNB's local oscillator (LO) frequency, so it
is specific to your setup. Also, the computation differs for C band and Ku band.

For Ku band (either high or low), the L-band frequency is given as follows:

```
l_band_freq_ku = satellite_frequency - lnb_lo_frequency
```

Meanwhile, for C band, it is computed as:

```
l_band_freq_c = lnb_lo_frequency - satellite_frequency
```

To find your satellite's frequency, first go to
[blockstream.com/satellite](https://blockstream.com/satellite/#satellite_network-coverage)
and check which one is your satellite (covering your location). Then, find the
frequency and the corresponding band of the satellite in the table that follows.

| Satellite          | Band    | Frequency    |
|--------------------|---------|--------------|
| Galaxy 18          | Ku High | 12016.92 MHz |
| Eutelsat 113       | Ku High | 12026.15 MHz |
| Telstar 11N Africa | Ku Low  | 11476.75 MHz |
| Telstar 11N Europe | Ku Low  | 11504.02 MHz |
| Telstar 18V        | C       | 4057.5 MHz   |

For the LNB's LO frequency, check the product's information. The typical LNB LO
frequencies for the bands of interest are summarized below:

|               Band |          C |     Ku Low |    Ku High |    Ku High |
| ------------------ | ---------- | ---------- | ---------- | ---------- |
|       LO Frequency |   5.15 GHz |   9.75 GHz |  10.60 GHz |  10.75 GHz |

Now, pick the correct formula for your signal band and compute the
frequency. For example, if your LNB has an LO frequency of 10750 MHz and you're
connecting to Eutelsat 113 at 12026.15 MHz (Ku high band), your L-band frequency
becomes 1,276,150,000 Hz, that is:

```
1,276,150,000 Hz       = 12,026,150,000 Hz   - 10,750,000,000 Hz
   ^                          ^                     ^
   ^                          ^                     ^
l_band_freq_ku = satellite_frequency - lnb_lo_frequency
```

The following table summarizes some L-band frequencies (in Hz) considering
typical LNB LO frequencies:

|       LO Frequency |   5.15 GHz |   9.75 GHz |  10.60 GHz |  10.75 GHz |
| ------------------ | ---------- | ---------- | ---------- | ---------- |
|          Galaxy 18 |            |            | 1416920000 | 1266920000 |
|       Eutelsat 113 |            |            | 1426150000 | 1276150000 |
| Telstar 11N Africa |            | 1726750000 |            |            |
| Telstar 11N Europe |            | 1754020000 |            |            |
|        Telstar 18V | 1092500000 |            |            |            |
