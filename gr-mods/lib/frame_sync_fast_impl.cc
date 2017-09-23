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
#include "frame_sync_fast_impl.h"
#include <gnuradio/math.h>
#include <cstdio>
#include <iostream>
#include <chrono>
#include <ctime>

#define DEBUG_LOG 0
#define AVG_LEN 200
#define FRAME_ACQUIRED_CNT 50

#define FRAME_PAYLOAD   2
#define FRAME_PREAMBLE  1
#define IDLE_SPACE      0

void __debug_log(const char* fmt, ...)
{
  #if DEBUG_LOG == 1
  va_list args;
  va_start(args,fmt);
  vprintf(fmt,args);
  va_end(args);
  #endif
}

namespace gr {
  namespace mods {

    frame_sync_fast::sptr
    frame_sync_fast::make(float treshold, int preamble_len, int payload_len, int equalize, int fix_phase, int const_order, int fw_preamble, int verbosity)
    {
      return gnuradio::get_initial_sptr
      (new frame_sync_fast_impl(treshold, preamble_len, payload_len, equalize, fix_phase, const_order, fw_preamble, verbosity));
    }

    /*
    * The private constructor
    */
    static int is[] = {sizeof(gr_complex), sizeof(float), sizeof(gr_complex)};
    static std::vector<int> isig(is, is+sizeof(is)/sizeof(int));
    static int os[] = {sizeof(gr_complex), sizeof(char), sizeof(float)};
    static std::vector<int> osig(os, os+sizeof(os)/sizeof(int));
    frame_sync_fast_impl::frame_sync_fast_impl(float treshold, int preamble_len, int payload_len, int equalize, int fix_phase, int const_order, int fw_preamble, int verbosity)
    : gr::block("frame_sync_fast",
    gr::io_signature::makev(3, 3, isig),
    gr::io_signature::makev(1, 3, osig)),

    d_threshold(treshold),
    d_preamble_len(preamble_len),
    d_payload_len(payload_len),
    d_frame_len(payload_len + preamble_len),
    d_equalize(equalize),
    d_fix_phase(fix_phase),
    d_verbosity(verbosity),
    d_fw_preamble(fw_preamble),
    d_const_order(const_order),
    d_eq_gain(0.0),
    d_last_max(0.0),
    d_last_mag_peak(0.0),
    d_pmf_at_last_max(0.0),
    d_i_after_peak(0),
    d_i_sym(0),
    d_n_peak_found(0),
    d_is_first_sym_after_lock(true),
    d_i_scheduled_peak(0),
    d_peak_cnt(0),
    d_i_prev_peak(0),
    d_correct_dist_peak_cnt(0),
    d_unmatched_pmf_peak_cnt(0),
    d_frame_lock(0),
    d_timing_metric_sum(0.0),
    d_n_timing_metric(0.0),
    d_avg_peak_dist(0.0),
    d_var_peak_dist(0.0) // init with a high value
    {
      d_delay_line.resize(2*preamble_len + 1);
      d_peak_dist_hist.resize(AVG_LEN);
      d_central_diff.resize(AVG_LEN);
    }

    /*
    * Our virtual destructor.
    */
    frame_sync_fast_impl::~frame_sync_fast_impl()
    {
    }

    /*
     * Timestamp
     */
    void frame_sync_fast_impl::print_system_timestamp() {
      std::chrono::time_point<std::chrono::system_clock> now;
      now = std::chrono::system_clock::now();
      std::time_t now_time = std::chrono::system_clock::to_time_t(now);
      std::cout << "-- On " << std::ctime(&now_time);
    }

    void
    frame_sync_fast_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      unsigned ninputs = ninput_items_required.size();
      for(unsigned i = 0; i < ninputs; i++)
      ninput_items_required[i] = noutput_items;
    }

    float frame_sync_fast_impl::get_avg_timing_metric(){
      float avg;
      if(d_n_timing_metric != 0.0){
        avg = d_timing_metric_sum/d_n_timing_metric;
      }else
        avg = 0;
      d_timing_metric_sum = 0.0;
      d_n_timing_metric = 0.0;
      //printf("Cur avg %f\n", avg);
      return avg;
    }

