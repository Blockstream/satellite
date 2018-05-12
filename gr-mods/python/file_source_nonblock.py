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

import numpy, time, os, stat, errno
from gnuradio import gr

class file_source_nonblock(gr.sync_block):
    """
    docstring for block file_source_nonblock
      file_name - the pipe file used to read data from
        obs: the block will automatically create this file
      poling_rate - the expected bit-rate to be read from file
        this is used to prevent the block from using the whole processing in poling
    """
    def __init__(self, file_name, poling_rate):
        gr.sync_block.__init__(self,
            name="file_source_nonblock",
            in_sig=None,
            out_sig=[numpy.uint8])

        self.poling_rate = poling_rate;
        self.DEBUG_LOG = False;
        self.file_name = file_name;
        self.finish_timestamp = 0;
        self.last_produced = 0;

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
        # Check if the file is pipe
        if stat.S_ISFIFO(os.stat(f_name).st_mode):
          f = os.open(f_name, os.O_NONBLOCK)
        else:
          os.system('rm '+f_name);
          os.mkfifo(f_name, 0777)
          f = os.open(f_name, os.O_NONBLOCK)
      else:
        os.mkfifo(f_name, 0777)
        f = os.open(f_name, os.O_NONBLOCK)
      return f;

    def close_pipe_file(self):
      os.close(self.pipe_descriptor)

    def work(self, input_items, output_items):
        out = output_items[0]

        # Wait until last samples have been processed, just to keep the throughtput
        start_timestamp = time.time()
        if self.last_produced == 0:
          sleep_time = 0.001;
        else:
          sleep_time = (self.last_produced * 8. / self.poling_rate) - \
            (start_timestamp - self.finish_timestamp)

        #print("Last Produced:",self.last_produced, "Initial Sleep:", sleep_time);

        time.sleep(sleep_time)

        # Read assynchronously from pipe
        try:
          buf = os.read(self.pipe_descriptor, len(out))
        except OSError as err:
          if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
            buf = None
          else:
            raise

        # If something was read, insert into output and count  
        n_produced = 0 
        if buf != None and buf != '':
          #udp.send_msg(buf)
          out[:len(buf)] = [ord(i) for i in buf];
          n_produced = len(buf);
          wait_time = len(buf)*8./self.poling_rate;

        # Hold information for next iteration
        self.last_produced = n_produced;
        self.finish_timestamp = time.time()

        return n_produced

