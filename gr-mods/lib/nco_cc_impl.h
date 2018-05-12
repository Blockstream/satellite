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

#ifndef INCLUDED_MODS_NCO_CC_IMPL_H
#define INCLUDED_MODS_NCO_CC_IMPL_H

#include <mods/nco_cc.h>

namespace gr {
  namespace mods {

    class nco_cc_impl : public nco_cc
    {
     private:
      float d_phase_inc;
      float d_phase_accum;
      float d_last_phase_inc;
      float d_target_phase_inc;
      float d_missing_phase_inc_adj;
      float d_samp_rate;
      float d_freq;
      int d_n_steps;
      int d_i_step;
      float d_step;
      int d_state;

     public:
      nco_cc_impl(float samp_rate, float freq, int n_steps);
      ~nco_cc_impl();

      // Setters ready for parameter adjustment in runtime:
      float phase_inc() const { return d_phase_inc; }
      void set_freq(float new_freq);

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_NCO_CC_IMPL_H */
