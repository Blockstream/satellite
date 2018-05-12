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
    runtime_cfo_ctrl::make(int avg_len, float abs_cfo_threshold, int rf_center_freq)
    {
      return gnuradio::get_initial_sptr
        (new runtime_cfo_ctrl_impl(avg_len, abs_cfo_threshold, rf_center_freq));
    }

    /*
     * The private constructor
     */
    runtime_cfo_ctrl_impl::runtime_cfo_ctrl_impl(int avg_len, float abs_cfo_threshold, int rf_center_freq)
      : gr::sync_block("runtime_cfo_ctrl",
              gr::io_signature::make(3, 3, sizeof(float)),
              gr::io_signature::make(1, 1, sizeof(float))),
        d_avg_len(avg_len),
        d_abs_cfo_threshold(abs_cfo_threshold),
        d_rf_center_freq(rf_center_freq),
        d_cfo_est(0.0),
        d_i_sample(0),
        d_cfo_est_converged(0),
        d_last_converged_cfo_est(0.0)
    {}

    /*
     * Our virtual destructor.
     */
    runtime_cfo_ctrl_impl::~runtime_cfo_ctrl_impl()
    {
    }

    /**
     * Reset CFO recovery state
     *
     * Reset the state of the algorithm such that it transitions back to
     * non-converged state and sets the CFO correction to 0 (no correction).
     */
    void runtime_cfo_ctrl_impl::reset_cfo_rec_state()
    {
      // Reset the sample count
      d_i_sample = 0;

      // Reset CFO memory
      d_last_converged_cfo_est = 0;

      // Reset the state
      d_cfo_est_converged = 0;
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
      float cfo_est_mean_dev;

      // Do <+signal processing+>
      for(int i = 0; i < noutput_items; i++)
      {
        // Keep track of the moving average transitory

        // Output a frequency offset only after the transitory has passed
        if (d_i_sample > d_avg_len) {
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
           * If the instantaneous CFO estimation is within the converged
           * average, take this value into consideration.
           */
          if (d_cfo_est_converged)
            d_last_converged_cfo_est = freq_offset_in[i];

          /*
           * Always output the converged average CFO, rather than the
           * instantaneous estimation (potentially noisy).
           */
          freq_offset_out[i] = d_last_converged_cfo_est;

        } else {
          // Transitory Phase

          // Increment the sample count
          d_i_sample++;

          // Output zero frequency offset
          freq_offset_out[i] = d_last_converged_cfo_est;
        }

        // Update the internal variable holding the CFO
        d_cfo_est = freq_offset_out[i];
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

    /*
     * Public methos
     */

    /**
     * Set average length
     */
    void runtime_cfo_ctrl_impl::set_avg_len(int avg_len){
        d_avg_len = avg_len;
    }

    /**
     * Get current CFO estimate
     */
    float runtime_cfo_ctrl_impl::get_cfo_estimate(){
      return d_cfo_est;
    }

    /**
     * Get target RF center frequency
     *
     * This RF center frequency corresponds to the frequency that, according to
     * the CFO recovery algorithm, should be currently used in the HW. However,
     * not it is not necessarily the RF center frequency being used already.
     *
     * When the CFO is approaching the correction range of the digital CFO
     * recovery method, in order to be able to continue tracking the CFO (before
     * the CFO exceeds the range), the RF center frequency needs to be changed
     * in HW. This function returns the adjusted frequency in this case.
     */
    int runtime_cfo_ctrl_impl::get_rf_center_freq(){
      int target_rf_center_freq;

      // If the CFO exceeds the threshold, adjust the target center frequency:
      if (fabs(d_cfo_est) > d_abs_cfo_threshold) {
        target_rf_center_freq = d_rf_center_freq + int(roundf(d_cfo_est));
      } else {
        target_rf_center_freq = d_rf_center_freq;
      }

      return target_rf_center_freq;
    }

    /**
     * Set the RF center frequency
     *
     * Must be called when the HW RF frequency change is not coming from a
     * detection carried internally, but instead by another process at another
     * module. Since the runtime CFO controller needs to be aware of the current
     * RF center frequency configured in the hardware, any such external module
     * needs to call this function during a HW freq. update.
     */
    void runtime_cfo_ctrl_impl::set_rf_center_freq(int freq){
      d_rf_center_freq = freq;

      // Reset CFO state automatically (no need for another call)
      reset_cfo_rec_state();
    }

    /**
     * Get the current CFO recovery state
     *
     * Indicates whether the CFO recovery is converged or not.
     */
    int runtime_cfo_ctrl_impl::get_cfo_est_state(){
      return d_cfo_est_converged;
    }

  } /* namespace mods */
} /* namespace gr */
