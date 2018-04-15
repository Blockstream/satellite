/* -*- c++ -*- */
/*
 * Copyright 2007,2013 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * GNU Radio is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * GNU Radio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with GNU Radio; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "argpeak_impl.h"

namespace gr {
  namespace mods {

    argpeak::sptr
    argpeak::make(size_t vlen, float max_thresh)
    {
      return gnuradio::get_initial_sptr
        (new argpeak_impl(vlen, max_thresh));
    }

    argpeak_impl::argpeak_impl(size_t vlen, float max_thresh)
    : sync_block("argpeak",
                    io_signature::make(1, -1, vlen*sizeof(float)),
                    io_signature::make(1, 1, sizeof(short))),
      d_vlen(vlen),
      d_max_diff_thresh(max_thresh)
    {
    }

    argpeak_impl::~argpeak_impl()
    {
    }

    int
    argpeak_impl::work(int noutput_items,
                      gr_vector_const_void_star &input_items,
                      gr_vector_void_star &output_items)
    {
      float curr_val;
      int ninputs = input_items.size ();

      short *x_optr = (short *)output_items[0];

      for(int i = 0; i < noutput_items; i++) {
        float max = ((float *)input_items[0])[i*d_vlen];
        float scnd_max = ((float *)input_items[0])[i*d_vlen];
        int x      = 0;
        int x_scnd = 0;
        int y      = 0;
        int y_scnd = 0;

        for(int j = 0; j < (int)d_vlen; j++ ) {
          for(int k = 0; k < ninputs; k++) {

            curr_val = ((float *)input_items[k])[i*d_vlen + j];

            if (curr_val > max) {
              max = curr_val;
              x = j;
              y = k;
            } else if (curr_val > scnd_max) {
              scnd_max = curr_val;
              x_scnd = j;
              y_scnd = k;
            }
          }
        }

        /* The criteria used to infer the peak consider the following:
         *
         * - If the maximum and the second biggest value are too close in
         *   magnitude, then the peak might be just noise, so it is probably
         *   better to ignore it.
         *
         * - If the above condition is true, but the maximum and second
         *   biggest values are found in consecutive indexes, then this is good
         *   evidence that there is indeed a peak in this region, so the peak is
         *   considered.
         *
         */
        if ((max - scnd_max) > d_max_diff_thresh ||
            (x - x_scnd) == 1 ||
            (x_scnd - x) == 1) {
          *x_optr++ = (short)x;
        } else {
          *x_optr++ = 0;
        }

      }
      return noutput_items;
    }

  } /* namespace mods */
} /* namespace gr */
