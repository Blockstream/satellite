# Copyright 2011,2012 Free Software Foundation, Inc.
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

########################################################################
# Install public header files
########################################################################
install(FILES
	Decoder/Decoder_SIHO.hpp
	Decoder/Decoder_SISO.hpp
	Decoder/RSC/BCJR/Seq/Decoder_RSC_BCJR_seq_very_fast.hpp
	Decoder/Turbo/Decoder_turbo_fast.hpp
	Decoder/Turbo/Decoder_turbo.hpp
	Encoder/Encoder.hpp
	Encoder/Encoder_sys.hpp
	Encoder/RSC/Encoder_RSC_generic_sys.hpp
	Encoder/RSC/Encoder_RSC_sys.hpp
	Encoder/Turbo/Encoder_turbo.hpp
	Interleaver/Interleaver.hpp
	Interleaver/LTE/Interleaver_LTE.hpp
	Module.hpp DESTINATION include/Module
)
