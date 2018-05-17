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

#ifndef INCLUDED_MODS_RUNTIME_CFO_CTRL_IMPL_H
#define INCLUDED_MODS_RUNTIME_CFO_CTRL_IMPL_H

#include <mods/runtime_cfo_ctrl.h>

namespace gr {
  namespace mods {

    class runtime_cfo_ctrl_impl : public runtime_cfo_ctrl
    {
     private:
      // Nothing to declare in this block.
      int d_avg_len;
      float d_abs_cfo_threshold;
      float d_cfo_est;
      int d_rf_center_freq;
      int d_i_sample;
      int d_cfo_est_converged;

      void reset_cfo_rec_state();

     public:
      runtime_cfo_ctrl_impl(int avg_len, float abs_cfo_threshold, int rf_center_freq);
      ~runtime_cfo_ctrl_impl();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
      void set_avg_len(int avg_len);
      float get_cfo_estimate();
      int get_rf_center_freq();
      void set_rf_center_freq(int freq);
      int get_cfo_est_state();

    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_RUNTIME_CFO_CTRL_IMPL_H */
