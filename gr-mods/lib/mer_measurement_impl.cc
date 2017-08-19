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
 *
 *  MER Measurement
 *
 *  Computes the instantaenous modulation error ratio (MER)
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "mer_measurement_impl.h"

namespace gr {
  namespace mods {

    mer_measurement::sptr
    mer_measurement::make(int N, int M)
    {
      return gnuradio::get_initial_sptr
        (new mer_measurement_impl(N, M));
    }

    /*
     * The private constructor
     */
    mer_measurement_impl::mer_measurement_impl(int N, int M)
      : gr::sync_block("mer_measurement",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(float))),
        d_N(N), // Averaging length
        d_M(M), // Constellation Order
        d_i_sym(0), // Symbol index used to keep track of the transitory
        d_e_sum(0.0) // Symbol mag sq. error sum
    {
      d_delay_line.resize(N);
    }

    /*
     * Our virtual destructor.
     */
    mer_measurement_impl::~mer_measurement_impl()
    {
    }

    int
    mer_measurement_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      float *out = (float *) output_items[0];
      gr_complex Ik, sym_err_k;
      float e_sum, e_k, e_k_last;
      float lin_mer;

      gr_complex origin = gr_complex(0,0);

      // Perform ML decoding over the input iq data to generate alphabets
      for(int i = 0; i < noutput_items; i++)
      {
        // Keep track of the initialization transitory
        if (d_i_sym < d_N) {
          d_i_sym++;
        }

        // Slice the symbol
        Ik = slice_symbol(in[i]);

        // Symbol error:
        sym_err_k = Ik - in[i];

        // mag Sq. of the error
        e_k = (sym_err_k.real()*sym_err_k.real()) + (sym_err_k.imag()*sym_err_k.imag());

        // Output the last mag sq error within the delay line
        e_k_last = d_delay_line.back();
        // Throw it away (pop) from the vector
        d_delay_line.pop_back();
        // Shift the delay line and put the new mag sq. in
        d_delay_line.insert(d_delay_line.begin(), e_k);

        // Update the sum of the past N mag sq. errors
        if (d_i_sym < d_N) {
          d_e_sum = d_e_sum + e_k;
        } else {
          d_e_sum = d_e_sum + (e_k - e_k_last);
        }

        // Resulting linear MER
        lin_mer = float(d_N) / d_e_sum;
        // The numerator should be the sum of the magnitude squared of the ideal
        // symbols for the past N symbols. However, since unitary magnitude is
        // assumed, the sum is simply equal to N.

        // Output MER in dB
        out[i] = 10.0*log10(lin_mer);

        // Prints
        // printf("Symbol In \t Real:\t %f\t Imag:\t %f\n", in[i].real(), in[i].imag());
        // printf("Sliced \t Real:\t %f\t Imag:\t %f\n", Ik.real(), Ik.imag());
        // printf("Error \t Real:\t %f\t Imag:\t %f\n", sym_err_k.real(), sym_err_k.imag());
        // printf("Mag Sq. Error \t %f \n", e_k);
        // printf("Popped Mag Sq. Error \t %f \n", e_k_last);
        // printf("Sum Mag Sq. Error \t %f \n", e_sum);
        // printf("Linear MER \t %f \n", lin_mer);
        // printf("dB MER \t %f \n", out[i]);
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

    gr_complex mer_measurement_impl::slice_symbol(const gr_complex &sample)
    {
      // BPSK
      if (d_M == 2) {
        if (sample.real() > 0) {
          return gr_complex(1,0);
        } else {
          return gr_complex(-1,0);
        }
      // QPSK
      } else if (d_M == 4) {
        if (sample.imag() >= 0 and sample.real() >= 0) {
          return gr_complex(0.7071068,0.7071068);
        }
        else if (sample.imag() >= 0 and sample.real() < 0) {
          return gr_complex(-0.7071068,0.7071068);
        }
        else if (sample.imag() < 0 and sample.real() < 0) {
          return gr_complex(-0.7071068,-0.7071068);
        }
        else if (sample.imag() < 0 and sample.real() >= 0) {
          return gr_complex(0.7071068,-0.7071068);
        }
      } else {
        return gr_complex(0,0);
      }
    }

  } /* namespace mods */
} /* namespace gr */
