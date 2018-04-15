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
#include <iostream>
#include <chrono>
#include <ctime>
#include "runtime_cfo_ctrl_impl.h"

// Thresholds used to infer convergence in the estimation:
#define CFO_EST_MEAN_THRESHOLD 10
#define CFO_EST_VAR_THRESHOLD  10

namespace gr {
  namespace mods {

    runtime_cfo_ctrl::sptr
    runtime_cfo_ctrl::make(int avg_len, float abs_cfo_threshold, float rf_center_freq)
    {
      return gnuradio::get_initial_sptr
        (new runtime_cfo_ctrl_impl(avg_len, abs_cfo_threshold, rf_center_freq));
    }

    /*
     * The private constructor
     */
    runtime_cfo_ctrl_impl::runtime_cfo_ctrl_impl(int avg_len, float abs_cfo_threshold, float rf_center_freq)
      : gr::sync_block("runtime_cfo_ctrl",
              gr::io_signature::make(3, 3, sizeof(float)),
              gr::io_signature::make(2, 2, sizeof(float))),
        d_avg_len(avg_len),
        d_abs_cfo_threshold(abs_cfo_threshold),
        d_rf_center_freq(rf_center_freq),
        d_cfo_est(0.0),
        d_i_sample(0),
        d_sleep_count(0),
        d_cfo_est_converged(0),
        d_last_converged_cfo_est(0.0)
    {}

    /*
     * Our virtual destructor.
     */
    runtime_cfo_ctrl_impl::~runtime_cfo_ctrl_impl()
    {
    }

    void runtime_cfo_ctrl_impl::print_system_timestamp() {
      std::chrono::time_point<std::chrono::system_clock> now;
      now = std::chrono::system_clock::now();
      std::time_t now_time = std::chrono::system_clock::to_time_t(now);
      std::cout << "-- On " << std::ctime(&now_time);
    }

    int
    runtime_cfo_ctrl_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const float *freq_offset_in = (const float *) input_items[0];
      const float *mean_fo_est = (const float *) input_items[1];
      const float *var_fo_est = (const float *) input_items[2];
      float *freq_offset_out = (float *) output_items[0];
      float *rf_center_freq = (float *) output_items[1];
      float cfo_est_mean_dev;

      // Do <+signal processing+>
      for(int i = 0; i < noutput_items; i++)
      {
        // Keep track of the moving average transitory

        // Output a frequency offset only after the transitory has passed
        if (d_i_sample > d_avg_len && d_sleep_count == 0) {
          // Transitory or sleep interval are finished

          // Deviation from the current mean:
          cfo_est_mean_dev = fabs(freq_offset_in[i] - mean_fo_est[i]);

          /*
           * Check if the CFO estimation has converged, i.e. has low
           * instantaneous deviation and low variance.
           */
          d_cfo_est_converged = (cfo_est_mean_dev < CFO_EST_MEAN_THRESHOLD) &&
                                (var_fo_est[i] < CFO_EST_VAR_THRESHOLD);
          /*
           * Check if the current CFO exceeds the threshold, but take actions
           * only if the CFO estimation has converged.
           *
           * When the CFO is approaching the correction range of the method, in
           * order to be able to continue tracking the CFO (if it ends up
           * exceeding the range), the RF center frequency is changed in HW.
           * The HW center freq. is updated using the current CFO estimation
           * and, then, CFO output by this block is set to 0 (since it will be
           * corrected in HW).
           */
           if (d_cfo_est_converged) {
             if (fabs(freq_offset_in[i]) > d_abs_cfo_threshold) {
               // Debug
               printf("\n--- Carrier Tracking Mechanism ---\n");
               printf("RF center frequency update.\n");
               printf("From:\t %f Hz.\n", d_rf_center_freq);
               // Adjust the RF center frequency
               d_rf_center_freq += freq_offset_in[i];
               // Set the CFO freq. offset to 0 (as if corrected by the new RF
               // center freq. configuration)
               freq_offset_out[i] = 0;
               // Add a sleep interval to prevent further increases in the RF
               // center frequency while it is being updated in the hardware
               d_sleep_count = d_avg_len;
               printf("To:\t %f Hz.\n", d_rf_center_freq);
               print_system_timestamp();
               printf("----------------------------------\n");
             } else {
               freq_offset_out[i] = freq_offset_in[i];
             }

             // Save
             d_last_converged_cfo_est = freq_offset_out[i];

           } else {
             // No correction is output, unless it is stable (converged)
             freq_offset_out[i] = d_last_converged_cfo_est;
           }
        } else {
          // Decrement the sleep interval counter
          if (d_sleep_count > 0) {
            d_sleep_count--;
          }

          // Increment the sample count
          if (d_i_sample <= d_avg_len) {
            d_i_sample++;
          }

          // Output zero frequency offset
          freq_offset_out[i] = 0;
        }

        // RF Center Frequency is the default configuration + corrections
        // accumulated during runtime
        rf_center_freq[i] = d_rf_center_freq;

        // Update the internal variable holding the CFO
        d_cfo_est = freq_offset_out[i];
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

    /*
    * Getters regarding CFO recovery data
    */
    float runtime_cfo_ctrl_impl::get_cfo_estimate(){
      return d_cfo_est;
    }
    float runtime_cfo_ctrl_impl::get_rf_center_freq(){
      return d_rf_center_freq;
    }
    int runtime_cfo_ctrl_impl::get_cfo_est_state(){
      return d_cfo_est_converged;
    }

  } /* namespace mods */
} /* namespace gr */
