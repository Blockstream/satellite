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

import numpy, os, stat
from gnuradio import gr

class file_sink_nonblock(gr.sync_block):
    """
    docstring for block file_sink_nonblock
    """
    def __init__(self, file_name):
        gr.sync_block.__init__(self,
            name="file_sink_nonblock",
            in_sig=[numpy.uint8],
            out_sig=None)

        self.file_name = file_name;

    def start(self):
        self.pipe_descriptor = self.get_pipe_non_block(self.file_name)

        if self.pipe_descriptor < 0:
          print("Unable to open PIPE descriptor")
          ret = False
        else:
          ret = True
          
        return ret

    def stop(self):
        print("Closing pipe file")
        os.close(self.pipe_descriptor)
        return True

    def get_pipe_non_block(self, f_name):
      # Check if file exists
      if os.path.exists(f_name):
        print('File exists')
        # Check if the file is pipe
        if stat.S_ISFIFO(os.stat(f_name).st_mode):
          print('and is pipe, opening ...')
          f = os.open(f_name, os.O_RDWR)
        else:
          print('but is not pipe, remove and recreate ...')
          os.system('rm '+f_name);
          os.mkfifo(f_name, 0777)
          f = os.open(f_name, os.O_RDWR)
      else:
        print("File does not exists, create ...")
        os.mkfifo(f_name, 0777)
        f = os.open(f_name, os.O_RDWR)
    
      return f;

    def work(self, input_items, output_items):
        in0 = input_items[0]
        # <+signal processing here+>
        data = ''
        for i in in0:
          data += chr(i)
        #print('Received data', data)
        os.write(self.pipe_descriptor, data)
        return len(input_items[0])

