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
#include <gnuradio/math.h>
#include "da_carrier_phase_rec_impl.h"

namespace gr {
  namespace mods {

    da_carrier_phase_rec::sptr
    da_carrier_phase_rec::make(const std::vector<gr_complex> &preamble_syms, float noise_bw, float damp_factor, int M, bool data_aided, bool reset_per_frame)
    {
      return gnuradio::get_initial_sptr
        (new da_carrier_phase_rec_impl(preamble_syms, noise_bw, damp_factor, M, data_aided, reset_per_frame));
    }

    /*
     * The private constructor
     */
    static int is[] = {sizeof(gr_complex), sizeof(char)};
    static std::vector<int> isig(is, is+sizeof(is)/sizeof(int));
    static int os[] = {sizeof(gr_complex), sizeof(float)};
    static std::vector<int> osig(os, os+sizeof(os)/sizeof(int));
    da_carrier_phase_rec_impl::da_carrier_phase_rec_impl(const std::vector<gr_complex> &preamble_syms, float noise_bw, float damp_factor, int M, bool data_aided, bool reset_per_frame)
      : gr::block("da_carrier_phase_rec",
              io_signature::makev(2, 2, isig),
              io_signature::makev(2, 2, osig)),
              d_noise_bw(noise_bw),
              d_damp_factor(damp_factor),
              d_const_order(M),
              d_data_aided(data_aided),
              d_reset_per_frame(reset_per_frame),
              d_i_sym(0),
              d_nco_phase(0.0),
              d_integrator(0.0),
              d_preamble_state(0)
    {
      d_tx_pilots.resize(preamble_syms.size());
      d_tx_pilots = preamble_syms;
      d_K1 = set_K1(damp_factor, noise_bw);
      d_K2 = set_K2(damp_factor, noise_bw);
    }

    /*
     * Our virtual destructor.
     */
    da_carrier_phase_rec_impl::~da_carrier_phase_rec_impl()
    {
    }

    void
    da_carrier_phase_rec_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      unsigned ninputs = ninput_items_required.size();
      for(unsigned i = 0; i < ninputs; i++)
      ninput_items_required[i] = noutput_items;
    }

    /*
    * Set PI Constants
    *
    * References
    * [1] "Digital Communications: A Discrete-Time Approach", by Michael Rice
    */
    float da_carrier_phase_rec_impl::set_K1(float zeta, float Bn_Ts) {
      float theta_n;
      float Kp_K0_K1;
      float K1;

      // Definition theta_n (See Eq. C.60 in [1])
      theta_n = Bn_Ts / (zeta + (1.0/(4*zeta)));
      // Note: for this loop, Bn*Ts = Bn*T, because the loop operates at 1
      // sample/symbol (at the symbol rate).

      // Eq. C.56 in [1]:
      Kp_K0_K1 = (4 * zeta * theta_n) / (1 + 2*zeta*theta_n + (theta_n*theta_n));

      // Then obtain the PI contants:
      K1 = Kp_K0_K1;
      /*
      * This value should be divided by (Kp * K0), but the latter is unitary
      * here. That is:
      *
      * Carrier Phase Error Detector Gain is unitary (Kp = 1)
      * DDS Gain is unitary (K0 = 1)
      */
      // printf("K1 configured to:\t %f\n", K1);

      return K1;
    }
    float da_carrier_phase_rec_impl::set_K2(float zeta, float Bn_Ts) {
      float theta_n;
      float Kp_K0_K2;
      float K2;

      // Definition theta_n (See Eq. C.60 in [1])
      theta_n = Bn_Ts / (zeta + (1.0/(4*zeta)));
      // Note: for this loop, Bn*Ts = Bn*T, because the loop operates at 1
      // sample/symbol (at the symbol rate).

      // Eq. C.56 in [1]:
      Kp_K0_K2 = (4 * (theta_n*theta_n)) / (1 + 2*zeta*theta_n + (theta_n*theta_n));

      // Then obtain the PI contants:
      K2 = Kp_K0_K2;
      /*
      * This value should be divided by (Kp * K0), but the latter is unitary
      * here. That is:
      *
      * Carrier Phase Error Detector Gain is unitary (Kp = 1)
      * DDS Gain is unitary (K0 = 1)
      */
      // printf("K2 configured to:\t %f\n", K2);

      return K2;
    }

