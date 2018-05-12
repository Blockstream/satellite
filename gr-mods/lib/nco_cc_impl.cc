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
    nco_cc::make(float samp_rate, float freq, int n_steps)
    {
      return gnuradio::get_initial_sptr
        (new nco_cc_impl(samp_rate, freq, n_steps));
    }

    /*
     * The private constructor
     */
    nco_cc_impl::nco_cc_impl(float samp_rate, float freq, int n_steps)
      : gr::sync_block("nco_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex))),
      d_phase_accum(0.0),
      d_phase_inc(0.0),
      d_last_phase_inc(0.0),
      d_target_phase_inc(0.0),
      d_missing_phase_inc_adj(0.0),
      d_samp_rate(samp_rate),
      d_freq(freq),
      d_n_steps(n_steps),
      d_i_step(0),
      d_step(0.0),
      d_state(0)
    {
    }

    /*
     * Our virtual destructor.
     */
    nco_cc_impl::~nco_cc_impl()
    {
    }

    void nco_cc_impl::set_freq(float new_freq) {
      float new_phase_inc;
      float phase_inc_change;
      float missing_phase_inc_adj;

      // Compute new phase increment
      new_phase_inc = M_TWOPI * new_freq / d_samp_rate;

      // Check if there was a change and, if yes, enter a state in which the
      // target new increment is reached smoothly
      phase_inc_change = new_phase_inc - d_phase_inc;

      if (d_state == 0) {
        // Save the previous configuration
        d_last_phase_inc = d_phase_inc;

        // Save the target new configuration
        d_target_phase_inc = new_phase_inc;

        // Detect whether the NCO has been reset and, in this case, change it
        // immediatelly. Otherwise, change smoothly.
        if (d_target_phase_inc == 0.0) {
          // Compute a single transition step
          d_step = (d_target_phase_inc - d_last_phase_inc);

          // Set it straight to the last step
          d_i_step == d_n_steps;
        } else {
          // Compute the smooth transition step
          d_step = (d_target_phase_inc - d_last_phase_inc) / float(d_n_steps);

          // Set it in the first step
          d_i_step = 0;
        }

        if (fabs(d_step) > 1e-8) {
          // Enter the Transition sate
          d_state = 1;
        }
      }

      // When transitioning, slowly increase/decrease to the target phase inc
      if (d_state == 1) {

        // Are we done?
        missing_phase_inc_adj = fabs(d_phase_inc - d_target_phase_inc);

        if (missing_phase_inc_adj > d_missing_phase_inc_adj
            || d_i_step == d_n_steps) {
          // Leave the Transition sate
          d_state = 0;
        } else {
          d_i_step++;
        }

        //Apply one more step
        d_phase_inc = d_phase_inc + d_step;

        // Save the missing amount for the phase increment change
        d_missing_phase_inc_adj = missing_phase_inc_adj;
      } else {
        // Otherwise, just keep the configuration
        d_phase_inc = d_phase_inc;
      }
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