    /*
    * Peak search
    */
    int frame_sync_fast_impl::is_corr_peak(float timing_metric, gr_complex norm_c_pmf)
    {
      int is_peak;
      int offset_from_max;
      /*
       * If the current PMF output sample is above the threshold, it is deemed
       * as a peak, but not necessarily the main peak.
       *
       * NOTE: Since the timing metric is obtained by normalizing the PMF output
       * by the received signal power itself, it is necessary to prevent a peak
       * that may arise due to normalizing by a zero Rx power (when no signal
       * is being received). Do so by checking also the second argument
       * ("norm_c_pmf") of this function. The latter is similar to the timing
       * metric, but with the important distinction that its value is normalized
       * by the theoretical preamble energy, rather than the Rx energy.
       */
      if (timing_metric > d_threshold && (fabs(norm_c_pmf) > 0.0001)){
        // Keep track of the number of peaks found for the frame
        d_n_peak_found++;
        // Update the maximum of the timing metric
        if (timing_metric > d_last_max) {
          d_last_max = timing_metric;
          d_pmf_at_last_max = norm_c_pmf;
          d_i_last_max = d_i_sym;
        }
      }

      // Offset of the current symbol index relative to the last maximum:
      offset_from_max = d_i_sym - d_i_last_max;

      // Hold peak information for external usage
      // (see get_avg_timing_metric)
      d_timing_metric_sum += abs(d_pmf_at_last_max);
      d_n_timing_metric += 1.0;

      // Check whether the offset exceeds the preamble length, meaning the last
      // maximum was really the peak in the window, in case any peak was found
      if (offset_from_max > d_preamble_len && d_n_peak_found > 0) {
        is_peak = 1;
        d_last_mag_peak = abs(d_pmf_at_last_max);
        d_eq_gain = 1.0 / d_last_mag_peak;
        d_phase_rot = resolve_phase(d_pmf_at_last_max.real(), d_pmf_at_last_max.imag());

        // Reset
        d_last_max = 0.0;
        d_n_peak_found = 0;

        // Prepare for the next maximum
        d_i_last_max = d_i_sym + d_frame_len;
        // printf("Eq gain:\t %f\n", d_eq_gain);
        // printf("Real:\t %f\t Imag:\t %f\n", d_pmf_at_last_max.real(), d_pmf_at_last_max.imag());
        // printf("Phase Rotation - Real:\t %f\t Imag:\t %f\n", d_phase_rot.real(), d_phase_rot.imag());
      } else {
        is_peak = 0;
      }

      return is_peak;
    }

    /*
     * Resolve phase ambiguity based on sign of complex PMF peak
     */
    gr_complex frame_sync_fast_impl::resolve_phase(float pmf_peak_re, float pmf_peak_im) {
      double phase_corr;
      gr_complex phase_change;

      if (d_const_order == 4) {
        if (pmf_peak_re > 0 && fabs(pmf_peak_im) < 0.1) {
          // Blue positive peak
          // Carrier Phase Loop does not rotate
          phase_corr = 0.0;
        } else if (fabs(pmf_peak_re) < 0.1 && pmf_peak_im > 0) {
          // Red positive peak
          // Carrier Phase Loop rotates by 90 degrees
          phase_corr = M_PI/2;
        } else if (pmf_peak_re < 0 && fabs(pmf_peak_im) < 0.1) {
          // Blue negative peak
          // Carrier Phase Loop rotates by 180 degrees
          phase_corr = -M_PI;
        } else if (fabs(pmf_peak_re) < 0.1 && pmf_peak_im < 0) {
          // Red negative peak
          // Carrier Phase Loop rotates by -90 degrees
          phase_corr = -M_PI/2;
        } else {
          phase_corr = 0.0;
        }
      } else if (d_const_order == 2) {
        if (pmf_peak_re > 0) {
          phase_corr = 0.0;
        } else {
          phase_corr = -M_PI;
        }
      } else {
        phase_corr = 0.0;
      }


      phase_change = gr_complex(cos(phase_corr), -sin(phase_corr));

      return phase_change;
    }

    /*
    * Post-processing of the peak for error checkings
    */
    int frame_sync_fast_impl::postprocess_peak(int is_peak_in, int offset_prev_peak)
    {
      int is_peak_out;
      int rounded_avg_peak_dist;
      int offset_from_max;

      // Check the rounded (integer) average peak distance
      rounded_avg_peak_dist = (int) (d_avg_peak_dist + 0.5f);

      /*
      * Whether or not a peak is fixed during this processing depends on the
      * variance corresponding to the peak distances. The algorithm attemps to
      * fix frame timing errors solely after the variance indicates small
      * fluctuations between frame distances.
      */
      if (d_peak_cnt > AVG_LEN && d_var_peak_dist < 1) {
        // Normal peak
        if (is_peak_in && offset_prev_peak == d_frame_len) {
          is_peak_out = 1;
        } // Peak detected, but wrong frame distance:
        else if (!is_peak_in & offset_prev_peak == rounded_avg_peak_dist) {
          is_peak_out = 1;
          if (d_verbosity > 1) {
            printf("Peak timeout triggered at offset %d\n", offset_prev_peak);
          }
        } // No peak
        else{
          is_peak_out = 0;
        }
      } else {
        is_peak_out = is_peak_in;
      }

      return is_peak_out;
    }

