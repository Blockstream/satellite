---
parent: Hardware guide
nav_order: 4
---

# SDR Setup



This section summarizes the items you need to purchase for a software-defined radio (SDR) setup. Note you will need to source these independently, as no kits are available for the SDR setup on [Blockstream Store](https://store.blockstream.com/product/blockstream-satellite-base-station/). To avoid misunderstandings, we recommend checking out the [hardware components](hardware-components.md) page with further details about the parts, especially the section about [SDR-specific components](hardware-components.md#specific-parts-for-the-sdr-setup).

In the shopping lists below, we distinguish between the Ku and C bands and also between the Ku low and high bands. The low and high parts of the Ku band have different frequency ranges (see the [frequency guide](frequency.md#signal-bands)) that determine the appropriate SDR interface.

If you are covered by a Ku high band beam (G18 and E113), consider purchasing the following items:

1. [RTL-SDR model RTL2832U with R820T2 tuner](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-smartee-sdr.html).
2. DIRECTV 21 Volt SWM Power Inserter.
3. Male-to-male SMA cable.
4. SMA to F adapter (SMA Female, F male).
5. Ku-band satellite dish.
6. MK1-PLL LNB.
7. Ku band LNB mounting bracket.
8. RG6 coaxial cable.

Alternatively, if you are covered by a Ku low band beam (T11N or T18V Ku), please consider the following items:

1. [RTL-SDR model RTL2832U with E4000 tuner](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-smart-xtr-sdr.html).
2. DIRECTV 21 Volt SWM Power Inserter.
3. Male-to-male SMA cable.
4. SMA to F adapter (SMA Female, F male).
5. Ku-band satellite dish.
6. GEOSATpro UL1PLL Universal Ku band PLL LNB.
7. Ku band LNB mounting bracket.
8. RG6 coaxial cable.

> **Note:** The items that differ between the Ku low and high-band lists are the RTL-SDR model (R820T2 vs. E4000 tuner) and the LNB model (MK1-PLL vs. GEOSATpro UL1PLL).

Next, if you would like to use a flat-panel antenna instead of a conventional dish, please consider doing so only if you are covered by a Ku low-band beam (T11N or T18V Ku). In that case, you can purchase the following items:

1. [RTL-SDR model RTL2832U with E4000 tuner](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-smart-xtr-sdr.html).
2. DIRECTV 21 Volt SWM Power Inserter.
3. Male-to-male SMA cable.
4. SMA to F adapter (SMA Female, F male).
5. [Selfsat H50D](https://s3.ap-northeast-2.amazonaws.com/logicsquare-seoul/a64d56aa-567b-4053-bc84-12c2e58e46a6/H50DSeries%28no1-4%29Spec_sheet.pdf) flat panel antenna.
6. RG6 coaxial cable.

> **Note:** The flat panel antenna only works in the Ku band. Also, specifically with SDR receivers, the flat panel only works in the low part of the Ku band. Thus, please make sure you are covered by a Ku low-band beam before purchasing it.

Lastly, if you are covered by a C-band beam (T18V C), please consider the following items:

1. [RTL-SDR model RTL2832U with R820T2 tuner](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-smartee-sdr.html).
2. DIRECTV 21 Volt SWM Power Inserter.
3. Male-to-male SMA cable.
4. SMA to F adapter (SMA Female, F male).
5. C-band satellite dish.
6. [Titanium C1-PLL C Band PLL LNB](https://www.titaniumsatellite.com/c1wpll).
7. [Titanium CS1 Conical Scalar Kit](https://www.titaniumsatellite.com/cs1) for using an [offset dish](https://en.wikipedia.org/wiki/Offset_dish_antenna).
8. C Band LNB mounting bracket.
9. RG6 coaxial cable.

Again, please refer to the [hardware components page](hardware-components.md#specific-parts-for-the-sdr-setup) to understand these requirements.

---

Prev: [Base Station Kit](base-station.md) - Next: [Hardware Components](hardware-components.md)