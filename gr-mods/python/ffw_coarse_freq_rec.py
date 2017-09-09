# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Coarse Freq. Rec.
# Description: FFT-Based Feedforward Coarse Carrier Frequency Recovery
# Generated: Sun Sep  3 15:05:19 2017
##################################################

from gnuradio import blocks
from gnuradio import gr
from gnuradio.fft import logpwrfft
from gnuradio.filter import firdes
from math import *
import mods
import threading
import time


class ffw_coarse_freq_rec(gr.hier_block2):

    def __init__(self, alpha=0.001, fft_len=512, samp_rate=32e3):
        gr.hier_block2.__init__(
            self, "Coarse Freq. Rec.",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
            gr.io_signaturev(3, 3, [gr.sizeof_float*fft_len, gr.sizeof_float*1, gr.sizeof_gr_complex*1]),
        )

        ##################################################
        # Parameters
        ##################################################
        self.alpha = alpha
        self.fft_len = fft_len
        self.samp_rate = samp_rate

        ##################################################
        # Variables
        ##################################################
        self.fft_peak_bin_index = fft_peak_bin_index = 0

        ##################################################
        # Blocks
        ##################################################
        self.probe = blocks.probe_signal_f()

        def _fft_peak_bin_index_probe():
            while True:
                val = self.probe.level()
                try:
                    self.set_fft_peak_bin_index(val)
                except AttributeError:
                    pass
                time.sleep(1.0 / (100))
        _fft_peak_bin_index_thread = threading.Thread(target=_fft_peak_bin_index_probe)
        _fft_peak_bin_index_thread.daemon = True
        _fft_peak_bin_index_thread.start()

        self.mods_nco_cc_0 = mods.nco_cc((2*pi*fft_peak_bin_index/fft_len)/4)
        self.mods_exponentiate_const_cci_0 = mods.exponentiate_const_cci(4, 1)
        self.logpwrfft_x_0 = logpwrfft.logpwrfft_c(
        	sample_rate=samp_rate,
        	fft_size=fft_len,
        	ref_scale=2,
        	frame_rate=samp_rate/fft_len,
        	avg_alpha=alpha,
        	average=True,
        )
        self.blocks_short_to_float_0 = blocks.short_to_float(1, 1)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_short*1)
        self.blocks_argmax_xx_0 = blocks.argmax_fs(fft_len)
        self.mods_wrap_fft_index_0 = mods.wrap_fft_index(fft_len)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_argmax_xx_0, 1), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_argmax_xx_0, 0), (self.mods_wrap_fft_index_0, 0))
        self.connect((self.mods_wrap_fft_index_0, 0), (self.blocks_short_to_float_0, 0))
        self.connect((self.mods_exponentiate_const_cci_0, 0), (self.logpwrfft_x_0, 0))
        self.connect((self.blocks_short_to_float_0, 0), (self, 1))
        self.connect((self.blocks_short_to_float_0, 0), (self.probe, 0))
        self.connect((self.logpwrfft_x_0, 0), (self.blocks_argmax_xx_0, 0))
        self.connect((self.logpwrfft_x_0, 0), (self, 0))
        self.connect((self.mods_nco_cc_0, 0), (self, 2))
        self.connect((self, 0), (self.mods_exponentiate_const_cci_0, 0))
        self.connect((self, 0), (self.mods_nco_cc_0, 0))

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.logpwrfft_x_0.set_avg_alpha(self.alpha)

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self.mods_nco_cc_0.set_phase_inc((2*pi*self.fft_peak_bin_index/self.fft_len)/4)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.logpwrfft_x_0.set_sample_rate(self.samp_rate)

    def get_fft_peak_bin_index(self):
        return self.fft_peak_bin_index

    def set_fft_peak_bin_index(self, fft_peak_bin_index):
        self.fft_peak_bin_index = fft_peak_bin_index
        self.mods_nco_cc_0.set_phase_inc((2*pi*self.fft_peak_bin_index/self.fft_len)/4)