    /*
    * Payload state checking
    *
    * Based on the index offset with respect to the peak index, decide whether
    * the current symbol is within preamble or payload. Importantly, use a
    * dedicated index variable inside the function, one that increments solely
    * once a peak is effectively detected. Otherwise, a payload would be
    * detected prior to a frame detection.
    */
    int frame_sync_fast_impl::check_frame_part(int is_peak){
      int frame_part;

      // Is the current symbol within the frame payload?
      if ((d_i_after_peak > d_preamble_len) && (d_i_after_peak <= d_frame_len)) {
        // IMPORTANT: the last index in the payload is where the subsequent
        // frame sync timing metric peak occurs. Be sure to account for this
        // possibility in order to allow continuous operation (with no silence
        // period between frames).
        if (is_peak) {
          __debug_log("[is_payload] Found peak\n");
          d_i_after_peak = 1;
          // Flag payload, except if the first symbol after lock is caught here
          // Otherwise, the first symbol of the first acquired frame would have
          // a payload symbol appended in front of the preamble
          if (d_is_first_sym_after_lock) {
            frame_part = IDLE_SPACE;
          } else {
            frame_part = FRAME_PAYLOAD;
          }
        } else {
          d_i_after_peak ++;
          // Flag payload
          frame_part = FRAME_PAYLOAD;
        }
        __debug_log("[is_payload] Forwarding payload\n");
      // Is the current symbol within the frame preamble?
      } else if ((d_i_after_peak > 0) && (d_i_after_peak <= d_preamble_len)) {
        d_i_after_peak ++;
        frame_part = FRAME_PREAMBLE;
        __debug_log("[is_payload] Forwarding preamble\n");
      } else {
        // Trigger the acquisition of the preamble when a peak occurs in the PMF
        if (is_peak){
          __debug_log("[is_payload] Found peak\n");
          d_i_after_peak = 1;
        } else {
          d_i_after_peak = 0;
        }
        // Currently still idling
        frame_part = IDLE_SPACE;
      }

      return frame_part;
    }

    /*
    * Check frame sync acquisition
    *
    * Note: should be called after an inferred or observed peak, where
    * "inferred" means the determinstic peak assigned when in frame lock and
    * "observed" means the PMF peak observed prior to entering in frame lock.
    */
    int frame_sync_fast_impl::verify_frame_acquisition(int dist_peak) {
      int is_frame_time_acquired;

      // Check if peak distance is as expected
      if (dist_peak == d_frame_len) {
        d_correct_dist_peak_cnt++;
      } else {
        // Frame distance error, reset the counter for consecutive correct dist
        d_correct_dist_peak_cnt = 0;
      }

      // Check frame timing acquisition
      if (d_correct_dist_peak_cnt == FRAME_ACQUIRED_CNT) {
        is_frame_time_acquired = 1;
        if (d_verbosity > 0) {
          printf("\n##########################################\n");
          printf("-- Frame synchronization acquired\n");
          print_system_timestamp();
          printf("##########################################\n");
        }
      } else {
        is_frame_time_acquired = 0;
      }

      return is_frame_time_acquired;
    }

    /*
    *
    */
    int frame_sync_fast_impl::verify_frame_lock_loss(int is_pmf_peak) {
      int frame_lock_loss;
      // Check if PMF peak matches the peak that triggered this function
      if (!is_pmf_peak) {
        d_unmatched_pmf_peak_cnt++;
      } else {
        d_unmatched_pmf_peak_cnt = 0;
      }

      // Check frame timing loss
      if (d_unmatched_pmf_peak_cnt == FRAME_ACQUIRED_CNT) {
        frame_lock_loss = 1;
        if (d_verbosity > 0) {
          printf("\n##########################################\n");
          printf("-- Frame synchronization lost\n");
          print_system_timestamp();
          printf("##########################################\n");
        }
      } else {
        frame_lock_loss = 0;
      }

      return frame_lock_loss;
    }