    /*
     * Main work
     */
    int da_carrier_phase_rec_impl::general_work(int noutput_items,
        gr_vector_int &ninput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *rx_sym_in = (const gr_complex*) input_items[0];
      const char *is_preamble  = (const char*) input_items[1];
      gr_complex *rx_sym_out = (gr_complex *) output_items[0];
      float *error_out = (float *) output_items[1];
      gr_complex nco_conj;
      gr_complex x_derotated, x_sliced, conj_prod_err;
      float phi_error;
      float p_out, pi_out;
      int n_consumed = 0, n_produced = 0;

      // Do <+signal processing+>
      for (int i = 0; i< noutput_items ; i++) {
        // Keep track of the number of consumed inputs
        n_consumed += 1;

        // Keep track of the symbol index
        d_i_sym++;

        /*
         * Keep a state indicating whether symbol is preamble or not and use
         * that to recognize the beginning of the frame (where symbol index
         * should be 0)
         */

        // Check the transition into the preamble, which happens whenever the
        // previous state was not-preamble and the current input is preamble
        if (d_preamble_state == 0 && is_preamble[i]) {
          d_preamble_state = 1;
          // Reset the symbol index
          d_i_sym = 0;

          // Reset the loop state for each frame, if so desired
          if (d_reset_per_frame) {
            d_nco_phase  = 0.0; // Reset the NCO phase accumulator
            d_integrator = 0.0; // Reset the integrator
          }
        } else if (d_preamble_state == 1 && !is_preamble[i]) {
          d_preamble_state = 0;
        }

        // Update NCO (actually the complex conjugate of the NCO)
        // nco_conj = gr_complex(cos(d_nco_phase), -sin(d_nco_phase));
        nco_conj = gr_expj(-d_nco_phase);

        // De-rotation:
        x_derotated = rx_sym_in[i] * nco_conj;

        /*
         * Phase Error Detection
         *
         * When operating over the payload symbols, compute the phase error by
         * inspecting the angle of the cross conjugate product between the
         * sliced (symbols after decision) and the noisy received symbols. This
         * is the decision-directed operation. Meanwhile, when operating over
         * the preamble (the known training sequence), the error is taken from
         * the angle of the cross conjugate product between the known preamble
         * symbols and the noisy received symbols, operation is data-aided.
         *
         * Note that another possibility is obtaining the error by the direct
         * difference between the angle of the received symbol and the angle of
         * the expected symbol. However, this type of difference suffers from
         * ambiguity. Meanwhile, when using the conjugate product, ambiguity is
         * not a problem.
         *
         */
        if (is_preamble[i] && d_data_aided) {
            // Preamble

            // Data-aided error detector's conjugate product:
            conj_prod_err = x_derotated * conj(d_tx_pilots[d_i_sym]);
        } else {
            // Payload

            // Sliced symbol (nearest constellation point)
            x_sliced = slice_symbol(x_derotated, d_const_order);

            // Decision-directed error detector's conjugate product:
            conj_prod_err = x_derotated * conj(x_sliced);
        }

        // Phase error is the angle of the conjugate product:
        phi_error = gr::fast_atan2f(conj_prod_err);

        /*
         * Outputs
         * (only for the payload)
         */
        if (!is_preamble[i]) {
          // Put this de-rotated symbol in the ouput:
          rx_sym_out[n_produced] = x_derotated;

          // Error detector
          error_out[n_produced] = phi_error;

          // Produce an output only for the payload
          n_produced ++;
        }


        /*
        * Loop Filter
        */

        // Proportional term
        p_out  = phi_error * d_K1;
        // Integral term
        d_integrator = (phi_error * d_K2) + d_integrator;
        // PI Filter output:
        pi_out = p_out + d_integrator;

        /*
         * Next value for the phase accumulator
         */
        d_nco_phase = d_nco_phase + pi_out;
      }

      // Always consume the same amount from both inputs
      consume_each(n_consumed);

      // Tell runtime system how many output items we produced.
      return n_produced;
    }

    /*
     * Symbol slicing
     */
    gr_complex da_carrier_phase_rec_impl::slice_symbol(const gr_complex &sample, int M)
    {
      // BPSK
      if (M == 2) {
        if (sample.real() > 0) {
          return gr_complex(1,0);
        } else {
          return gr_complex(-1,0);
        }
        // QPSK
      } else if (M == 4) {
        // Search for the correct quadrant and slice
        if (sample.imag() >= 0) {
          if (sample.real() >= 0) {
            return gr_complex(0.7071068,0.7071068);
          } else {
            return gr_complex(-0.7071068,0.7071068);
          }
        } else {
          if (sample.real() >= 0) {
            return gr_complex(0.7071068,-0.7071068);
          } else {
            return gr_complex(-0.7071068,-0.7071068);
          }
        }
      } else {
        return gr_complex(0,0);
      }
    }

  } /* namespace mods */
} /* namespace gr */
