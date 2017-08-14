#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 <+YOU OR YOUR COMPANY+>.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from gnuradio import filter
from frame_sync_cc import frame_sync_cc
import numpy

class qa_frame_sync_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        pmf_vals = (
            0.1,
            -0.1,
            0.55,
            0.1,
            0.1,
            1,
            0.1,
            -0.1,
            .55,
            0.1,
            -0.1,
            0.1,
            0.1,
            0.1,
            -0.1,
            0.1)
        sym_in = (
            1.0 + 1.0j,
            -1.0 - 1.0j,
            1.0 - 1.0j,
            1.0 + 1.0j,
            -1.0 + 1.0j,
            1.0 - 1.0j,
            1 + 1j,
            2 + 2j,
            3 + 3j,
            4 + 4j,
            5 + 5j,
            0 + 0j,
            0 + 0j,
            0 + 0j,
            0 + 0j,
            0 + 0j
            )
        expected_peak_est = (0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0)
        expected_sym_out = (
            1 + 1j,
            2 + 2j,
            3 + 3j,
            4 + 4j,
            5 + 5j
            )
        pmf_src = blocks.vector_source_f (pmf_vals)
        sym_src = blocks.vector_source_c (sym_in)
        threshold = 0.5
        barker_len = 3
        barker_rep = 2
        payload_len = 5
        n_init_peaks = 0
        equalize = 1
        frame_synchronizer = frame_sync_cc (threshold, barker_len, barker_rep, payload_len, n_init_peaks, equalize)
        peak_snk = blocks.vector_sink_b ()
        sym_snk = blocks.vector_sink_c ()
        self.tb.connect (sym_src, (frame_synchronizer, 0))
        self.tb.connect (pmf_src, (frame_synchronizer, 1))
        self.tb.connect ((frame_synchronizer, 0), sym_snk)
        self.tb.connect ((frame_synchronizer, 1), peak_snk)
        self.tb.run ()
        res_sym_out = sym_snk.data ()
        res_peak_out = peak_snk.data ()

        self.assertFloatTuplesAlmostEqual (expected_sym_out, res_sym_out, 6)
        # self.assertFloatTuplesAlmostEqual (expected_peak_est, res_peak_out, 6)

    def test_002_t (self):

        # Configuration of the following setup
        barker_len = 13
        n_barker_rep = 8
        preamble_len = barker_len * n_barker_rep
        payload_len = 20
        threshold = 0.5
        n_init_peaks = 0
        equalize = 1

        # Symbol sequence containing the barker preamble and some payload data
        sym_in =  [-1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,
        -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 +
        1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,
        -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 -
        1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,
        -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 + 1.0000j, -1.0000 -
        1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,
        1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 -
        1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,
        1.0000 + 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 -
        1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,
        -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 -
        1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,
        1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 +
        1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,
        -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 -
        1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 + 1.0000j,
        -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 -
        1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,
        -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 -
        1.0000j,  1.0000 + 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,
        -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,  1.0000 +
        1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,
        -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 +
        1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,
        1.0000 + 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 -
        1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,
        -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 +
        1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,
        -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, 0.5000 +
        0.5000j,  2.0000 + 2.0000j,  3.0000 + 3.0000j,  4.0000 + 4.0000j,
        5.0000 + 5.0000j,  6.0000 + 6.0000j,  7.0000 + 7.0000j,  8.0000 +
        8.0000j,  9.0000 + 9.0000j, 10.0000 +10.0000j, 11.0000 +11.0000j,
        12.0000 +12.0000j, 13.0000 +13.0000j, 14.0000 +14.0000j, 15.0000
        +15.0000j, 16.0000 +16.0000j, 17.0000 +17.0000j, 18.0000 +18.0000j,
        19.0000 +19.0000j, 20.0000 +20.0000j]
        sym_src = blocks.vector_source_c (sym_in)

        # Normalized PMF Filter
        preamble_mached_filter = filter.interp_fir_filter_ccc(1, ( [-0.0048 +
        0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j,  0.0048 -
        0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,  0.0048 -
        0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j,
        -0.0048 + 0.0048j,  0.0048 - 0.0048j,  0.0048 - 0.0048j, -0.0048 +
        0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j, -0.0048 +
        0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,
        0.0048 - 0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j, -0.0048 +
        0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,
        -0.0048 + 0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j,  0.0048 -
        0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j,
        0.0048 - 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 +
        0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,
        0.0048 - 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j, -0.0048 +
        0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j,  0.0048 - 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 +
        0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j,
        -0.0048 + 0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j, -0.0048 +
        0.0048j,  0.0048 - 0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 +
        0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j,
        0.0048 - 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,  0.0048 -
        0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 +
        0.0048j,  0.0048 - 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j,  0.0048 - 0.0048j,  0.0048 -
        0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j, -0.0048 + 0.0048j,
        -0.0048 + 0.0048j, -0.0048 + 0.0048j] ))
        preamble_mached_filter.declare_sample_delay(0)

        # Block for conversion of the complex PMF output to magnitude:
        pmf_complex_to_mag = blocks.complex_to_mag(1)

        # Frame synchronizer
        frame_synchronizer = frame_sync_cc(threshold, barker_len, n_barker_rep, payload_len, n_init_peaks, equalize)

        # Sinks
        peak_snk = blocks.vector_sink_b ()
        sym_snk = blocks.vector_sink_c ()

        ############ Exepected Output

        expected_sym_out = [ 0.5000 +0.5000j,  2.0000 + 2.0000j,
        3.0000 + 3.0000j, 4.0000 + 4.0000j, 5.0000 + 5.0000j,  6.0000 + 6.0000j,
        7.0000 + 7.0000j]
        ############ Connections

        # Symbol input goes to both the PMF and the Frame Synchronizer directly
        self.tb.connect (sym_src, (preamble_mached_filter, 0))
        self.tb.connect (sym_src, (frame_synchronizer, 0))

        # Scalar multiplier connects to the "complex to mag" block
        self.tb.connect (preamble_mached_filter, pmf_complex_to_mag)

        # Magnitude goes to the second input of the Frame synchronizer
        self.tb.connect (pmf_complex_to_mag, (frame_synchronizer, 1))

        # Frame synchronizer outputs:
        self.tb.connect ((frame_synchronizer, 0), sym_snk)
        self.tb.connect ((frame_synchronizer, 1), peak_snk)
        self.tb.run ()
        res_sym_out = sym_snk.data ()
        res_peak_out = peak_snk.data ()

        self.assertFloatTuplesAlmostEqual (expected_sym_out, res_sym_out, 1)

if __name__ == '__main__':
    gr_unittest.run(qa_frame_sync_cc, "qa_frame_sync_cc.xml")
