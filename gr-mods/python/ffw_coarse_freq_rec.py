# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Coarse Freq. Rec.
# Description: FFT-Based Feedforward Coarse Carrier Frequency Recovery
# Generated: Sat Sep 23 10:15:57 2017
##################################################

from gnuradio import blocks
from gnuradio import gr
from gnuradio.fft import logpwrfft
from gnuradio.filter import firdes
from math import *
import mods


class ffw_coarse_freq_rec(gr.hier_block2):

    def __init__(self, abs_cfo_threshold=1e6, alpha=0.001, fft_len=512, rf_center_freq=1e9, samp_rate=32e3):
        gr.hier_block2.__init__(
            self, "Coarse Freq. Rec.",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
            gr.io_signaturev(2, 2, [gr.sizeof_float*fft_len, gr.sizeof_float*1]),
        )

        ##################################################
        # Parameters
        ##################################################
        self.abs_cfo_threshold = abs_cfo_threshold
        self.alpha = alpha
        self.fft_len = fft_len
        self.rf_center_freq = rf_center_freq
        self.samp_rate = samp_rate

        ##################################################
        # Blocks
        ##################################################
        self.mods_wrap_fft_index_0 = mods.wrap_fft_index(fft_len)
        self.mods_runtime_cfo_ctrl_0 = mods.runtime_cfo_ctrl(7*int(1/alpha), abs_cfo_threshold, rf_center_freq)
        self.mods_exponentiate_const_cci_0 = mods.exponentiate_const_cci(4, 1)
        self.logpwrfft_x_0 = logpwrfft.logpwrfft_c(
        	sample_rate=samp_rate,
        	fft_size=fft_len,
        	ref_scale=2,
        	frame_rate=samp_rate/fft_len,
        	avg_alpha=alpha,
        	average=True,
        )
        self.blocks_sub_xx_0 = blocks.sub_ff(1)
        self.blocks_short_to_float_0 = blocks.short_to_float(1, 1)
        self.blocks_null_sink_1 = blocks.null_sink(gr.sizeof_float*1)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_short*1)
        self.blocks_multiply_xx_0 = blocks.multiply_vff(1)
        self.blocks_multiply_const_vxx_2 = blocks.multiply_const_vff((samp_rate/(fft_len*4), ))
        self.blocks_moving_average_xx_0_0 = blocks.moving_average_ff(int(1/alpha), 1.0/int(1/alpha), int(4/alpha))
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(int(1/alpha), 1.0/int(1/alpha), int(4/alpha))
        self.blocks_argmax_xx_0 = blocks.argmax_fs(fft_len)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_argmax_xx_0, 1), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_argmax_xx_0, 0), (self.mods_wrap_fft_index_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_sub_xx_0, 1))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.mods_runtime_cfo_ctrl_0, 1))
        self.connect((self.blocks_moving_average_xx_0_0, 0), (self.mods_runtime_cfo_ctrl_0, 2))
        self.connect((self.blocks_multiply_const_vxx_2, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_2, 0), (self.blocks_sub_xx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_2, 0), (self.mods_runtime_cfo_ctrl_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_moving_average_xx_0_0, 0))
        self.connect((self.blocks_short_to_float_0, 0), (self.blocks_multiply_const_vxx_2, 0))
        self.connect((self.blocks_sub_xx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_sub_xx_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.logpwrfft_x_0, 0), (self.blocks_argmax_xx_0, 0))
        self.connect((self.logpwrfft_x_0, 0), (self, 0))
        self.connect((self.mods_exponentiate_const_cci_0, 0), (self.logpwrfft_x_0, 0))
        self.connect((self.mods_runtime_cfo_ctrl_0, 1), (self.blocks_null_sink_1, 0))
        self.connect((self.mods_runtime_cfo_ctrl_0, 0), (self, 1))
        self.connect((self.mods_wrap_fft_index_0, 0), (self.blocks_short_to_float_0, 0))
        self.connect((self, 0), (self.mods_exponentiate_const_cci_0, 0))

    def get_abs_cfo_threshold(self):
        return self.abs_cfo_threshold

    def set_abs_cfo_threshold(self, abs_cfo_threshold):
        self.abs_cfo_threshold = abs_cfo_threshold

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.logpwrfft_x_0.set_avg_alpha(self.alpha)
        self.blocks_moving_average_xx_0_0.set_length_and_scale(int(1/self.alpha), 1.0/int(1/self.alpha))
        self.blocks_moving_average_xx_0.set_length_and_scale(int(1/self.alpha), 1.0/int(1/self.alpha))

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self.blocks_multiply_const_vxx_2.set_k((self.samp_rate/(self.fft_len*4), ))

    def get_rf_center_freq(self):
        return self.rf_center_freq

    def set_rf_center_freq(self, rf_center_freq):
        self.rf_center_freq = rf_center_freq

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.logpwrfft_x_0.set_sample_rate(self.samp_rate)
        self.blocks_multiply_const_vxx_2.set_k((self.samp_rate/(self.fft_len*4), ))
