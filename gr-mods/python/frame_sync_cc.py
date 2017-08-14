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

import numpy
from gnuradio import gr

class frame_sync_cc(gr.basic_block):
    """
    docstring for block frame_sync_cc
    """
    def __init__(self, threshold, barker_len, barker_rep, payload_len, n_init_peaks, equalize):
        self.threshold = threshold
        self.barker_len = barker_len
        self.preamble_len = barker_rep*barker_len
        self.payload_len = payload_len
        self.n_init_peaks = n_init_peaks
        gr.basic_block.__init__(self,
            name="frame_sync_cc",
            in_sig=[numpy.complex64,numpy.float32],
            out_sig=[numpy.complex64,numpy.uint8])
        self.i_sym = 0
        self.i_after_peak = 0
        self.last_peak = 0
        self.i_last_peak = 0
        self.penultimate_peak = 0
        self.i_penultimate_peak = 0
        self.state = 0 # 0 - waiting, 1 - data payload
        self.peak_cnt = 0
        self.delay_line = numpy.zeros(barker_len)
        self.eq_gain = 1
        self.equalize = equalize

    def forecast(self, noutput_items, ninput_items_required):
        #setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):
            #no = noutput_items * ((self.payload_len + self.preamble_len)/self.payload_len)
            ninput_items_required[i] = noutput_items

    def general_work(self, input_items, output_items):
        rx_sym_in = input_items[0]
        mag_pmf = input_items[1]
        rx_sym_out = output_items[0]
        is_peak = output_items[1]

        #print('Work [ in0:', len(rx_sym_in),'in1:',len(mag_pmf), 'out0',len(rx_sym_out), 'out1:', len(is_peak))

        n_consumed = 0;
        n_produced = 0;
        # Search for the main peak among the PMF output stream
        for i in range(0, len(rx_sym_out)):
            # Keep a running counter of symbol indexes
            self.i_sym += 1
            n_consumed += 1

            # Output the last symbol within the delay line
            last_d_line_sym = self.delay_line[-1]

            # Shift the delay line and put the input symbol in
            self.delay_line = numpy.concatenate(([rx_sym_in[i]], self.delay_line[0:-1]))

            # Check if the current PMF sample corresponds to the main peak
            is_peak[i] = self.is_preamble_main_peak(mag_pmf[i])

            state = self.process_state(is_peak[i])

            # Output the equalized symbol only when in the data payload
            if (state == 1):
                if (self.equalize == 1):
                    rx_sym_out[n_produced] = self.eq_gain * last_d_line_sym
                else:
                    rx_sym_out[n_produced] = last_d_line_sym
                n_produced += 1;

        # Always consume the same amount from both inputs
        self.consume_each(n_consumed)
        return n_produced

    def is_preamble_main_peak(self, pmf_sample):
        # If the current PMF output sample is above the threshold it is deemed
        # as a peak, but not necessarily the main peak.
        if (pmf_sample > self.threshold):
            # The main peak is between two small peaks for the Barker
            # preamble. Since the two previous peaks are stored in memory,
            # the current peak can be compared to these two. If the last
            # peak is greater than both the penultimate peak and the
            # current peak, then it can be inferred that the last one was
            # the one we are looking for.
            if (self.last_peak > pmf_sample and self.last_peak > self.penultimate_peak):
                # This seems to be the correct peak. Finally, as a sanity
                # check verify that the distance between the peaks matches
                # with the Barker code periodicity:

                expected_i_last_peak = self.i_sym - self.barker_len
                expected_i_penultimate_peak = self.i_sym - 2*self.barker_len
                if ((self.i_last_peak == expected_i_last_peak) and
                (self.i_penultimate_peak == expected_i_penultimate_peak)):
                    is_peak = 1
                    self.eq_gain = 1.0 / self.last_peak
                else:
                    is_peak = 0
            else:
                is_peak = 0

            # Now, update the two previous peaks stored in memory
            self.penultimate_peak = self.last_peak
            self.i_penultimate_peak = self.i_last_peak
            self.last_peak = pmf_sample
            self.i_last_peak = self.i_sym
        else:
            is_peak = 0

        return is_peak

    def process_state(self, is_peak):
            # Keep the block processing input while the flow-graph is on startup or
            # initial synchronization peaks
            # This will prevent the flow-graph from starve while the block still do not
            # found the correlation peak
            if (self.peak_cnt < self.n_init_peaks):
                state = 1;
                if (is_peak):
                    self.peak_cnt += 1
            # Is the current symbol still within the data payload?
            elif (self.i_after_peak > 0 and self.i_after_peak <= self.payload_len):
                self.i_after_peak += 1
                state = 1
            # The initial
            # Otherwise, keep waiting for the peak
            else:
                # Trigger the acquisition of the preamble when a peak occurs in the PMF
                if (is_peak):
                    self.i_after_peak = 1;
                    state = 0
                else:
                    self.i_after_peak = 0;
                    state = 0

            return state
