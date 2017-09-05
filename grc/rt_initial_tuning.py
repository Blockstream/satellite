#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Rt Initial Tuning
# Generated: Sun Sep 17 20:21:03 2017
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
from gnuradio import fec
from gnuradio import filter
from gnuradio import gr
from gnuradio import qtgui
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import *
from optparse import OptionParser
import mods
import numpy
import numpy.matlib
import osmosdr
import sip
import sys
import threading
import time
from gnuradio import qtgui


class rt_initial_tuning(gr.top_block, Qt.QWidget):

    def __init__(self, frame_sync_verbosity=0):
        gr.top_block.__init__(self, "Rt Initial Tuning")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Rt Initial Tuning")
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

        self.settings = Qt.QSettings("GNU Radio", "rt_initial_tuning")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())

        ##################################################
        # Parameters
        ##################################################
        self.frame_sync_verbosity = frame_sync_verbosity

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 8
        self.excess_bw = excess_bw = 0.25
        self.target_samp_rate = target_samp_rate = sps*(200e3/(1 + excess_bw))
        self.dsp_rate = dsp_rate = 100e6

        self.qpsk_const = qpsk_const = digital.constellation_qpsk().base()

        self.dec_factor = dec_factor = ceil(dsp_rate/target_samp_rate)
        self.const_choice = const_choice = "qpsk"

        self.bpsk_const = bpsk_const = digital.constellation_bpsk().base()

        self.barker_code_two_dim = barker_code_two_dim = [-1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j]
        self.barker_code_one_dim = barker_code_one_dim = sqrt(2)*numpy.real([-1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j,  1.0000 + 1.0000j, -1.0000 - 1.0000j])
        self.rrc_delay = rrc_delay = int(round(-44*excess_bw + 33))
        self.nfilts = nfilts = 32
        self.n_barker_rep = n_barker_rep = 10
        self.ldpc_mtx_file = ldpc_mtx_file = gr.prefix() + "/share/gnuradio/fec/ldpc/n_0512_k_0130_gap_21.alist"
        self.even_dec_factor = even_dec_factor = dec_factor if (dec_factor % 1 == 1) else (dec_factor+1)
        self.constellation = constellation = qpsk_const if (const_choice=="qpsk") else bpsk_const
        self.barker_code = barker_code = barker_code_two_dim if (const_choice == "qpsk") else barker_code_one_dim
        self.samp_rate = samp_rate = dsp_rate/even_dec_factor
        self.preamble_syms = preamble_syms = numpy.matlib.repmat(barker_code, 1, n_barker_rep)[0]
        self.n_rrc_taps = n_rrc_taps = rrc_delay * int(sps*nfilts)
        self.n_codewords = n_codewords = 1
        self.const_order = const_order = pow(2,constellation.bits_per_symbol())
        self.codeword_len = codeword_len = 18444
        self.H = H = fec.ldpc_H_matrix(ldpc_mtx_file, 21)
        self.usrp_rx_addr = usrp_rx_addr = "192.168.10.2"
        self.tuning_control = mods.tuning_control(-200000, 200000, 10000, self)
        self.sym_rate = sym_rate = samp_rate / sps
        self.scrambler_poly = scrambler_poly = 0x21
        self.scrambler_length = scrambler_length = 16
        self.rx_gain = rx_gain = 0
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(nfilts, nfilts*sps, 1.0, excess_bw, n_rrc_taps)
        self.rf_center_freq = rf_center_freq = 1428.4309e6
        self.preamble_size = preamble_size = len(preamble_syms)
        self.pmf_peak_threshold = pmf_peak_threshold = 0.7
        self.payload_size = payload_size = codeword_len*n_codewords/int(numpy.log2(const_order))
        self.freq_t = freq_t = 0


        self.dec_ldpc2 = dec_ldpc2 = fec.ldpc_decoder.make(ldpc_mtx_file, 0.5, 5);


        self.dec_ldpc = dec_ldpc = fec.ldpc_bit_flip_decoder.make(H.get_base_sptr(), 50)
        self.dataword_len = dataword_len = 6144
        self.barker_len = barker_len = 13

        ##################################################
        # Blocks
        ##################################################
        self.mods_frame_sync_fast_0 = mods.frame_sync_fast(pmf_peak_threshold, preamble_size, payload_size, 1, 1, int(const_order), 1, frame_sync_verbosity)
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

        def _freq_t_probe():
            while True:
                val = self.tuning_control.get_next_freq(self.frame_synchronizer_0.mods_frame_sync_fast_0.get_avg_timing_metric())
                try:
                    self.set_freq_t(val)
                except AttributeError:
                    pass
                time.sleep(1.0 / (0.5))
        _freq_t_thread = threading.Thread(target=_freq_t_probe)
        _freq_t_thread.daemon = True
        _freq_t_thread.start()

        self.rtlsdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + '' )
        self.rtlsdr_source_0.set_sample_rate(samp_rate)
        self.rtlsdr_source_0.set_center_freq(rf_center_freq + freq_t, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(40, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna('', 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)

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
        self.qtgui_pmf_timing_metric = qtgui.time_sink_f(
        	preamble_size + payload_size, #size
        	sym_rate, #samp_rate
        	"Frame Timing Metric", #name
        	1 #number of inputs
        )
        self.qtgui_pmf_timing_metric.set_update_time(0.10)
        self.qtgui_pmf_timing_metric.set_y_axis(-1, 1)

        self.qtgui_pmf_timing_metric.set_y_label('Amplitude', "")

        self.qtgui_pmf_timing_metric.enable_tags(-1, True)
        self.qtgui_pmf_timing_metric.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_pmf_timing_metric.enable_autoscale(True)
        self.qtgui_pmf_timing_metric.enable_grid(False)
        self.qtgui_pmf_timing_metric.enable_axis_labels(True)
        self.qtgui_pmf_timing_metric.enable_control_panel(False)

        if not True:
          self.qtgui_pmf_timing_metric.disable_legend()

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
                self.qtgui_pmf_timing_metric.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_pmf_timing_metric.set_line_label(i, labels[i])
            self.qtgui_pmf_timing_metric.set_line_width(i, widths[i])
            self.qtgui_pmf_timing_metric.set_line_color(i, colors[i])
            self.qtgui_pmf_timing_metric.set_line_style(i, styles[i])
            self.qtgui_pmf_timing_metric.set_line_marker(i, markers[i])
            self.qtgui_pmf_timing_metric.set_line_alpha(i, alphas[i])

        self._qtgui_pmf_timing_metric_win = sip.wrapinstance(self.qtgui_pmf_timing_metric.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_1.addWidget(self._qtgui_pmf_timing_metric_win, 0,1)
        self.qtgui_pmf_peak_vs_time = qtgui.time_sink_f(
        	8*(preamble_size + payload_size), #size
        	sym_rate, #samp_rate
        	"Preamble Matched Filter Peak vs. Time", #name
        	1 #number of inputs
        )
        self.qtgui_pmf_peak_vs_time.set_update_time(0.10)
        self.qtgui_pmf_peak_vs_time.set_y_axis(0, 1.1)

        self.qtgui_pmf_peak_vs_time.set_y_label('Amplitude', "")

        self.qtgui_pmf_peak_vs_time.enable_tags(-1, True)
        self.qtgui_pmf_peak_vs_time.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_pmf_peak_vs_time.enable_autoscale(False)
        self.qtgui_pmf_peak_vs_time.enable_grid(False)
        self.qtgui_pmf_peak_vs_time.enable_axis_labels(True)
        self.qtgui_pmf_peak_vs_time.enable_control_panel(False)

        if not True:
          self.qtgui_pmf_peak_vs_time.disable_legend()

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
        self.qtgui_pmf_out = qtgui.time_sink_c(
        	preamble_size + payload_size, #size
        	sym_rate, #samp_rate
        	"Preamble Matched Filter (PMF) Output", #name
        	1 #number of inputs
        )
        self.qtgui_pmf_out.set_update_time(0.10)
        self.qtgui_pmf_out.set_y_axis(-1, 1)

        self.qtgui_pmf_out.set_y_label('Re/Im Amplitudes', "")

        self.qtgui_pmf_out.enable_tags(-1, True)
        self.qtgui_pmf_out.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_pmf_out.enable_autoscale(True)
        self.qtgui_pmf_out.enable_grid(False)
        self.qtgui_pmf_out.enable_axis_labels(True)
        self.qtgui_pmf_out.enable_control_panel(False)

        if not True:
          self.qtgui_pmf_out.disable_legend()

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
                    self.qtgui_pmf_out.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_pmf_out.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_pmf_out.set_line_label(i, labels[i])
            self.qtgui_pmf_out.set_line_width(i, widths[i])
            self.qtgui_pmf_out.set_line_color(i, colors[i])
            self.qtgui_pmf_out.set_line_style(i, styles[i])
            self.qtgui_pmf_out.set_line_marker(i, markers[i])
            self.qtgui_pmf_out.set_line_alpha(i, alphas[i])

        self._qtgui_pmf_out_win = sip.wrapinstance(self.qtgui_pmf_out.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_1.addWidget(self._qtgui_pmf_out_win, 0,0)
        self.qtgui_mer = qtgui.time_sink_f(
        	1024, #size
        	sym_rate, #samp_rate
        	"", #name
        	1 #number of inputs
        )
        self.qtgui_mer.set_update_time(0.10)
        self.qtgui_mer.set_y_axis(-100, 100)

        self.qtgui_mer.set_y_label('Modulation Error Ratio (dB)', "")

        self.qtgui_mer.enable_tags(-1, True)
        self.qtgui_mer.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_mer.enable_autoscale(True)
        self.qtgui_mer.enable_grid(False)
        self.qtgui_mer.enable_axis_labels(True)
        self.qtgui_mer.enable_control_panel(False)

        if not True:
          self.qtgui_mer.disable_legend()

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
                self.qtgui_mer.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_mer.set_line_label(i, labels[i])
            self.qtgui_mer.set_line_width(i, widths[i])
            self.qtgui_mer.set_line_color(i, colors[i])
            self.qtgui_mer.set_line_style(i, styles[i])
            self.qtgui_mer.set_line_marker(i, markers[i])
            self.qtgui_mer.set_line_alpha(i, alphas[i])

        self._qtgui_mer_win = sip.wrapinstance(self.qtgui_mer.pyqwidget(), Qt.QWidget)
        self.tabs_layout_0.addWidget(self._qtgui_mer_win)
        self.qtgui_freq_sink_fll_in_0 = qtgui.freq_sink_c(
        	1024, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	0, #fc
        	samp_rate, #bw
        	"Frequency-Locked Loop (FLL) Output", #name
        	1 #number of inputs
        )
        self.qtgui_freq_sink_fll_in_0.set_update_time(0.10)
        self.qtgui_freq_sink_fll_in_0.set_y_axis(-140, 10)
        self.qtgui_freq_sink_fll_in_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_fll_in_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_fll_in_0.enable_autoscale(True)
        self.qtgui_freq_sink_fll_in_0.enable_grid(False)
        self.qtgui_freq_sink_fll_in_0.set_fft_average(0.05)
        self.qtgui_freq_sink_fll_in_0.enable_axis_labels(True)
        self.qtgui_freq_sink_fll_in_0.enable_control_panel(False)

        if not True:
          self.qtgui_freq_sink_fll_in_0.disable_legend()

        if "complex" == "float" or "complex" == "msg_float":
          self.qtgui_freq_sink_fll_in_0.set_plot_pos_half(not True)

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
                self.qtgui_freq_sink_fll_in_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_fll_in_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_fll_in_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_fll_in_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_fll_in_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_fll_in_0_win = sip.wrapinstance(self.qtgui_freq_sink_fll_in_0.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_2.addWidget(self._qtgui_freq_sink_fll_in_0_win, 0,1)
        self.qtgui_freq_sink_fll_in = qtgui.freq_sink_c(
        	1024, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	0, #fc
        	samp_rate, #bw
        	"Frequency-Locked Loop (FLL) Input", #name
        	1 #number of inputs
        )
        self.qtgui_freq_sink_fll_in.set_update_time(0.10)
        self.qtgui_freq_sink_fll_in.set_y_axis(-140, 10)
        self.qtgui_freq_sink_fll_in.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_fll_in.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_fll_in.enable_autoscale(True)
        self.qtgui_freq_sink_fll_in.enable_grid(False)
        self.qtgui_freq_sink_fll_in.set_fft_average(0.05)
        self.qtgui_freq_sink_fll_in.enable_axis_labels(True)
        self.qtgui_freq_sink_fll_in.enable_control_panel(False)

        if not True:
          self.qtgui_freq_sink_fll_in.disable_legend()

        if "complex" == "float" or "complex" == "msg_float":
          self.qtgui_freq_sink_fll_in.set_plot_pos_half(not True)

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
                self.qtgui_freq_sink_fll_in.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_fll_in.set_line_label(i, labels[i])
            self.qtgui_freq_sink_fll_in.set_line_width(i, widths[i])
            self.qtgui_freq_sink_fll_in.set_line_color(i, colors[i])
            self.qtgui_freq_sink_fll_in.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_fll_in_win = sip.wrapinstance(self.qtgui_freq_sink_fll_in.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_2.addWidget(self._qtgui_freq_sink_fll_in_win, 0,0)
        self.qtgui_freq_sink_agc_in = qtgui.freq_sink_c(
        	1024, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	0, #fc
        	samp_rate, #bw
        	"Input Signal", #name
        	1 #number of inputs
        )
        self.qtgui_freq_sink_agc_in.set_update_time(0.10)
        self.qtgui_freq_sink_agc_in.set_y_axis(-140, 10)
        self.qtgui_freq_sink_agc_in.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_agc_in.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_agc_in.enable_autoscale(False)
        self.qtgui_freq_sink_agc_in.enable_grid(False)
        self.qtgui_freq_sink_agc_in.set_fft_average(1.0)
        self.qtgui_freq_sink_agc_in.enable_axis_labels(True)
        self.qtgui_freq_sink_agc_in.enable_control_panel(False)

        if not True:
          self.qtgui_freq_sink_agc_in.disable_legend()

        if "complex" == "float" or "complex" == "msg_float":
          self.qtgui_freq_sink_agc_in.set_plot_pos_half(not True)

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
                self.qtgui_freq_sink_agc_in.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_agc_in.set_line_label(i, labels[i])
            self.qtgui_freq_sink_agc_in.set_line_width(i, widths[i])
            self.qtgui_freq_sink_agc_in.set_line_color(i, colors[i])
            self.qtgui_freq_sink_agc_in.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_agc_in_win = sip.wrapinstance(self.qtgui_freq_sink_agc_in.pyqwidget(), Qt.QWidget)
        self.tabs_layout_6.addWidget(self._qtgui_freq_sink_agc_in_win)
        self.qtgui_fll_state = qtgui.time_sink_f(
        	8192, #size
        	samp_rate, #samp_rate
        	"FLL State", #name
        	3 #number of inputs
        )
        self.qtgui_fll_state.set_update_time(0.10)
        self.qtgui_fll_state.set_y_axis(-1, 1)

        self.qtgui_fll_state.set_y_label('Amplitude', "")

        self.qtgui_fll_state.enable_tags(-1, True)
        self.qtgui_fll_state.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_fll_state.enable_autoscale(False)
        self.qtgui_fll_state.enable_grid(False)
        self.qtgui_fll_state.enable_axis_labels(True)
        self.qtgui_fll_state.enable_control_panel(False)

        if not True:
          self.qtgui_fll_state.disable_legend()

        labels = ['FLL Freq (PI Output)', 'FLL Phase Accum', 'FLL Error', '', '',
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

        for i in xrange(3):
            if len(labels[i]) == 0:
                self.qtgui_fll_state.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_fll_state.set_line_label(i, labels[i])
            self.qtgui_fll_state.set_line_width(i, widths[i])
            self.qtgui_fll_state.set_line_color(i, colors[i])
            self.qtgui_fll_state.set_line_style(i, styles[i])
            self.qtgui_fll_state.set_line_marker(i, markers[i])
            self.qtgui_fll_state.set_line_alpha(i, alphas[i])

        self._qtgui_fll_state_win = sip.wrapinstance(self.qtgui_fll_state.pyqwidget(), Qt.QWidget)
        self.tabs_grid_layout_2.addWidget(self._qtgui_fll_state_win, 1,0,1,2)
        self.qtgui_costas_state = qtgui.time_sink_f(
        	1024*4, #size
        	sym_rate, #samp_rate
        	"Costas Loop State", #name
        	1 #number of inputs
        )
        self.qtgui_costas_state.set_update_time(0.10)
        self.qtgui_costas_state.set_y_axis(-1, 1)

        self.qtgui_costas_state.set_y_label('Amplitude', "")

        self.qtgui_costas_state.enable_tags(-1, True)
        self.qtgui_costas_state.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_costas_state.enable_autoscale(False)
        self.qtgui_costas_state.enable_grid(False)
        self.qtgui_costas_state.enable_axis_labels(True)
        self.qtgui_costas_state.enable_control_panel(False)

        if not True:
          self.qtgui_costas_state.disable_legend()

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
        self.mods_mer_measurement_0 = mods.mer_measurement(1024, int(const_order))
        self.interp_fir_filter_xxx_0_0 = filter.interp_fir_filter_fff(1, ( numpy.ones(n_barker_rep*barker_len)))
        self.interp_fir_filter_xxx_0_0.declare_sample_delay(0)
        self.interp_fir_filter_xxx_0 = filter.interp_fir_filter_ccc(1, ( numpy.flipud(numpy.conj(preamble_syms))))
        self.interp_fir_filter_xxx_0.declare_sample_delay(0)
        self.digital_pfb_clock_sync_xxx_0 = digital.pfb_clock_sync_ccf(sps, 2*pi/50, (rrc_taps), nfilts, nfilts/2, pi/8, 1)
        self.digital_fll_band_edge_cc_1 = digital.fll_band_edge_cc(sps, excess_bw, rrc_delay * int(sps) + 1, 1e-4)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(2*pi/800, 2**constellation.bits_per_symbol(), False)
        self.blocks_rms_xx_1 = blocks.rms_cf(0.0001)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_char*1)
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
        self.connect((self.blocks_complex_to_mag_1, 0), (self.blocks_divide_xx_1, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.interp_fir_filter_xxx_0_0, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.digital_fll_band_edge_cc_1, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.qtgui_freq_sink_fll_in, 0))
        self.connect((self.blocks_divide_xx_1, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_divide_xx_1, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.mods_frame_sync_fast_0, 2))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.qtgui_pmf_out, 0))
        self.connect((self.blocks_multiply_const_vxx_1_1, 0), (self.blocks_complex_to_mag_1, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.mods_frame_sync_fast_0, 1))
        self.connect((self.blocks_multiply_xx_0, 0), (self.qtgui_pmf_timing_metric, 0))
        self.connect((self.blocks_rms_xx_1, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.blocks_rms_xx_1, 0), (self.qtgui_time_agc_rms_val, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.interp_fir_filter_xxx_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.mods_frame_sync_fast_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.mods_mer_measurement_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_const_sink_costas_const, 0))
        self.connect((self.digital_costas_loop_cc_0, 1), (self.qtgui_costas_state, 0))
        self.connect((self.digital_fll_band_edge_cc_1, 0), (self.digital_pfb_clock_sync_xxx_0, 0))
        self.connect((self.digital_fll_band_edge_cc_1, 3), (self.qtgui_fll_state, 2))
        self.connect((self.digital_fll_band_edge_cc_1, 1), (self.qtgui_fll_state, 0))
        self.connect((self.digital_fll_band_edge_cc_1, 2), (self.qtgui_fll_state, 1))
        self.connect((self.digital_fll_band_edge_cc_1, 0), (self.qtgui_freq_sink_fll_in_0, 0))
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0), (self.qtgui_const_sink_pfb_out_sym, 0))
        self.connect((self.interp_fir_filter_xxx_0, 0), (self.blocks_multiply_const_vxx_1, 0))
        self.connect((self.interp_fir_filter_xxx_0, 0), (self.blocks_multiply_const_vxx_1_1, 0))
        self.connect((self.interp_fir_filter_xxx_0_0, 0), (self.blocks_divide_xx_1, 1))
        self.connect((self.mods_frame_sync_fast_0, 1), (self.blocks_null_sink_0, 0))
        self.connect((self.mods_frame_sync_fast_0, 0), (self.qtgui_const_sink_x_1, 0))
        self.connect((self.mods_frame_sync_fast_0, 2), (self.qtgui_pmf_peak_vs_time, 0))
        self.connect((self.mods_mer_measurement_0, 0), (self.qtgui_mer, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_rms_xx_1, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.qtgui_freq_sink_agc_in, 0))

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "rt_initial_tuning")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_frame_sync_verbosity(self):
        return self.frame_sync_verbosity

    def set_frame_sync_verbosity(self, frame_sync_verbosity):
        self.frame_sync_verbosity = frame_sync_verbosity

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
        self.set_rrc_delay(int(round(-44*self.excess_bw + 33)))
        self.set_target_samp_rate(self.sps*(200e3/(1 + self.excess_bw)))

    def get_target_samp_rate(self):
        return self.target_samp_rate

    def set_target_samp_rate(self, target_samp_rate):
        self.target_samp_rate = target_samp_rate
        self.set_dec_factor(ceil(self.dsp_rate/self.target_samp_rate))

    def get_dsp_rate(self):
        return self.dsp_rate

    def set_dsp_rate(self, dsp_rate):
        self.dsp_rate = dsp_rate
        self.set_samp_rate(self.dsp_rate/self.even_dec_factor)
        self.set_dec_factor(ceil(self.dsp_rate/self.target_samp_rate))

    def get_qpsk_const(self):
        return self.qpsk_const

    def set_qpsk_const(self, qpsk_const):
        self.qpsk_const = qpsk_const
        self.set_constellation(self.qpsk_const if (self.const_choice=="qpsk") else self.bpsk_const)

    def get_dec_factor(self):
        return self.dec_factor

    def set_dec_factor(self, dec_factor):
        self.dec_factor = dec_factor
        self.set_even_dec_factor(self.dec_factor if (self.dec_factor % 1 == 1) else (self.dec_factor+1))

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

    def get_ldpc_mtx_file(self):
        return self.ldpc_mtx_file

    def set_ldpc_mtx_file(self, ldpc_mtx_file):
        self.ldpc_mtx_file = ldpc_mtx_file

    def get_even_dec_factor(self):
        return self.even_dec_factor

    def set_even_dec_factor(self, even_dec_factor):
        self.even_dec_factor = even_dec_factor
        self.set_samp_rate(self.dsp_rate/self.even_dec_factor)

    def get_constellation(self):
        return self.constellation

    def set_constellation(self, constellation):
        self.constellation = constellation

    def get_barker_code(self):
        return self.barker_code

    def set_barker_code(self, barker_code):
        self.barker_code = barker_code
        self.set_preamble_syms(numpy.matlib.repmat(self.barker_code, 1, self.n_barker_rep)[0])

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_sym_rate(self.samp_rate / self.sps)
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)
        self.qtgui_time_agc_rms_val.set_samp_rate(self.samp_rate)
        self.qtgui_freq_sink_fll_in_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_fll_in.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_agc_in.set_frequency_range(0, self.samp_rate)
        self.qtgui_fll_state.set_samp_rate(self.samp_rate)

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

    def get_H(self):
        return self.H

    def set_H(self, H):
        self.H = H

    def get_usrp_rx_addr(self):
        return self.usrp_rx_addr

    def set_usrp_rx_addr(self, usrp_rx_addr):
        self.usrp_rx_addr = usrp_rx_addr

    def get_tuning_control(self):
        return self.tuning_control

    def set_tuning_control(self, tuning_control):
        self.tuning_control = tuning_control

    def get_sym_rate(self):
        return self.sym_rate

    def set_sym_rate(self, sym_rate):
        self.sym_rate = sym_rate
        self.qtgui_pmf_timing_metric.set_samp_rate(self.sym_rate)
        self.qtgui_pmf_peak_vs_time.set_samp_rate(self.sym_rate)
        self.qtgui_pmf_out.set_samp_rate(self.sym_rate)
        self.qtgui_mer.set_samp_rate(self.sym_rate)
        self.qtgui_costas_state.set_samp_rate(self.sym_rate)

    def get_scrambler_poly(self):
        return self.scrambler_poly

    def set_scrambler_poly(self, scrambler_poly):
        self.scrambler_poly = scrambler_poly

    def get_scrambler_length(self):
        return self.scrambler_length

    def set_scrambler_length(self, scrambler_length):
        self.scrambler_length = scrambler_length

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps
        self.digital_pfb_clock_sync_xxx_0.update_taps((self.rrc_taps))

    def get_rf_center_freq(self):
        return self.rf_center_freq

    def set_rf_center_freq(self, rf_center_freq):
        self.rf_center_freq = rf_center_freq
        self.rtlsdr_source_0.set_center_freq(self.rf_center_freq + self.freq_t, 0)

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

    def get_freq_t(self):
        return self.freq_t

    def set_freq_t(self, freq_t):
        self.freq_t = freq_t
        self.rtlsdr_source_0.set_center_freq(self.rf_center_freq + self.freq_t, 0)

    def get_dec_ldpc2(self):
        return self.dec_ldpc2

    def set_dec_ldpc2(self, dec_ldpc2):
        self.dec_ldpc2 = dec_ldpc2

    def get_dec_ldpc(self):
        return self.dec_ldpc

    def set_dec_ldpc(self, dec_ldpc):
        self.dec_ldpc = dec_ldpc

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
    parser.add_option(
        "", "--frame-sync-verbosity", dest="frame_sync_verbosity", type="intx", default=0,
        help="Set Frame Sync Verbosity [default=%default]")
    return parser


def main(top_block_cls=rt_initial_tuning, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(frame_sync_verbosity=options.frame_sync_verbosity)
    tb.start()
    tb.show()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()


if __name__ == '__main__':
    main()
