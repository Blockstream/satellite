#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Rx
# Generated: Mon Aug 14 15:24:25 2017
##################################################

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt4 import Qt
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import *
from optparse import OptionParser
import framers
import mods
import numpy 
import numpy.matlib
import osmosdr
import pmt
import sys
import time


class rx(gr.top_block, Qt.QWidget):

    def __init__(self, freq=0, gain=0):
        gr.top_block.__init__(self, "Rx")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Rx")
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "rx")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())

        ##################################################
        # Parameters
        ##################################################
        self.freq = freq
        self.gain = gain

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 8
        self.excess_bw = excess_bw = 0.25
        self.target_samp_rate = target_samp_rate = sps*(200e3/(1 + excess_bw))
        
        self.qpsk_const = qpsk_const = digital.constellation_qpsk().base()
        
        self.dsp_rate = dsp_rate = 100e6
        self.const_choice = const_choice = "qpsk"
        
        self.bpsk_const = bpsk_const = digital.constellation_bpsk().base()
        
        self.barker_code_two_dim = barker_code_two_dim = [-1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j]
        self.barker_code_one_dim = barker_code_one_dim = sqrt(2)*numpy.real([-1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j])
        self.rrc_delay = rrc_delay = int(round(-44*excess_bw + 33))
        self.nfilts = nfilts = 32
        self.n_barker_rep = n_barker_rep = 10
        self.dec_factor = dec_factor = ceil(dsp_rate/target_samp_rate)
        self.constellation = constellation = qpsk_const if (const_choice=="qpsk") else bpsk_const
        self.barker_code = barker_code = barker_code_two_dim if (const_choice == "qpsk") else barker_code_one_dim
        self.preamble_syms = preamble_syms = numpy.matlib.repmat(barker_code, 1, n_barker_rep)[0]
        self.n_rrc_taps = n_rrc_taps = rrc_delay * int(sps*nfilts)
        self.n_codewords = n_codewords = 1
        self.even_dec_factor = even_dec_factor = dec_factor if (dec_factor % 1 == 1) else (dec_factor+1)
        self.const_order = const_order = pow(2,constellation.bits_per_symbol())
        self.codeword_len = codeword_len = 18444
        self.usrp_rx_addr = usrp_rx_addr = "192.168.10.2"
        self.samp_rate = samp_rate = dsp_rate/even_dec_factor
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(nfilts, nfilts*sps, 1.0, excess_bw, n_rrc_taps)
        self.rf_center_freq = rf_center_freq = 1428.4309e6
        self.preamble_size = preamble_size = len(preamble_syms)
        self.pmf_peak_threshold = pmf_peak_threshold = 0.6
        self.payload_size = payload_size = codeword_len*n_codewords/int(numpy.log2(const_order))
        self.dataword_len = dataword_len = 6144
        self.barker_len = barker_len = 13

        ##################################################
        # Blocks
        ##################################################
        self.tabs = Qt.QTabWidget()
        self.tabs_widget_0 = Qt.QWidget()
        self.tabs_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_0)
        self.tabs_grid_layout_0 = Qt.QGridLayout()
        self.tabs_layout_0.addLayout(self.tabs_grid_layout_0)
        self.tabs.addTab(self.tabs_widget_0, 'Tx Signal')
        self.tabs_widget_1 = Qt.QWidget()
        self.tabs_layout_1 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_1)
        self.tabs_grid_layout_1 = Qt.QGridLayout()
        self.tabs_layout_1.addLayout(self.tabs_grid_layout_1)
        self.tabs.addTab(self.tabs_widget_1, 'PMF Out')
        self.tabs_widget_2 = Qt.QWidget()
        self.tabs_layout_2 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_2)
        self.tabs_grid_layout_2 = Qt.QGridLayout()
        self.tabs_layout_2.addLayout(self.tabs_grid_layout_2)
        self.tabs.addTab(self.tabs_widget_2, 'Abs PMF Out')
        self.tabs_widget_3 = Qt.QWidget()
        self.tabs_layout_3 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_3)
        self.tabs_grid_layout_3 = Qt.QGridLayout()
        self.tabs_layout_3.addLayout(self.tabs_grid_layout_3)
        self.tabs.addTab(self.tabs_widget_3, 'FLL In')
        self.tabs_widget_4 = Qt.QWidget()
        self.tabs_layout_4 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_4)
        self.tabs_grid_layout_4 = Qt.QGridLayout()
        self.tabs_layout_4.addLayout(self.tabs_grid_layout_4)
        self.tabs.addTab(self.tabs_widget_4, 'FLL Out')
        self.tabs_widget_5 = Qt.QWidget()
        self.tabs_layout_5 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_5)
        self.tabs_grid_layout_5 = Qt.QGridLayout()
        self.tabs_layout_5.addLayout(self.tabs_grid_layout_5)
        self.tabs.addTab(self.tabs_widget_5, 'FLL State')
        self.tabs_widget_6 = Qt.QWidget()
        self.tabs_layout_6 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_6)
        self.tabs_grid_layout_6 = Qt.QGridLayout()
        self.tabs_layout_6.addLayout(self.tabs_grid_layout_6)
        self.tabs.addTab(self.tabs_widget_6, 'PFB Sync Out')
        self.tabs_widget_7 = Qt.QWidget()
        self.tabs_layout_7 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_7)
        self.tabs_grid_layout_7 = Qt.QGridLayout()
        self.tabs_layout_7.addLayout(self.tabs_grid_layout_7)
        self.tabs.addTab(self.tabs_widget_7, 'Costas State')
        self.tabs_widget_8 = Qt.QWidget()
        self.tabs_layout_8 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_8)
        self.tabs_grid_layout_8 = Qt.QGridLayout()
        self.tabs_layout_8.addLayout(self.tabs_grid_layout_8)
        self.tabs.addTab(self.tabs_widget_8, 'Demod Bits')
        self.tabs_widget_9 = Qt.QWidget()
        self.tabs_layout_9 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_9)
        self.tabs_grid_layout_9 = Qt.QGridLayout()
        self.tabs_layout_9.addLayout(self.tabs_grid_layout_9)
        self.tabs.addTab(self.tabs_widget_9, 'Costas  Sym Out')
        self.tabs_widget_10 = Qt.QWidget()
        self.tabs_layout_10 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_10)
        self.tabs_grid_layout_10 = Qt.QGridLayout()
        self.tabs_layout_10.addLayout(self.tabs_grid_layout_10)
        self.tabs.addTab(self.tabs_widget_10, 'Payload Symbols')
        self.top_layout.addWidget(self.tabs)
        self.rtlsdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + '' )
        self.rtlsdr_source_0.set_sample_rate(samp_rate)
        self.rtlsdr_source_0.set_center_freq(freq, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(gain, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna('', 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)
          
        self.mods_turbo_decoder_0 = mods.turbo_decoder(codeword_len, dataword_len)
        self.mods_frame_sync_fast_0 = mods.frame_sync_fast(pmf_peak_threshold, preamble_size, payload_size, 0, 1, 1, int(const_order))
        self.mods_fifo_async_sink_0 = mods.fifo_async_sink('/tmp/async_rx')
        self.interp_fir_filter_xxx_0_0 = filter.interp_fir_filter_fff(1, ( numpy.ones(n_barker_rep*barker_len)))
        self.interp_fir_filter_xxx_0_0.declare_sample_delay(0)
        self.interp_fir_filter_xxx_0 = filter.interp_fir_filter_ccc(1, ( numpy.flipud(numpy.conj(preamble_syms))))
        self.interp_fir_filter_xxx_0.declare_sample_delay(0)
        self.framers_gr_hdlc_deframer_b_0 = framers.gr_hdlc_deframer_b(0)
        self.digital_pfb_clock_sync_xxx_0 = digital.pfb_clock_sync_ccf(sps, 2*pi/50, (rrc_taps), nfilts, nfilts/2, pi/8, 1)
        self.digital_map_bb_0_0_0 = digital.map_bb(([1,- 1]))
        self.digital_fll_band_edge_cc_1 = digital.fll_band_edge_cc(sps, excess_bw, rrc_delay * int(sps) + 1, 0.002)
        self.digital_descrambler_bb_0 = digital.descrambler_bb(0x21, 0x7F, 16)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(2*pi/800, 2**constellation.bits_per_symbol(), False)
        self.digital_constellation_decoder_cb_0 = digital.constellation_decoder_cb(constellation.base())
        self.blocks_unpack_k_bits_bb_0 = blocks.unpack_k_bits_bb(constellation.bits_per_symbol())
        self.blocks_rms_xx_1 = blocks.rms_cf(0.0001)
        self.blocks_multiply_xx_0 = blocks.multiply_vff(1)
        self.blocks_multiply_const_vxx_1_1 = blocks.multiply_const_vcc((1.0/sqrt(2), ))
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_vcc((1.0/(preamble_size*sqrt(2)), ))
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_divide_xx_1 = blocks.divide_ff(1)
        self.blocks_divide_xx_0 = blocks.divide_cc(1)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_1 = blocks.complex_to_mag(1)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.framers_gr_hdlc_deframer_b_0, 'pdu'), (self.mods_fifo_async_sink_0, 'async_pdu'))    
        self.connect((self.blocks_complex_to_mag_1, 0), (self.blocks_divide_xx_1, 0))    
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.interp_fir_filter_xxx_0_0, 0))    
        self.connect((self.blocks_divide_xx_0, 0), (self.digital_fll_band_edge_cc_1, 0))    
        self.connect((self.blocks_divide_xx_1, 0), (self.blocks_multiply_xx_0, 0))    
        self.connect((self.blocks_divide_xx_1, 0), (self.blocks_multiply_xx_0, 1))    
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_divide_xx_0, 1))    
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.mods_frame_sync_fast_0, 2))    
        self.connect((self.blocks_multiply_const_vxx_1_1, 0), (self.blocks_complex_to_mag_1, 0))    
        self.connect((self.blocks_multiply_xx_0, 0), (self.mods_frame_sync_fast_0, 1))    
        self.connect((self.blocks_rms_xx_1, 0), (self.blocks_float_to_complex_0, 0))    
        self.connect((self.blocks_unpack_k_bits_bb_0, 0), (self.digital_map_bb_0_0_0, 0))    
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.blocks_unpack_k_bits_bb_0, 0))    
        self.connect((self.digital_costas_loop_cc_0, 0), (self.blocks_complex_to_mag_squared_0, 0))    
        self.connect((self.digital_costas_loop_cc_0, 0), (self.interp_fir_filter_xxx_0, 0))    
        self.connect((self.digital_costas_loop_cc_0, 0), (self.mods_frame_sync_fast_0, 0))    
        self.connect((self.digital_descrambler_bb_0, 0), (self.framers_gr_hdlc_deframer_b_0, 0))    
        self.connect((self.digital_fll_band_edge_cc_1, 0), (self.digital_pfb_clock_sync_xxx_0, 0))    
        self.connect((self.digital_map_bb_0_0_0, 0), (self.mods_turbo_decoder_0, 0))    
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0), (self.digital_costas_loop_cc_0, 0))    
        self.connect((self.interp_fir_filter_xxx_0, 0), (self.blocks_multiply_const_vxx_1, 0))    
        self.connect((self.interp_fir_filter_xxx_0, 0), (self.blocks_multiply_const_vxx_1_1, 0))    
        self.connect((self.interp_fir_filter_xxx_0_0, 0), (self.blocks_divide_xx_1, 1))    
        self.connect((self.mods_frame_sync_fast_0, 0), (self.digital_constellation_decoder_cb_0, 0))    
        self.connect((self.mods_turbo_decoder_0, 0), (self.digital_descrambler_bb_0, 0))    
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_divide_xx_0, 0))    
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_rms_xx_1, 0))    

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "rx")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.rtlsdr_source_0.set_center_freq(self.freq, 0)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.rtlsdr_source_0.set_gain(self.gain, 0)

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))
        self.set_target_samp_rate(self.sps*(200e3/(1 + self.excess_bw)))
        self.set_n_rrc_taps(self.rrc_delay * int(self.sps*self.nfilts))

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))
        self.set_rrc_delay(int(round(-44*self.excess_bw + 33)))
        self.set_target_samp_rate(self.sps*(200e3/(1 + self.excess_bw)))

    def get_target_samp_rate(self):
        return self.target_samp_rate

    def set_target_samp_rate(self, target_samp_rate):
        self.target_samp_rate = target_samp_rate
        self.set_dec_factor(ceil(self.dsp_rate/self.target_samp_rate))

    def get_qpsk_const(self):
        return self.qpsk_const

    def set_qpsk_const(self, qpsk_const):
        self.qpsk_const = qpsk_const
        self.set_constellation(self.qpsk_const if (self.const_choice=="qpsk") else self.bpsk_const)

    def get_dsp_rate(self):
        return self.dsp_rate

    def set_dsp_rate(self, dsp_rate):
        self.dsp_rate = dsp_rate
        self.set_samp_rate(self.dsp_rate/self.even_dec_factor)
        self.set_dec_factor(ceil(self.dsp_rate/self.target_samp_rate))

    def get_const_choice(self):
        return self.const_choice

    def set_const_choice(self, const_choice):
        self.const_choice = const_choice
        self.set_constellation(self.qpsk_const if (self.const_choice=="qpsk") else self.bpsk_const)
        self.set_barker_code(self.barker_code_two_dim if (self.const_choice == "qpsk") else self.barker_code_one_dim)

    def get_bpsk_const(self):
        return self.bpsk_const

    def set_bpsk_const(self, bpsk_const):
        self.bpsk_const = bpsk_const
        self.set_constellation(self.qpsk_const if (self.const_choice=="qpsk") else self.bpsk_const)

    def get_barker_code_two_dim(self):
        return self.barker_code_two_dim

    def set_barker_code_two_dim(self, barker_code_two_dim):
        self.barker_code_two_dim = barker_code_two_dim
        self.set_barker_code(self.barker_code_two_dim if (self.const_choice == "qpsk") else self.barker_code_one_dim)

    def get_barker_code_one_dim(self):
        return self.barker_code_one_dim

    def set_barker_code_one_dim(self, barker_code_one_dim):
        self.barker_code_one_dim = barker_code_one_dim
        self.set_barker_code(self.barker_code_two_dim if (self.const_choice == "qpsk") else self.barker_code_one_dim)

    def get_rrc_delay(self):
        return self.rrc_delay

    def set_rrc_delay(self, rrc_delay):
        self.rrc_delay = rrc_delay
        self.set_n_rrc_taps(self.rrc_delay * int(self.sps*self.nfilts))

    def get_nfilts(self):
        return self.nfilts

    def set_nfilts(self, nfilts):
        self.nfilts = nfilts
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))
        self.set_n_rrc_taps(self.rrc_delay * int(self.sps*self.nfilts))

    def get_n_barker_rep(self):
        return self.n_barker_rep

    def set_n_barker_rep(self, n_barker_rep):
        self.n_barker_rep = n_barker_rep
        self.set_preamble_syms(numpy.matlib.repmat(self.barker_code, 1, self.n_barker_rep)[0])
        self.interp_fir_filter_xxx_0_0.set_taps(( numpy.ones(self.n_barker_rep*self.barker_len)))

    def get_dec_factor(self):
        return self.dec_factor

    def set_dec_factor(self, dec_factor):
        self.dec_factor = dec_factor
        self.set_even_dec_factor(self.dec_factor if (self.dec_factor % 1 == 1) else (self.dec_factor+1))

    def get_constellation(self):
        return self.constellation

    def set_constellation(self, constellation):
        self.constellation = constellation

    def get_barker_code(self):
        return self.barker_code

    def set_barker_code(self, barker_code):
        self.barker_code = barker_code
        self.set_preamble_syms(numpy.matlib.repmat(self.barker_code, 1, self.n_barker_rep)[0])

    def get_preamble_syms(self):
        return self.preamble_syms

    def set_preamble_syms(self, preamble_syms):
        self.preamble_syms = preamble_syms
        self.set_preamble_size(len(self.preamble_syms))
        self.interp_fir_filter_xxx_0.set_taps(( numpy.flipud(numpy.conj(self.preamble_syms))))

    def get_n_rrc_taps(self):
        return self.n_rrc_taps

    def set_n_rrc_taps(self, n_rrc_taps):
        self.n_rrc_taps = n_rrc_taps
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))

    def get_n_codewords(self):
        return self.n_codewords

    def set_n_codewords(self, n_codewords):
        self.n_codewords = n_codewords
        self.set_payload_size(self.codeword_len*self.n_codewords/int(numpy.log2(self.const_order)))

    def get_even_dec_factor(self):
        return self.even_dec_factor

    def set_even_dec_factor(self, even_dec_factor):
        self.even_dec_factor = even_dec_factor
        self.set_samp_rate(self.dsp_rate/self.even_dec_factor)

    def get_const_order(self):
        return self.const_order

    def set_const_order(self, const_order):
        self.const_order = const_order
        self.set_payload_size(self.codeword_len*self.n_codewords/int(numpy.log2(self.const_order)))

    def get_codeword_len(self):
        return self.codeword_len

    def set_codeword_len(self, codeword_len):
        self.codeword_len = codeword_len
        self.set_payload_size(self.codeword_len*self.n_codewords/int(numpy.log2(self.const_order)))

    def get_usrp_rx_addr(self):
        return self.usrp_rx_addr

    def set_usrp_rx_addr(self, usrp_rx_addr):
        self.usrp_rx_addr = usrp_rx_addr

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps
        self.digital_pfb_clock_sync_xxx_0.update_taps((self.rrc_taps))

    def get_rf_center_freq(self):
        return self.rf_center_freq

    def set_rf_center_freq(self, rf_center_freq):
        self.rf_center_freq = rf_center_freq

    def get_preamble_size(self):
        return self.preamble_size

    def set_preamble_size(self, preamble_size):
        self.preamble_size = preamble_size
        self.blocks_multiply_const_vxx_1.set_k((1.0/(self.preamble_size*sqrt(2)), ))

    def get_pmf_peak_threshold(self):
        return self.pmf_peak_threshold

    def set_pmf_peak_threshold(self, pmf_peak_threshold):
        self.pmf_peak_threshold = pmf_peak_threshold

    def get_payload_size(self):
        return self.payload_size

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size

    def get_dataword_len(self):
        return self.dataword_len

    def set_dataword_len(self, dataword_len):
        self.dataword_len = dataword_len

    def get_barker_len(self):
        return self.barker_len

    def set_barker_len(self, barker_len):
        self.barker_len = barker_len
        self.interp_fir_filter_xxx_0_0.set_taps(( numpy.ones(self.n_barker_rep*self.barker_len)))


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    return parser


def main(top_block_cls=rx, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    tb.start()
    tb.show()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()


if __name__ == '__main__':
    main()
