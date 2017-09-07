# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Frame Synchronizer
# Description: Correlation-based frame synchronization
# Generated: Thu Sep  7 13:50:39 2017
##################################################

from gnuradio import blocks
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
from math import *
import mods
import numpy


class frame_synchronizer(gr.hier_block2):

    def __init__(self, M=4, equalize=0, fix_phase=0, fw_preamble=2, payload_size=1, pmf_peak_threshold=0.7, preamble_size=1, preamble_syms=[0+0j, 0 +0j], verbosity=0):
        gr.hier_block2.__init__(
            self, "Frame Synchronizer",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
            gr.io_signaturev(5, 5, [gr.sizeof_gr_complex*1, gr.sizeof_char*1, gr.sizeof_float*1, gr.sizeof_float*1, gr.sizeof_gr_complex*1]),
        )

        ##################################################
        # Parameters
        ##################################################
        self.M = M
        self.equalize = equalize
        self.fix_phase = fix_phase
        self.fw_preamble = fw_preamble
        self.payload_size = payload_size
        self.pmf_peak_threshold = pmf_peak_threshold
        self.preamble_size = preamble_size
        self.preamble_syms = preamble_syms
        self.verbosity = verbosity

        ##################################################
        # Blocks
        ##################################################
        self.mods_frame_sync_fast_0 = mods.frame_sync_fast(pmf_peak_threshold, preamble_size, payload_size, equalize, fix_phase, M, fw_preamble, verbosity)
        self.interp_fir_filter_xxx_0_0 = filter.interp_fir_filter_fff(1, ( numpy.ones(preamble_size)))
        self.interp_fir_filter_xxx_0_0.declare_sample_delay(0)
        self.interp_fir_filter_xxx_0 = filter.interp_fir_filter_ccc(1, ( numpy.flipud(numpy.conj(preamble_syms))))
        self.interp_fir_filter_xxx_0.declare_sample_delay(0)
        self.blocks_multiply_xx_0 = blocks.multiply_vff(1)
        self.blocks_multiply_const_vxx_1_1 = blocks.multiply_const_vcc((1.0/sqrt(2), ))
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_vcc((1.0/(preamble_size*sqrt(2)), ))
        self.blocks_divide_xx_1 = blocks.divide_ff(1)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_1 = blocks.complex_to_mag(1)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_1, 0), (self.blocks_divide_xx_1, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.interp_fir_filter_xxx_0_0, 0))
        self.connect((self.blocks_divide_xx_1, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_divide_xx_1, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.mods_frame_sync_fast_0, 2))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self, 4))
        self.connect((self.blocks_multiply_const_vxx_1_1, 0), (self.blocks_complex_to_mag_1, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.mods_frame_sync_fast_0, 1))
        self.connect((self.blocks_multiply_xx_0, 0), (self, 3))
        self.connect((self.interp_fir_filter_xxx_0, 0), (self.blocks_multiply_const_vxx_1, 0))
        self.connect((self.interp_fir_filter_xxx_0, 0), (self.blocks_multiply_const_vxx_1_1, 0))
        self.connect((self.interp_fir_filter_xxx_0_0, 0), (self.blocks_divide_xx_1, 1))
        self.connect((self.mods_frame_sync_fast_0, 0), (self, 0))
        self.connect((self.mods_frame_sync_fast_0, 1), (self, 1))
        self.connect((self.mods_frame_sync_fast_0, 2), (self, 2))
        self.connect((self, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self, 0), (self.interp_fir_filter_xxx_0, 0))
        self.connect((self, 0), (self.mods_frame_sync_fast_0, 0))

    def get_M(self):
        return self.M

    def set_M(self, M):
        self.M = M

    def get_equalize(self):
        return self.equalize

    def set_equalize(self, equalize):
        self.equalize = equalize

    def get_fix_phase(self):
        return self.fix_phase

    def set_fix_phase(self, fix_phase):
        self.fix_phase = fix_phase

    def get_fw_preamble(self):
        return self.fw_preamble

    def set_fw_preamble(self, fw_preamble):
        self.fw_preamble = fw_preamble

    def get_payload_size(self):
        return self.payload_size

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size

    def get_pmf_peak_threshold(self):
        return self.pmf_peak_threshold

    def set_pmf_peak_threshold(self, pmf_peak_threshold):
        self.pmf_peak_threshold = pmf_peak_threshold

    def get_preamble_size(self):
        return self.preamble_size

    def set_preamble_size(self, preamble_size):
        self.preamble_size = preamble_size
        self.interp_fir_filter_xxx_0_0.set_taps(( numpy.ones(self.preamble_size)))
        self.blocks_multiply_const_vxx_1.set_k((1.0/(self.preamble_size*sqrt(2)), ))

    def get_preamble_syms(self):
        return self.preamble_syms

    def set_preamble_syms(self, preamble_syms):
        self.preamble_syms = preamble_syms
        self.interp_fir_filter_xxx_0.set_taps(( numpy.flipud(numpy.conj(self.preamble_syms))))

    def get_verbosity(self):
        return self.verbosity

    def set_verbosity(self, verbosity):
        self.verbosity = verbosity
