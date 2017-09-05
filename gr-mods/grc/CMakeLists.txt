# Copyright 2011 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

install(FILES
    mods_frame_sync_cc.xml
    mods_frame_sync_fast.xml
    mods_file_source_nonblock.xml
    mods_file_sink_nonblock.xml
    mods_fifo_async_source.xml
    mods_fifo_async_sink.xml
    mods_turbo_encoder.xml
    mods_turbo_decoder.xml
    mods_mer_measurement.xml
    mods_da_carrier_phase_rec.xml
    mods_nco_cc.xml
    mods_ffw_coarse_freq_rec.xml
    mods_wrap_fft_index.xml
    mods_frame_synchronizer.xml
    mods_exponentiate_const_cci.xml
    mods_runtime_cfo_ctrl.xml
    mods_exponentiate_const_cci.xml
    mods_variable_tuning_control.xml
    mods_wrap_fft_index.xml DESTINATION share/gnuradio/grc/blocks
)
