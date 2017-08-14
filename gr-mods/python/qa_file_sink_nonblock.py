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
from file_sink_nonblock import file_sink_nonblock

class qa_file_sink_nonblock (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        # set up fg

        self.blocks_random_pdu_0 = blocks.random_pdu(50, 2000, chr(0xFF), 2)
        snk = file_sink_nonblock('/tmp/test_001_out');
        self.tb.connect (src, snk)

        self.tb.run ()
        # check data


if __name__ == '__main__':
    gr_unittest.run(qa_file_sink_nonblock, "qa_file_sink_nonblock.xml")
