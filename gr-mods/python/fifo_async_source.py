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

from gnuradio import gr, blocks
import mods

class fifo_async_source(gr.hier_block2):
    """
    docstring for block fifo_async_source
    """
    def __init__(self, fifo_file, poling_rate, pkt_size):
        gr.hier_block2.__init__(self,
            "fifo_async_source",
            gr.io_signature(0,0,0),  # Input signature
            gr.io_signature(0,0,0)) # Output signature

        self.message_port_register_hier_out("async_pdu")

        ##################################################
        # Blocks
        ##################################################
        self.mods_file_source_nonblock_0 = mods.file_source_nonblock(fifo_file, poling_rate)
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, pkt_size, "packet_len")
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, 'packet_len')

        ##################################################
        # Connections
        ##################################################
        self.connect((self.mods_file_source_nonblock_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))    
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))    
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self,"async_pdu"))    


