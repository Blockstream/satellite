/* -*- c++ -*- */
/*
 * Copyright 2017 <+YOU OR YOUR COMPANY+>.
 *
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "wrap_fft_index_impl.h"

namespace gr {
  namespace mods {

    wrap_fft_index::sptr
    wrap_fft_index::make(int fft_size)
    {
      return gnuradio::get_initial_sptr
        (new wrap_fft_index_impl(fft_size));
    }

    /*
     * The private constructor
     */
    wrap_fft_index_impl::wrap_fft_index_impl(int fft_size)
      : gr::sync_block("wrap_fft_index",
              gr::io_signature::make(1, 1, sizeof(short)),
              gr::io_signature::make(1, 1, sizeof(short))),
        d_fft_size(fft_size)
    {}

    /*
     * Our virtual destructor.
     */
    wrap_fft_index_impl::~wrap_fft_index_impl()
    {
    }

    int
    wrap_fft_index_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const short *in = (const short *) input_items[0];
      short *out = (short *) output_items[0];

      // Do <+signal processing+>
      for(int i = 0; i < noutput_items; i++)
      {
        if (in[i] > (d_fft_size/2)) {
          out[i] = in[i] - d_fft_size;
        } else {
          out[i] = in[i];
        }
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace mods */
} /* namespace gr */
