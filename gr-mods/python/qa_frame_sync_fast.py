#!/usr/bin/env python2
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
import mods_swig as mods

class qa_frame_sync_fast (gr_unittest.TestCase):

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
        equalize = 0
        frame_synchronizer = mods.frame_sync_fast (threshold, barker_len, barker_rep, payload_len, n_init_peaks, equalize)
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

if __name__ == '__main__':
    gr_unittest.run(qa_frame_sync_fast, "qa_frame_sync_fast.xml")
