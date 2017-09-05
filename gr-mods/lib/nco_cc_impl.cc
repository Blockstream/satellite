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
#include <gnuradio/expj.h>
#include "nco_cc_impl.h"

#define M_TWOPI (2*M_PI)

namespace gr {
  namespace mods {

    nco_cc::sptr
    nco_cc::make(float phase_inc)
    {
      return gnuradio::get_initial_sptr
        (new nco_cc_impl(phase_inc));
    }

    /*
     * The private constructor
     */
    nco_cc_impl::nco_cc_impl(float phase_inc)
      : gr::sync_block("nco_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex))),
      d_phase_accum(0.0),
      d_phase_inc(0.0)
    {
    }

    /*
     * Our virtual destructor.
     */
    nco_cc_impl::~nco_cc_impl()
    {
    }

    void nco_cc_impl::set_phase_inc(float new_phase_inc) {
      d_phase_inc = new_phase_inc;
    }

    int
    nco_cc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      gr_complex nco_conj;

      // Multiply the incoming symbols by the NCO
      for(int i = 0; i < noutput_items; i++)
      {
        // Accumulate the current phase increment
        d_phase_accum = d_phase_accum + d_phase_inc;

        // Wrap phase between -pi to pi
        while (d_phase_accum < -M_PI)
          d_phase_accum += M_TWOPI;
        while (d_phase_accum > M_PI)
          d_phase_accum -= M_TWOPI;

        // Complex conjugate of the NCO value
        nco_conj = gr_expj(-d_phase_accum);

        // Phase correction
        out[i] = in[i] * nco_conj;
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace mods */
} /* namespace gr */
