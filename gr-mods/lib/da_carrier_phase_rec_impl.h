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

/*
* Data-aided Carrier Phase Recovery Loop
*
*   This module consists is an implementation of a carrier phase recovery loop
* that leverages on the knowledge of the preamble portion appended to transmit
* frames, reason why it is called "data-aided" (based on known data). The loop
* expects to receive symbols corresponding to the full frame (preamble +
* payload) in its input. When receiving the preamble, the phase error detector
* of the loop constrasts the phase of the incoming symbol with the phase of the
* expected preamble symbol that is known a priori (passed as argument to the
* block). In contrast, when receiving payload symbols, the error detector
* compares the incoming phase with the phase of the "sliced" version of the
* incoming symbol, where "sliced" should be understood as the nearest
* constellation point. Therefore, over the payload portion of the frame, the
* loop operates in "decision-directed" mode, rather than data-aided.
*
*   An important aspect of this implementation is that it resets the loop state
* at the beggining of every frame. The motivation for doing so is to avoid the
* so-called "cycle slips". The latter happens over the long term, when the loop
* that is already locked slowly slips into another stationary state. In case of
* carrier phase recovery, cycle slips come from the fact that the loop can
* settle in any of the M possible rotations of the constellation, where M is the
* constellation order. If noise is too strong, then, it possible that the loop
* keeps slipping from one stationary state to the other. In this context, then,
* by restarting the loop in the beggining of every frame, there will be less
* time for the small errors to accumulate such that a slip occurs. Furthermore,
* because the initial transitory of the loop over each frame is based on known
* preamble, the loop is expected to be already settled when payload starts for
* each frame if the is long enough.
*
*/

#ifndef INCLUDED_MODS_DA_CARRIER_PHASE_REC_IMPL_H
#define INCLUDED_MODS_DA_CARRIER_PHASE_REC_IMPL_H

#include <mods/da_carrier_phase_rec.h>

namespace gr {
  namespace mods {

    class da_carrier_phase_rec_impl : public da_carrier_phase_rec
    {
     private:
       float d_noise_bw;
       float d_damp_factor;
       float d_K1;
       float d_K2;
       float d_integrator;
       int d_i_sym;
       int d_const_order;
       float d_nco_phase;
       char d_preamble_state;
       bool d_data_aided;
       bool d_reset_per_frame;
       std::vector<gr_complex> d_tx_pilots;

     public:
      da_carrier_phase_rec_impl(const std::vector<gr_complex> &preamble_syms, float noise_bw, float damp_factor, int M, bool data_aided, bool reset_per_frame);
      ~da_carrier_phase_rec_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);
      int general_work(int noutput_items,
        gr_vector_int &ninput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items);

      gr_complex slice_symbol(const gr_complex &sample, int M);
      float set_K1(float zeta, float Bn_Ts);
      float set_K2(float zeta, float Bn_Ts);
    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_DA_CARRIER_PHASE_REC_IMPL_H */
