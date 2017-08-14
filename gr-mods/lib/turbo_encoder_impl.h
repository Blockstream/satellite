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

#ifndef INCLUDED_MODS_TURBO_ENCODER_IMPL_H
#define INCLUDED_MODS_TURBO_ENCODER_IMPL_H

#include <mods/turbo_encoder.h>

#include "Tools/types.h"
#include "Module/Interleaver/LTE/Interleaver_LTE.hpp"

#include "Module/Encoder/Turbo/Encoder_turbo.hpp"
#include "Module/Encoder/Encoder_sys.hpp"
#include "Module/Encoder/RSC/Encoder_RSC_generic_sys.hpp"

using namespace aff3ct;

namespace gr {
  namespace mods {

    class turbo_encoder_impl : public turbo_encoder
    {
     private:
      // Nothing to declare in this block.
			module::Interleaver_LTE<int> *interleaver;
			module::Encoder_RSC_generic_sys<B_8> *sub_dec;
			module::Encoder_turbo<B_8> *enc;
      int d_input_size  ;
      int d_output_size ;

     public:
      turbo_encoder_impl(int N, int K);
      ~turbo_encoder_impl();

      // Where all the action really happens
      //int work(int noutput_items,
      //   gr_vector_const_void_star &input_items,
      //   gr_vector_void_star &output_items);
      int general_work(int noutput_items,
                       gr_vector_int& ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items);
      int fixed_rate_ninput_to_noutput(int ninput);
      int fixed_rate_noutput_to_ninput(int noutput);
      void forecast(int noutput_items,
                    gr_vector_int& ninput_items_required);
    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_TURBO_ENCODER_IMPL_H */

