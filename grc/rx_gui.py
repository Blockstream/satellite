#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Rx Gui
# Generated: Sun Feb 11 12:39:16 2018
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
from gnuradio import gr
from gnuradio import qtgui
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
import sip
import sys
import threading
import time
from gnuradio import qtgui


class rx_gui(gr.top_block, Qt.QWidget):

    def __init__(self, fft_len=2048, fllbw=0.002, frame_sync_verbosity=1, freq=0, freq_rec_alpha=0.001, gain=40, loopbw=100, loopbw_0=100, poll_rate=100):
        gr.top_block.__init__(self, "Rx Gui")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Rx Gui")
        qtgui.util.check_set_qss()
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

        self.settings = Qt.QSettings("GNU Radio", "rx_gui")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())

        ##################################################
        # Parameters
        ##################################################
        self.fft_len = fft_len
        self.fllbw = fllbw
        self.frame_sync_verbosity = frame_sync_verbosity
        self.freq = freq
        self.freq_rec_alpha = freq_rec_alpha
        self.gain = gain
        self.loopbw = loopbw
        self.loopbw_0 = loopbw_0
        self.poll_rate = poll_rate

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
        self.n_barker_rep = n_barker_rep = 10
        self.dec_factor = dec_factor = ceil(dsp_rate/target_samp_rate)
        self.constellation = constellation = qpsk_const if (const_choice=="qpsk") else bpsk_const
        self.barker_code = barker_code = barker_code_two_dim if (const_choice == "qpsk") else barker_code_one_dim
        self.preamble_syms = preamble_syms = numpy.matlib.repmat(barker_code, 1, n_barker_rep)[0]
        self.n_codewords = n_codewords = 1
        self.even_dec_factor = even_dec_factor = dec_factor if (dec_factor % 1 == 1) else (dec_factor+1)
        self.const_order = const_order = pow(2,constellation.bits_per_symbol())
        self.codeword_len = codeword_len = 18444
        self.samp_rate = samp_rate = dsp_rate/even_dec_factor
        self.rrc_delay = rrc_delay = int(round(-44*excess_bw + 33))
        self.preamble_size = preamble_size = len(preamble_syms)
        self.payload_size = payload_size = codeword_len*n_codewords/int(numpy.log2(const_order))
        self.nfilts = nfilts = 32
        self.dataword_len = dataword_len = 6144
        self.sym_rate = sym_rate = samp_rate / sps
        self.phy_preamble_overhead = phy_preamble_overhead = 1.0* preamble_size / (preamble_size + payload_size)
        self.n_rrc_taps = n_rrc_taps = rrc_delay * int(sps*nfilts)
        self.code_rate = code_rate = 1.0*dataword_len/codeword_len
        self.usrp_rx_addr = usrp_rx_addr = "192.168.10.2"
        self.tuning_control = mods.tuning_control(0, 0, 1, self)
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(nfilts, nfilts*sps, 1.0, excess_bw, n_rrc_taps)
        self.pmf_peak_threshold = pmf_peak_threshold = 0.7
        self.phy_bit_rate = phy_bit_rate = sym_rate* ( constellation.bits_per_symbol() ) * (code_rate) * (1.-phy_preamble_overhead)
        self.est_cfo_hz = est_cfo_hz = 0
        self.barker_len = barker_len = 13

        ##################################################
        # Blocks
        ##################################################
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

        self.mods_ffw_coarse_freq_rec_0 = mods.ffw_coarse_freq_rec(
            abs_cfo_threshold=0.95*(samp_rate/8),
            alpha=freq_rec_alpha,
            fft_len=fft_len,
            samp_rate=samp_rate,
            rf_center_freq=freq,
        )
        self.tabs = Qt.QTabWidget()
        self.tabs_widget_0 = Qt.QWidget()
        self.tabs_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_0)
        self.tabs_grid_layout_0 = Qt.QGridLayout()
        self.tabs_layout_0.addLayout(self.tabs_grid_layout_0)
        self.tabs.addTab(self.tabs_widget_0, 'SNR')
        self.tabs_widget_1 = Qt.QWidget()
        self.tabs_layout_1 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_1)
        self.tabs_grid_layout_1 = Qt.QGridLayout()
        self.tabs_layout_1.addLayout(self.tabs_grid_layout_1)
        self.tabs.addTab(self.tabs_widget_1, 'Frame Sync')
        self.tabs_widget_2 = Qt.QWidget()
        self.tabs_layout_2 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_2)
        self.tabs_grid_layout_2 = Qt.QGridLayout()
        self.tabs_layout_2.addLayout(self.tabs_grid_layout_2)
        self.tabs.addTab(self.tabs_widget_2, 'Freq. Sync')
        self.tabs_widget_3 = Qt.QWidget()
        self.tabs_layout_3 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_3)
        self.tabs_grid_layout_3 = Qt.QGridLayout()
        self.tabs_layout_3.addLayout(self.tabs_grid_layout_3)
        self.tabs.addTab(self.tabs_widget_3, 'Timing Sync')
        self.tabs_widget_4 = Qt.QWidget()
        self.tabs_layout_4 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_4)
        self.tabs_grid_layout_4 = Qt.QGridLayout()
        self.tabs_layout_4.addLayout(self.tabs_grid_layout_4)
        self.tabs.addTab(self.tabs_widget_4, 'Phase Sync')
        self.tabs_widget_5 = Qt.QWidget()
        self.tabs_layout_5 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_5)
        self.tabs_grid_layout_5 = Qt.QGridLayout()
        self.tabs_layout_5.addLayout(self.tabs_grid_layout_5)
        self.tabs.addTab(self.tabs_widget_5, 'Demodulation')
        self.tabs_widget_6 = Qt.QWidget()
        self.tabs_layout_6 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_6)
        self.tabs_grid_layout_6 = Qt.QGridLayout()
        self.tabs_layout_6.addLayout(self.tabs_grid_layout_6)
        self.tabs.addTab(self.tabs_widget_6, 'Auto. Gain Control')
        self.top_layout.addWidget(self.tabs)

        def _est_cfo_hz_probe():
            while True:
                val = self.tuning_control.update_nco_freq(self.mods_ffw_coarse_freq_rec_0.mods_runtime_cfo_ctrl_0.get_cfo_estimate(), self.mods_ffw_coarse_freq_rec_0.mods_runtime_cfo_ctrl_0.get_rf_center_freq(), self.rtlsdr_source_0.get_center_freq())
                try:
                    self.set_est_cfo_hz(val)
                except AttributeError:
                    pass
                time.sleep(1.0 / (poll_rate))
        _est_cfo_hz_thread = threading.Thread(target=_est_cfo_hz_probe)
        _est_cfo_hz_thread.daemon = True
        _est_cfo_hz_thread.start()

        self.qtgui_vector_sink_f_0 = qtgui.vector_sink_f(
            fft_len,
            0,
            1,
            "FFT bin",
            "log FFT",
            "Freq. Offset Estimation FFT",
            1 # Number of inputs
        )
        self.qtgui_vector_sink_f_0.set_update_time(0.10)
        self.qtgui_vector_sink_f_0.set_y_axis(-140, 10)
        self.qtgui_vector_sink_f_0.enable_autoscale(True)
        self.qtgui_vector_sink_f_0.enable_grid(False)
        self.qtgui_vector_sink_f_0.set_x_axis_units("kHz")
        self.qtgui_vector_sink_f_0.set_y_axis_units("")
        self.qtgui_vector_sink_f_0.set_ref_level(0)

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_vector_sink_f_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_vector_sink_f_0.set_line_label(i, labels[i])
            self.qtgui_vector_sink_f_0.set_line_width(i, widths[i])
            self.qtgui_vector_sink_f_0.set_line_color(i, colors[i])
            self.qtgui_vector_sink_f_0.set_line_alpha(i, alphas[i])

        self._qtgui_vector_sink_f_0_win = sip.wrapinstance(self.qtgui_vector_sink_f_0.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_2.addWidget(self._qtgui_vector_sink_f_0_win, 1,1)
        self.qtgui_time_sink_x_2 = qtgui.time_sink_c(
        	preamble_size + payload_size, #size
        	sym_rate, #samp_rate
        	"Preamble Matched Filter Output", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_2.set_update_time(0.10)
        self.qtgui_time_sink_x_2.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_2.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_2.enable_tags(-1, True)
        self.qtgui_time_sink_x_2.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_2.enable_autoscale(True)
        self.qtgui_time_sink_x_2.enable_grid(False)
        self.qtgui_time_sink_x_2.enable_axis_labels(True)
        self.qtgui_time_sink_x_2.enable_control_panel(False)

        if not True:
          self.qtgui_time_sink_x_2.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(2):
            if len(labels[i]) == 0:
                if(i % 2 == 0):
                    self.qtgui_time_sink_x_2.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_2.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_2.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_2.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_2.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_2.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_2.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_2.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_2_win = sip.wrapinstance(self.qtgui_time_sink_x_2.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_1.addWidget(self._qtgui_time_sink_x_2_win, 0,0)
        self.qtgui_time_sink_x_1_0_0 = qtgui.time_sink_f(
        	1024, #size
        	phy_bit_rate/8, #samp_rate
        	"Demodulated Bytes", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_1_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_1_0_0.set_y_axis(-128, 128)

        self.qtgui_time_sink_x_1_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1_0_0.enable_tags(-1, False)
        self.qtgui_time_sink_x_1_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_1_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_1_0_0.enable_grid(False)
        self.qtgui_time_sink_x_1_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_1_0_0.enable_control_panel(False)

        if not True:
          self.qtgui_time_sink_x_1_0_0.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_1_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_1_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_1_0_0.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_5.addWidget(self._qtgui_time_sink_x_1_0_0_win, 0,0)
        self.qtgui_time_sink_x_1_0 = qtgui.time_sink_f(
        	1024, #size
        	phy_bit_rate, #samp_rate
        	"Demodulated Bits", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_1_0.set_update_time(0.10)
        self.qtgui_time_sink_x_1_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_1_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1_0.enable_tags(-1, True)
        self.qtgui_time_sink_x_1_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_1_0.enable_autoscale(False)
        self.qtgui_time_sink_x_1_0.enable_grid(False)
        self.qtgui_time_sink_x_1_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_1_0.enable_control_panel(False)

        if not True:
          self.qtgui_time_sink_x_1_0.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_1_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_1_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_0_win = sip.wrapinstance(self.qtgui_time_sink_x_1_0.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_5.addWidget(self._qtgui_time_sink_x_1_0_win, 1,0)
        self.qtgui_time_sink_x_1 = qtgui.time_sink_f(
        	8, #size
        	samp_rate/fft_len, #samp_rate
        	"Coarse Freq. Offset Estimation", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_1.set_update_time(0.10)
        self.qtgui_time_sink_x_1.set_y_axis(-samp_rate/8, samp_rate/8)

        self.qtgui_time_sink_x_1.set_y_label('Freq. Offset', "Hz")

        self.qtgui_time_sink_x_1.enable_tags(-1, False)
        self.qtgui_time_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_1.enable_autoscale(False)
        self.qtgui_time_sink_x_1.enable_grid(False)
        self.qtgui_time_sink_x_1.enable_axis_labels(True)
        self.qtgui_time_sink_x_1.enable_control_panel(False)

        if not True:
          self.qtgui_time_sink_x_1.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_win = sip.wrapinstance(self.qtgui_time_sink_x_1.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_2.addWidget(self._qtgui_time_sink_x_1_win, 1,0)
        self.qtgui_time_sink_x_0_0 = qtgui.time_sink_f(
        	preamble_size + payload_size, #size
        	sym_rate, #samp_rate
        	"Frame Timing Metric", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0.enable_tags(-1, True)
        self.qtgui_time_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0_0.enable_autoscale(True)
        self.qtgui_time_sink_x_0_0.enable_grid(False)
        self.qtgui_time_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0.enable_control_panel(False)

        if not True:
          self.qtgui_time_sink_x_0_0.disable_legend()

        labels = ['Mag Sq', 'Mag', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_1.addWidget(self._qtgui_time_sink_x_0_0_win, 0,1)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
        	(preamble_size + payload_size)*4, #size
        	samp_rate, #samp_rate
        	"DA Carrier Phase Recovery Error", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(-1, True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(True)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)

        if not True:
          self.qtgui_time_sink_x_0.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_4.addWidget(self._qtgui_time_sink_x_0_win, 0,1)
        self.qtgui_time_agc_rms_val = qtgui.time_sink_f(
        	1024, #size
        	samp_rate, #samp_rate
        	"Input RMS Value Estimate", #name
        	1 #number of inputs
        )
        self.qtgui_time_agc_rms_val.set_update_time(0.10)
        self.qtgui_time_agc_rms_val.set_y_axis(-1, 1)

        self.qtgui_time_agc_rms_val.set_y_label('Amplitude', "")

        self.qtgui_time_agc_rms_val.enable_tags(-1, True)
        self.qtgui_time_agc_rms_val.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_agc_rms_val.enable_autoscale(False)
        self.qtgui_time_agc_rms_val.enable_grid(False)
        self.qtgui_time_agc_rms_val.enable_axis_labels(True)
        self.qtgui_time_agc_rms_val.enable_control_panel(False)

        if not True:
          self.qtgui_time_agc_rms_val.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_time_agc_rms_val.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_agc_rms_val.set_line_label(i, labels[i])
            self.qtgui_time_agc_rms_val.set_line_width(i, widths[i])
            self.qtgui_time_agc_rms_val.set_line_color(i, colors[i])
            self.qtgui_time_agc_rms_val.set_line_style(i, styles[i])
            self.qtgui_time_agc_rms_val.set_line_marker(i, markers[i])
            self.qtgui_time_agc_rms_val.set_line_alpha(i, alphas[i])

        self._qtgui_time_agc_rms_val_win = sip.wrapinstance(self.qtgui_time_agc_rms_val.pyqwidget(), Qt.QWidget)
        self.tabs_layout_6.addWidget(self._qtgui_time_agc_rms_val_win)
        self.qtgui_pmf_peak_vs_time = qtgui.time_sink_f(
        	8*(preamble_size + payload_size), #size
        	sym_rate, #samp_rate
        	"Preamble Matched Filter Peak vs. Time", #name
        	1 #number of inputs
        )
        self.qtgui_pmf_peak_vs_time.set_update_time(0.10)
        self.qtgui_pmf_peak_vs_time.set_y_axis(-0.2, 1.2)

        self.qtgui_pmf_peak_vs_time.set_y_label('Amplitude', "")

        self.qtgui_pmf_peak_vs_time.enable_tags(-1, True)
        self.qtgui_pmf_peak_vs_time.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_pmf_peak_vs_time.enable_autoscale(True)
        self.qtgui_pmf_peak_vs_time.enable_grid(False)
        self.qtgui_pmf_peak_vs_time.enable_axis_labels(True)
        self.qtgui_pmf_peak_vs_time.enable_control_panel(False)

        if not True:
          self.qtgui_pmf_peak_vs_time.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_pmf_peak_vs_time.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_pmf_peak_vs_time.set_line_label(i, labels[i])
            self.qtgui_pmf_peak_vs_time.set_line_width(i, widths[i])
            self.qtgui_pmf_peak_vs_time.set_line_color(i, colors[i])
            self.qtgui_pmf_peak_vs_time.set_line_style(i, styles[i])
            self.qtgui_pmf_peak_vs_time.set_line_marker(i, markers[i])
            self.qtgui_pmf_peak_vs_time.set_line_alpha(i, alphas[i])

        self._qtgui_pmf_peak_vs_time_win = sip.wrapinstance(self.qtgui_pmf_peak_vs_time.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_1.addWidget(self._qtgui_pmf_peak_vs_time_win, 1,0,1,2)
        self.qtgui_mer_measurement_pre_frame_sync = qtgui.time_sink_f(
        	preamble_size + payload_size, #size
        	sym_rate, #samp_rate
        	'Input to Frame Synchronizer', #name
        	1 #number of inputs
        )
        self.qtgui_mer_measurement_pre_frame_sync.set_update_time(0.10)
        self.qtgui_mer_measurement_pre_frame_sync.set_y_axis(-100, 100)

        self.qtgui_mer_measurement_pre_frame_sync.set_y_label('Modulation Error Ratio (dB)', "")

        self.qtgui_mer_measurement_pre_frame_sync.enable_tags(-1, True)
        self.qtgui_mer_measurement_pre_frame_sync.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_mer_measurement_pre_frame_sync.enable_autoscale(True)
        self.qtgui_mer_measurement_pre_frame_sync.enable_grid(False)
        self.qtgui_mer_measurement_pre_frame_sync.enable_axis_labels(True)
        self.qtgui_mer_measurement_pre_frame_sync.enable_control_panel(False)

        if not True:
          self.qtgui_mer_measurement_pre_frame_sync.disable_legend()

        labels = ['', 'Post-eq', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_mer_measurement_pre_frame_sync.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_mer_measurement_pre_frame_sync.set_line_label(i, labels[i])
            self.qtgui_mer_measurement_pre_frame_sync.set_line_width(i, widths[i])
            self.qtgui_mer_measurement_pre_frame_sync.set_line_color(i, colors[i])
            self.qtgui_mer_measurement_pre_frame_sync.set_line_style(i, styles[i])
            self.qtgui_mer_measurement_pre_frame_sync.set_line_marker(i, markers[i])
            self.qtgui_mer_measurement_pre_frame_sync.set_line_alpha(i, alphas[i])

        self._qtgui_mer_measurement_pre_frame_sync_win = sip.wrapinstance(self.qtgui_mer_measurement_pre_frame_sync.pyqwidget(), Qt.QWidget)
        self.tabs_layout_0.addWidget(self._qtgui_mer_measurement_pre_frame_sync_win)
        self.qtgui_mer_measurement_pre_decoder = qtgui.time_sink_f(
        	preamble_size + payload_size, #size
        	sym_rate, #samp_rate
        	'Input to Decoder', #name
        	1 #number of inputs
        )
        self.qtgui_mer_measurement_pre_decoder.set_update_time(0.10)
        self.qtgui_mer_measurement_pre_decoder.set_y_axis(-100, 100)

        self.qtgui_mer_measurement_pre_decoder.set_y_label('Modulation Error Ratio (dB)', "")

        self.qtgui_mer_measurement_pre_decoder.enable_tags(-1, True)
        self.qtgui_mer_measurement_pre_decoder.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_mer_measurement_pre_decoder.enable_autoscale(True)
        self.qtgui_mer_measurement_pre_decoder.enable_grid(False)
        self.qtgui_mer_measurement_pre_decoder.enable_axis_labels(True)
        self.qtgui_mer_measurement_pre_decoder.enable_control_panel(False)

        if not True:
          self.qtgui_mer_measurement_pre_decoder.disable_legend()

        labels = ['', 'Post-eq', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_mer_measurement_pre_decoder.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_mer_measurement_pre_decoder.set_line_label(i, labels[i])
            self.qtgui_mer_measurement_pre_decoder.set_line_width(i, widths[i])
            self.qtgui_mer_measurement_pre_decoder.set_line_color(i, colors[i])
            self.qtgui_mer_measurement_pre_decoder.set_line_style(i, styles[i])
            self.qtgui_mer_measurement_pre_decoder.set_line_marker(i, markers[i])
            self.qtgui_mer_measurement_pre_decoder.set_line_alpha(i, alphas[i])

        self._qtgui_mer_measurement_pre_decoder_win = sip.wrapinstance(self.qtgui_mer_measurement_pre_decoder.pyqwidget(), Qt.QWidget)
        self.tabs_layout_0.addWidget(self._qtgui_mer_measurement_pre_decoder_win)
        self.qtgui_freq_sink_fll_in_1 = qtgui.freq_sink_c(
        	1024, #size
        	firdes.WIN_HANN, #wintype
        	0, #fc
        	samp_rate, #bw
        	"Spectrum Before/After Coarse Freq. Correction", #name
        	2 #number of inputs
        )
        self.qtgui_freq_sink_fll_in_1.set_update_time(0.10)
        self.qtgui_freq_sink_fll_in_1.set_y_axis(-140, 10)
        self.qtgui_freq_sink_fll_in_1.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_fll_in_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_fll_in_1.enable_autoscale(True)
        self.qtgui_freq_sink_fll_in_1.enable_grid(False)
        self.qtgui_freq_sink_fll_in_1.set_fft_average(0.05)
        self.qtgui_freq_sink_fll_in_1.enable_axis_labels(True)
        self.qtgui_freq_sink_fll_in_1.enable_control_panel(False)

        if not True:
          self.qtgui_freq_sink_fll_in_1.disable_legend()

        if "complex" == "float" or "complex" == "msg_float":
          self.qtgui_freq_sink_fll_in_1.set_plot_pos_half(not True)

        labels = ['Before', 'After', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [0.5, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(2):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_fll_in_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_fll_in_1.set_line_label(i, labels[i])
            self.qtgui_freq_sink_fll_in_1.set_line_width(i, widths[i])
            self.qtgui_freq_sink_fll_in_1.set_line_color(i, colors[i])
            self.qtgui_freq_sink_fll_in_1.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_fll_in_1_win = sip.wrapinstance(self.qtgui_freq_sink_fll_in_1.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_2.addWidget(self._qtgui_freq_sink_fll_in_1_win, 0,0,1,2)
        self.qtgui_freq_sink_agc_in = qtgui.freq_sink_c(
        	1024, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	0, #fc
        	samp_rate, #bw
        	"Signal", #name
        	2 #number of inputs
        )
        self.qtgui_freq_sink_agc_in.set_update_time(0.10)
        self.qtgui_freq_sink_agc_in.set_y_axis(-140, 10)
        self.qtgui_freq_sink_agc_in.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_agc_in.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_agc_in.enable_autoscale(True)
        self.qtgui_freq_sink_agc_in.enable_grid(False)
        self.qtgui_freq_sink_agc_in.set_fft_average(0.05)
        self.qtgui_freq_sink_agc_in.enable_axis_labels(True)
        self.qtgui_freq_sink_agc_in.enable_control_panel(False)

        if not True:
          self.qtgui_freq_sink_agc_in.disable_legend()

        if "complex" == "float" or "complex" == "msg_float":
          self.qtgui_freq_sink_agc_in.set_plot_pos_half(not True)

        labels = ['Output', 'Input', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(2):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_agc_in.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_agc_in.set_line_label(i, labels[i])
            self.qtgui_freq_sink_agc_in.set_line_width(i, widths[i])
            self.qtgui_freq_sink_agc_in.set_line_color(i, colors[i])
            self.qtgui_freq_sink_agc_in.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_agc_in_win = sip.wrapinstance(self.qtgui_freq_sink_agc_in.pyqwidget(), Qt.QWidget)
        self.tabs_layout_6.addWidget(self._qtgui_freq_sink_agc_in_win)
        self.qtgui_costas_state = qtgui.time_sink_f(
        	8*(preamble_size + payload_size), #size
        	sym_rate, #samp_rate
        	"Costas Loop State", #name
        	1 #number of inputs
        )
        self.qtgui_costas_state.set_update_time(0.10)
        self.qtgui_costas_state.set_y_axis(0, 1.1)

        self.qtgui_costas_state.set_y_label('Amplitude', "")

        self.qtgui_costas_state.enable_tags(-1, True)
        self.qtgui_costas_state.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_costas_state.enable_autoscale(False)
        self.qtgui_costas_state.enable_grid(False)
        self.qtgui_costas_state.enable_axis_labels(True)
        self.qtgui_costas_state.enable_control_panel(False)

        if not True:
          self.qtgui_costas_state.disable_legend()

        labels = ['Frequency', 'Post-eq', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_costas_state.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_costas_state.set_line_label(i, labels[i])
            self.qtgui_costas_state.set_line_width(i, widths[i])
            self.qtgui_costas_state.set_line_color(i, colors[i])
            self.qtgui_costas_state.set_line_style(i, styles[i])
            self.qtgui_costas_state.set_line_marker(i, markers[i])
            self.qtgui_costas_state.set_line_alpha(i, alphas[i])

        self._qtgui_costas_state_win = sip.wrapinstance(self.qtgui_costas_state.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_4.addWidget(self._qtgui_costas_state_win, 0,0)
        self.qtgui_const_sink_x_1 = qtgui.const_sink_c(
        	1024, #size
        	"DA Carrier Phase Rec Output Symbols (payload-only)", #name
        	1 #number of inputs
        )
        self.qtgui_const_sink_x_1.set_update_time(0.10)
        self.qtgui_const_sink_x_1.set_y_axis(-2, 2)
        self.qtgui_const_sink_x_1.set_x_axis(-2, 2)
        self.qtgui_const_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_1.enable_autoscale(False)
        self.qtgui_const_sink_x_1.enable_grid(False)
        self.qtgui_const_sink_x_1.enable_axis_labels(True)

        if not True:
          self.qtgui_const_sink_x_1.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
                  "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_1_win = sip.wrapinstance(self.qtgui_const_sink_x_1.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_4.addWidget(self._qtgui_const_sink_x_1_win, 1,1)
        self.qtgui_const_sink_pfb_out_sym = qtgui.const_sink_c(
        	1024, #size
        	"Symbol Timing Recovery Output Symbols", #name
        	1 #number of inputs
        )
        self.qtgui_const_sink_pfb_out_sym.set_update_time(0.10)
        self.qtgui_const_sink_pfb_out_sym.set_y_axis(-2, 2)
        self.qtgui_const_sink_pfb_out_sym.set_x_axis(-2, 2)
        self.qtgui_const_sink_pfb_out_sym.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_pfb_out_sym.enable_autoscale(False)
        self.qtgui_const_sink_pfb_out_sym.enable_grid(False)
        self.qtgui_const_sink_pfb_out_sym.enable_axis_labels(True)

        if not True:
          self.qtgui_const_sink_pfb_out_sym.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
                  "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_pfb_out_sym.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_pfb_out_sym.set_line_label(i, labels[i])
            self.qtgui_const_sink_pfb_out_sym.set_line_width(i, widths[i])
            self.qtgui_const_sink_pfb_out_sym.set_line_color(i, colors[i])
            self.qtgui_const_sink_pfb_out_sym.set_line_style(i, styles[i])
            self.qtgui_const_sink_pfb_out_sym.set_line_marker(i, markers[i])
            self.qtgui_const_sink_pfb_out_sym.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_pfb_out_sym_win = sip.wrapinstance(self.qtgui_const_sink_pfb_out_sym.pyqwidget(), Qt.QWidget)
        self.tabs_layout_3.addWidget(self._qtgui_const_sink_pfb_out_sym_win)
        self.qtgui_const_sink_costas_const = qtgui.const_sink_c(
        	1024, #size
        	"Costas Loop Output Symbols", #name
        	1 #number of inputs
        )
        self.qtgui_const_sink_costas_const.set_update_time(0.10)
        self.qtgui_const_sink_costas_const.set_y_axis(-2, 2)
        self.qtgui_const_sink_costas_const.set_x_axis(-2, 2)
        self.qtgui_const_sink_costas_const.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_costas_const.enable_autoscale(False)
        self.qtgui_const_sink_costas_const.enable_grid(False)
        self.qtgui_const_sink_costas_const.enable_axis_labels(True)

        if not True:
          self.qtgui_const_sink_costas_const.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
                  "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_costas_const.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_costas_const.set_line_label(i, labels[i])
            self.qtgui_const_sink_costas_const.set_line_width(i, widths[i])
            self.qtgui_const_sink_costas_const.set_line_color(i, colors[i])
            self.qtgui_const_sink_costas_const.set_line_style(i, styles[i])
            self.qtgui_const_sink_costas_const.set_line_marker(i, markers[i])
            self.qtgui_const_sink_costas_const.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_costas_const_win = sip.wrapinstance(self.qtgui_const_sink_costas_const.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_4.addWidget(self._qtgui_const_sink_costas_const_win, 1,0)
        self.mods_turbo_decoder_0 = mods.turbo_decoder(codeword_len, dataword_len)
        self.mods_nco_cc_0 = mods.nco_cc((2*pi*(est_cfo_hz/samp_rate)), 100)
        self.mods_mer_measurement_pre_frame_sync = mods.mer_measurement(1024, int(const_order))
        self.mods_mer_measurement_pre_decoder = mods.mer_measurement(1024, int(const_order))
        self.mods_fifo_async_sink_0 = mods.fifo_async_sink('/tmp/async_rx')
        self.mods_da_carrier_phase_rec_0_0 = mods.da_carrier_phase_rec(((1/sqrt(2))*preamble_syms), 0.001, 1/sqrt(2), int(const_order), True, True)
        self.framers_gr_hdlc_deframer_b_0 = framers.gr_hdlc_deframer_b(0)
        self.frame_synchronizer_0 = mods.frame_synchronizer(
            M=int(const_order),
            equalize=1,
            fix_phase=1,
            fw_preamble=1,
            payload_size=payload_size,
            pmf_peak_threshold=pmf_peak_threshold,
            preamble_size=preamble_size,
            preamble_syms=preamble_syms,
            verbosity=frame_sync_verbosity,
        )
        self.digital_pfb_clock_sync_xxx_0 = digital.pfb_clock_sync_ccf(sps, 2*pi/50, (rrc_taps), nfilts, nfilts/2, pi/8, 1)
        self.digital_map_bb_0_0_0 = digital.map_bb(([1,- 1]))
        self.digital_descrambler_bb_0 = digital.descrambler_bb(0x21, 0x7F, 16)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(2*pi/loopbw, 2**constellation.bits_per_symbol(), False)
        self.digital_constellation_decoder_cb_0 = digital.constellation_decoder_cb(constellation.base())
        self.blocks_unpack_k_bits_bb_0 = blocks.unpack_k_bits_bb(constellation.bits_per_symbol())
        self.blocks_rms_xx_1 = blocks.rms_cf(0.0001)
        self.blocks_pack_k_bits_bb_1 = blocks.pack_k_bits_bb(8)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_divide_xx_0 = blocks.divide_cc(1)
        self.blocks_char_to_float_0_1 = blocks.char_to_float(1, 1)
        self.blocks_char_to_float_0_0 = blocks.char_to_float(1, 1)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.framers_gr_hdlc_deframer_b_0, 'pdu'), (self.mods_fifo_async_sink_0, 'async_pdu'))
        self.connect((self.blocks_char_to_float_0_0, 0), (self.qtgui_time_sink_x_1_0, 0))
        self.connect((self.blocks_char_to_float_0_1, 0), (self.qtgui_time_sink_x_1_0_0, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.mods_ffw_coarse_freq_rec_0, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.mods_nco_cc_0, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.qtgui_freq_sink_agc_in, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.qtgui_freq_sink_fll_in_1, 0))
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.blocks_pack_k_bits_bb_1, 0), (self.blocks_char_to_float_0_1, 0))
        self.connect((self.blocks_rms_xx_1, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.blocks_rms_xx_1, 0), (self.qtgui_time_agc_rms_val, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0, 0), (self.digital_map_bb_0_0_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.blocks_unpack_k_bits_bb_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.frame_synchronizer_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.mods_mer_measurement_pre_frame_sync, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_const_sink_costas_const, 0))
        self.connect((self.digital_costas_loop_cc_0, 1), (self.qtgui_costas_state, 0))
        self.connect((self.digital_descrambler_bb_0, 0), (self.blocks_char_to_float_0_0, 0))
        self.connect((self.digital_descrambler_bb_0, 0), (self.blocks_pack_k_bits_bb_1, 0))
        self.connect((self.digital_descrambler_bb_0, 0), (self.framers_gr_hdlc_deframer_b_0, 0))
        self.connect((self.digital_map_bb_0_0_0, 0), (self.mods_turbo_decoder_0, 0))
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0), (self.qtgui_const_sink_pfb_out_sym, 0))
        self.connect((self.frame_synchronizer_0, 1), (self.mods_da_carrier_phase_rec_0_0, 1))
        self.connect((self.frame_synchronizer_0, 0), (self.mods_da_carrier_phase_rec_0_0, 0))
        self.connect((self.frame_synchronizer_0, 2), (self.qtgui_pmf_peak_vs_time, 0))
        self.connect((self.frame_synchronizer_0, 3), (self.qtgui_time_sink_x_0_0, 0))
        self.connect((self.frame_synchronizer_0, 4), (self.qtgui_time_sink_x_2, 0))
        self.connect((self.mods_da_carrier_phase_rec_0_0, 0), (self.digital_constellation_decoder_cb_0, 0))
        self.connect((self.mods_da_carrier_phase_rec_0_0, 0), (self.mods_mer_measurement_pre_decoder, 0))
        self.connect((self.mods_da_carrier_phase_rec_0_0, 0), (self.qtgui_const_sink_x_1, 0))
        self.connect((self.mods_da_carrier_phase_rec_0_0, 1), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.mods_ffw_coarse_freq_rec_0, 1), (self.qtgui_time_sink_x_1, 0))
        self.connect((self.mods_ffw_coarse_freq_rec_0, 0), (self.qtgui_vector_sink_f_0, 0))
        self.connect((self.mods_mer_measurement_pre_decoder, 0), (self.qtgui_mer_measurement_pre_decoder, 0))
        self.connect((self.mods_mer_measurement_pre_frame_sync, 0), (self.qtgui_mer_measurement_pre_frame_sync, 0))
        self.connect((self.mods_nco_cc_0, 0), (self.digital_pfb_clock_sync_xxx_0, 0))
        self.connect((self.mods_nco_cc_0, 0), (self.qtgui_freq_sink_fll_in_1, 1))
        self.connect((self.mods_turbo_decoder_0, 0), (self.digital_descrambler_bb_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_rms_xx_1, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.qtgui_freq_sink_agc_in, 1))

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "rx_gui")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self.mods_ffw_coarse_freq_rec_0.set_fft_len(self.fft_len)
        self.qtgui_time_sink_x_1.set_samp_rate(self.samp_rate/self.fft_len)

    def get_fllbw(self):
        return self.fllbw

    def set_fllbw(self, fllbw):
        self.fllbw = fllbw

    def get_frame_sync_verbosity(self):
        return self.frame_sync_verbosity

    def set_frame_sync_verbosity(self, frame_sync_verbosity):
        self.frame_sync_verbosity = frame_sync_verbosity
        self.frame_synchronizer_0.set_verbosity(self.frame_sync_verbosity)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.rtlsdr_source_0.set_center_freq(self.freq, 0)
        self.mods_ffw_coarse_freq_rec_0.set_rf_center_freq(self.freq)

    def get_freq_rec_alpha(self):
        return self.freq_rec_alpha

    def set_freq_rec_alpha(self, freq_rec_alpha):
        self.freq_rec_alpha = freq_rec_alpha
        self.mods_ffw_coarse_freq_rec_0.set_alpha(self.freq_rec_alpha)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.rtlsdr_source_0.set_gain(self.gain, 0)

    def get_loopbw(self):
        return self.loopbw

    def set_loopbw(self, loopbw):
        self.loopbw = loopbw
        self.digital_costas_loop_cc_0.set_loop_bandwidth(2*pi/self.loopbw)

    def get_loopbw_0(self):
        return self.loopbw_0

    def set_loopbw_0(self, loopbw_0):
        self.loopbw_0 = loopbw_0

    def get_poll_rate(self):
        return self.poll_rate

    def set_poll_rate(self, poll_rate):
        self.poll_rate = poll_rate

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_sym_rate(self.samp_rate / self.sps)
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))
        self.set_target_samp_rate(self.sps*(200e3/(1 + self.excess_bw)))
        self.set_n_rrc_taps(self.rrc_delay * int(self.sps*self.nfilts))

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))
        self.set_target_samp_rate(self.sps*(200e3/(1 + self.excess_bw)))
        self.set_rrc_delay(int(round(-44*self.excess_bw + 33)))

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

    def get_n_barker_rep(self):
        return self.n_barker_rep

    def set_n_barker_rep(self, n_barker_rep):
        self.n_barker_rep = n_barker_rep
        self.set_preamble_syms(numpy.matlib.repmat(self.barker_code, 1, self.n_barker_rep)[0])

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
        self.frame_synchronizer_0.set_preamble_syms(self.preamble_syms)

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
        self.frame_synchronizer_0.set_M(int(self.const_order))

    def get_codeword_len(self):
        return self.codeword_len

    def set_codeword_len(self, codeword_len):
        self.codeword_len = codeword_len
        self.set_payload_size(self.codeword_len*self.n_codewords/int(numpy.log2(self.const_order)))
        self.set_code_rate(1.0*self.dataword_len/self.codeword_len)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)
        self.mods_ffw_coarse_freq_rec_0.set_abs_cfo_threshold(0.95*(self.samp_rate/8))
        self.mods_ffw_coarse_freq_rec_0.set_samp_rate(self.samp_rate)
        self.set_sym_rate(self.samp_rate / self.sps)
        self.qtgui_time_sink_x_1.set_y_axis(-self.samp_rate/8, self.samp_rate/8)
        self.qtgui_time_sink_x_1.set_samp_rate(self.samp_rate/self.fft_len)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_agc_rms_val.set_samp_rate(self.samp_rate)
        self.qtgui_freq_sink_fll_in_1.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_agc_in.set_frequency_range(0, self.samp_rate)
        self.mods_nco_cc_0.set_phase_inc((2*pi*(self.est_cfo_hz/self.samp_rate)))

    def get_rrc_delay(self):
        return self.rrc_delay

    def set_rrc_delay(self, rrc_delay):
        self.rrc_delay = rrc_delay
        self.set_n_rrc_taps(self.rrc_delay * int(self.sps*self.nfilts))

    def get_preamble_size(self):
        return self.preamble_size

    def set_preamble_size(self, preamble_size):
        self.preamble_size = preamble_size
        self.set_phy_preamble_overhead(1.0* self.preamble_size / (self.preamble_size + self.payload_size))
        self.frame_synchronizer_0.set_preamble_size(self.preamble_size)

    def get_payload_size(self):
        return self.payload_size

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size
        self.set_phy_preamble_overhead(1.0* self.preamble_size / (self.preamble_size + self.payload_size))
        self.frame_synchronizer_0.set_payload_size(self.payload_size)

    def get_nfilts(self):
        return self.nfilts

    def set_nfilts(self, nfilts):
        self.nfilts = nfilts
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))
        self.set_n_rrc_taps(self.rrc_delay * int(self.sps*self.nfilts))

    def get_dataword_len(self):
        return self.dataword_len

    def set_dataword_len(self, dataword_len):
        self.dataword_len = dataword_len
        self.set_code_rate(1.0*self.dataword_len/self.codeword_len)

    def get_sym_rate(self):
        return self.sym_rate

    def set_sym_rate(self, sym_rate):
        self.sym_rate = sym_rate
        self.set_phy_bit_rate(self.sym_rate* ( constellation.bits_per_symbol() ) * (self.code_rate) * (1.-self.phy_preamble_overhead))
        self.qtgui_time_sink_x_2.set_samp_rate(self.sym_rate)
        self.qtgui_time_sink_x_0_0.set_samp_rate(self.sym_rate)
        self.qtgui_pmf_peak_vs_time.set_samp_rate(self.sym_rate)
        self.qtgui_mer_measurement_pre_frame_sync.set_samp_rate(self.sym_rate)
        self.qtgui_mer_measurement_pre_decoder.set_samp_rate(self.sym_rate)
        self.qtgui_costas_state.set_samp_rate(self.sym_rate)

    def get_phy_preamble_overhead(self):
        return self.phy_preamble_overhead

    def set_phy_preamble_overhead(self, phy_preamble_overhead):
        self.phy_preamble_overhead = phy_preamble_overhead
        self.set_phy_bit_rate(self.sym_rate* ( constellation.bits_per_symbol() ) * (self.code_rate) * (1.-self.phy_preamble_overhead))

    def get_n_rrc_taps(self):
        return self.n_rrc_taps

    def set_n_rrc_taps(self, n_rrc_taps):
        self.n_rrc_taps = n_rrc_taps
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts*self.sps, 1.0, self.excess_bw, self.n_rrc_taps))

    def get_code_rate(self):
        return self.code_rate

    def set_code_rate(self, code_rate):
        self.code_rate = code_rate
        self.set_phy_bit_rate(self.sym_rate* ( constellation.bits_per_symbol() ) * (self.code_rate) * (1.-self.phy_preamble_overhead))

    def get_usrp_rx_addr(self):
        return self.usrp_rx_addr

    def set_usrp_rx_addr(self, usrp_rx_addr):
        self.usrp_rx_addr = usrp_rx_addr

    def get_tuning_control(self):
        return self.tuning_control

    def set_tuning_control(self, tuning_control):
        self.tuning_control = tuning_control

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps
        self.digital_pfb_clock_sync_xxx_0.update_taps((self.rrc_taps))

    def get_pmf_peak_threshold(self):
        return self.pmf_peak_threshold

    def set_pmf_peak_threshold(self, pmf_peak_threshold):
        self.pmf_peak_threshold = pmf_peak_threshold
        self.frame_synchronizer_0.set_pmf_peak_threshold(self.pmf_peak_threshold)

    def get_phy_bit_rate(self):
        return self.phy_bit_rate

    def set_phy_bit_rate(self, phy_bit_rate):
        self.phy_bit_rate = phy_bit_rate
        self.qtgui_time_sink_x_1_0_0.set_samp_rate(self.phy_bit_rate/8)
        self.qtgui_time_sink_x_1_0.set_samp_rate(self.phy_bit_rate)

    def get_est_cfo_hz(self):
        return self.est_cfo_hz

    def set_est_cfo_hz(self, est_cfo_hz):
        self.est_cfo_hz = est_cfo_hz
        self.mods_nco_cc_0.set_phase_inc((2*pi*(self.est_cfo_hz/self.samp_rate)))

    def get_barker_len(self):
        return self.barker_len

    def set_barker_len(self, barker_len):
        self.barker_len = barker_len


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "", "--fft-len", dest="fft_len", type="intx", default=2048,
        help="Set Carrier Freq. Recovery FFT Size [default=%default]")
    parser.add_option(
        "", "--fllbw", dest="fllbw", type="eng_float", default=eng_notation.num_to_str(0.002),
        help="Set fllbw [default=%default]")
    parser.add_option(
        "-v", "--frame-sync-verbosity", dest="frame_sync_verbosity", type="intx", default=1,
        help="Set Frame Sync Verbosity [default=%default]")
    parser.add_option(
        "", "--freq", dest="freq", type="intx", default=0,
        help="Set freq [default=%default]")
    parser.add_option(
        "", "--freq-rec-alpha", dest="freq_rec_alpha", type="eng_float", default=eng_notation.num_to_str(0.001),
        help="Set Carrier Freq. Recovery Averaging Alpha [default=%default]")
    parser.add_option(
        "", "--gain", dest="gain", type="intx", default=40,
        help="Set gain [default=%default]")
    parser.add_option(
        "", "--loopbw", dest="loopbw", type="intx", default=100,
        help="Set loopbw [default=%default]")
    parser.add_option(
        "", "--loopbw-0", dest="loopbw_0", type="intx", default=100,
        help="Set loopbw_0 [default=%default]")
    return parser


def main(top_block_cls=rx_gui, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(fft_len=options.fft_len, fllbw=options.fllbw, frame_sync_verbosity=options.frame_sync_verbosity, freq=options.freq, freq_rec_alpha=options.freq_rec_alpha, gain=options.gain, loopbw=options.loopbw, loopbw_0=options.loopbw_0)
    tb.start()
    tb.show()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()


if __name__ == '__main__':
    main()