    /*
    * Main work
    */
    int frame_sync_fast_impl::general_work (int noutput_items,
      gr_vector_int &ninput_items,
      gr_vector_const_void_star &input_items,
      gr_vector_void_star &output_items)
      {
        const gr_complex *rx_sym_in = (const gr_complex*) input_items[0];
        const float *timing_metric  = (const float*) input_items[1];
        const gr_complex *norm_c_corr = (const gr_complex*) input_items[2];
        gr_complex *rx_sym_out      = (gr_complex *) output_items[0];
        char *is_preamble           = (char *) output_items[1];
        float *peak_out             = (float *) output_items[2];

        int n_consumed = 0, n_produced = 0;
        gr_complex last_d_line_sym;
        int offset_prev_peak, last_peak_dist;
        float tmp, last_central_diff, current_central_diff;
        int is_pmf_peak;
        char is_postprocess_peak;
        int sym_frame_part;

        // Search for the main peak among the PMF output stream
        for (int i = 0; i< noutput_items ; i++) {
          __debug_log("Work %d, in (%f %f) corr %f\n", i, rx_sym_in[i].real(), rx_sym_in[i].imag(), norm_c_corr[i]);
          // Keep a running counter of symbol indexes
          d_i_sym += 1;
          n_consumed += 1;

          // Output the last symbol within the delay line
          last_d_line_sym = d_delay_line.back();
          d_delay_line.pop_back();

          // Shift the delay line and put the input symbol in
          d_delay_line.insert(d_delay_line.begin(), rx_sym_in[i]);

          // Check the index offset of the current symbol relative to the
          // previous peak:
          offset_prev_peak = d_i_sym - d_i_prev_peak;

          // Check if the current PMF sample corresponds to the main peak
          is_pmf_peak = is_corr_peak(timing_metric[i], norm_c_corr[i]);

          // Post-process when not in frame lock or simply assign the peak
          if (!d_frame_lock) {
            is_postprocess_peak = is_pmf_peak;
            // For postprocessing, use:
            // postprocess_peak(is_pmf_peak, offset_prev_peak);
            // Use the peak directly (without postprocessing) for the moment.
          } else {
            // When frame timing acquisition is already active, simply assign
            // a peak after every "frame_len" symbols
            is_postprocess_peak = (offset_prev_peak == d_frame_len);
          }

          if (is_postprocess_peak == 1) {
            // Keep track of the number of peaks tracked so far
            d_peak_cnt++;

            // Check whether frame sync is in lock (acquired) or has lost lock
            if (d_frame_lock) {
              d_frame_lock = !verify_frame_lock_loss(is_pmf_peak);
            } else {
              d_frame_lock = verify_frame_acquisition(offset_prev_peak);
            }

            // Check a frame distance error
            if ((d_verbosity > 1) && (offset_prev_peak != d_frame_len)) {
              printf("[work] Error in distance btw peak %d and %d:\t %d", d_peak_cnt-1, d_peak_cnt, offset_prev_peak);
              printf("(expected %d)\n", d_frame_len);
              printf("[work] Avg peak distance:\t %f\n", d_avg_peak_dist);
              printf("[work] Var peak distance:\t %f\n", d_var_peak_dist);
            }

            // Keep track of the average frame peak distance
            last_peak_dist = d_peak_dist_hist.back();
            d_peak_dist_hist.pop_back();
            d_avg_peak_dist = d_avg_peak_dist + (1.0/AVG_LEN)*(offset_prev_peak - last_peak_dist);
            d_peak_dist_hist.insert(d_peak_dist_hist.begin(), offset_prev_peak);

            // Keep track of central differences
            tmp = fabs(offset_prev_peak - d_avg_peak_dist);
            current_central_diff = tmp*tmp;
            last_central_diff = d_central_diff.back();
            d_central_diff.pop_back();
            d_var_peak_dist = d_var_peak_dist + (1.0/AVG_LEN)*(current_central_diff - last_central_diff);
            d_central_diff.insert(d_central_diff.begin(), current_central_diff);

            // Debug
            __debug_log("[work] Found peak at input %d\n", i);

            // Save the peak as the "previous" for the next (forthcoming) peak
            d_i_prev_peak = d_i_sym;
          }

          // Check whether the current symbol pertains to the payload
          sym_frame_part = check_frame_part(is_postprocess_peak);

          // Output the equalized symbol only when in the data payload
          if ((d_frame_lock > 0) && (sym_frame_part == FRAME_PAYLOAD || (d_fw_preamble && sym_frame_part == FRAME_PREAMBLE))){

            // Unflag the "first symbol" status
            if (d_is_first_sym_after_lock)
              d_is_first_sym_after_lock = false;

            // Single-tap equalizer:
            if (d_equalize) {
              rx_sym_out[n_produced] = d_eq_gain * last_d_line_sym;
            } else {
              rx_sym_out[n_produced] = last_d_line_sym;
            }

            // Phase ambiguity correction
            if (d_fix_phase) {
              rx_sym_out[n_produced] = rx_sym_out[n_produced] * d_phase_rot;
            }

            // Output whether this is a symbol of the preamble
            is_preamble[n_produced] = (sym_frame_part == FRAME_PREAMBLE && d_fw_preamble) ? 1 : 0;

            __debug_log("Gen output (%f %f) at %d\n", last_d_line_sym.real(), last_d_line_sym.imag(), n_produced);

            // Output the magnitude of the PMF peak
            peak_out[n_produced] = d_last_mag_peak;

            n_produced ++;
          }
        }

        // Always consume the same amount from both inputs
        consume_each(n_consumed);

        // Tell runtime system how many output items we produced.
        return n_produced;
      }

    } /* namespace mods */
  } /* namespace gr */
