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

#ifndef INCLUDED_MODS_FRAME_SYNC_FAST_IMPL_H
#define INCLUDED_MODS_FRAME_SYNC_FAST_IMPL_H

#include <mods/frame_sync_fast.h>

namespace gr {
  namespace mods {

    class frame_sync_fast_impl : public frame_sync_fast
    {
    private:
      float d_threshold;
      int d_preamble_len;
      int d_payload_len;
      int d_frame_len;
      int d_n_init_peaks;
      int d_equalize;
      int d_fix_phase;
      int d_verbosity;
      float d_eq_gain;
      gr_complex d_phase_rot;
      float d_last_max;
      gr_complex d_pmf_at_last_max;
      int d_i_last_max;
      int d_i_after_peak;
      int d_i_sym;
      int d_pending_peak;
      int d_i_scheduled_peak;
      int d_peak_cnt;
      int d_i_prev_peak;
      int d_correct_dist_peak_cnt;
      int d_unmatched_pmf_peak_cnt;
      int d_frame_lock;
      int d_const_order;
      float d_avg_peak_dist;
      float d_var_peak_dist;
      std::vector<gr_complex> d_delay_line;
      std::vector<int> d_peak_dist_hist;
      std::vector<float> d_central_diff;


    public:
      frame_sync_fast_impl(float treshold,int preamble_len,int payload_len,int n_init_peak, int equalize, int fix_phase, int const_order, int verbosity);
      ~frame_sync_fast_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);
      int is_corr_peak(float timing_metric, gr_complex norm_c_pmf);
      int postprocess_peak(int is_peak_in, int offset_prev_peak);
      int is_payload(int is_peak);
      int verify_frame_acquisition(int d_peak);
      int verify_frame_lock_loss(int is_pmf_peak);
      gr_complex resolve_phase(float pmf_peak_re, float pmf_peak_im);

      int general_work(int noutput_items,
        gr_vector_int &ninput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items);
      };

    } // namespace mods
  } // namespace gr

  #endif /* INCLUDED_MODS_FRAME_SYNC_FAST_IMPL_H */
