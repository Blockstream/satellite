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

#ifndef INCLUDED_MODS_MER_MEASUREMENT_IMPL_H
#define INCLUDED_MODS_MER_MEASUREMENT_IMPL_H

#include <mods/mer_measurement.h>

namespace gr {
  namespace mods {

    class mer_measurement_impl : public mer_measurement
    {
     private:
       int d_N;
       int d_M;
       int d_i_sym;
       float d_e_sum;
       std::vector<float> d_delay_line;
       float d_snr_db;

     public:
      mer_measurement_impl(int N, int M);
      ~mer_measurement_impl();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
      gr_complex slice_symbol(const gr_complex &sample);

      // Public metrics
      float get_snr();
    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_MER_MEASUREMENT_IMPL_H */
