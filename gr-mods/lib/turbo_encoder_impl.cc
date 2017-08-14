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
#include "turbo_encoder_impl.h"

#undef _DEBUG

namespace gr {
  namespace mods {

    turbo_encoder::sptr
    turbo_encoder::make(int N, int K)
    {
      return gnuradio::get_initial_sptr
        (new turbo_encoder_impl(N, K));
    }


    /*
     * The private constructor
     */
    turbo_encoder_impl::turbo_encoder_impl(int N, int K)
      : gr::block("turbo_encoder",
              gr::io_signature::make(1, 1, sizeof(char)),
              gr::io_signature::make(1, 1, sizeof(char)))
    {
			std::vector<int> poly = {013, 015};
			int tail_length = (int)(2 * std::floor(std::log2((float)std::max(poly[0], poly[1]))));
			int N_cw        = 2 * K + tail_length;

			interleaver = new module::Interleaver_LTE<int> (K);
			interleaver->init();
			sub_dec = new module::Encoder_RSC_generic_sys<B_8> (K, N_cw, true, poly);
			enc = new module::Encoder_turbo <B_8>(K, N, *interleaver, *sub_dec, *sub_dec);

      set_fixed_rate(true);
      set_relative_rate((double)N/(double)K);
      set_output_multiple(N);

      d_input_size  = K * sizeof(signed char);
      d_output_size = N * sizeof(signed char);

#ifdef _DEBUG
			std::vector<std::vector<int>> trellis = sub_dec->get_trellis();
			printf("Treliss: ");
			for(int i =0; i<8; i++)
				printf("%d ", trellis[0][i]);
			printf("\n");
#endif

		}

    /*
     * Our virtual destructor.
     */
    turbo_encoder_impl::~turbo_encoder_impl()
    {
    }

    int
    turbo_encoder_impl::fixed_rate_ninput_to_noutput(int ninput)
    {
#ifdef _DEBUG
			printf("[enc] input to output: %f\n", 0.5 + ninput*relative_rate());
#endif
      return (int)(0.5 + ninput*relative_rate());
    }   

    int 
    turbo_encoder_impl::fixed_rate_noutput_to_ninput(int noutput)
    {   
#ifdef _DEBUG
			printf("[enc] output to input: %f\n", 0.5 + noutput/relative_rate());
#endif
      return (int)(0.5 + noutput/relative_rate());
    }   

    void
    turbo_encoder_impl::forecast(int noutput_items,
                           gr_vector_int& ninput_items_required)
    {   
      ninput_items_required[0] = fixed_rate_noutput_to_ninput(noutput_items);
#ifdef _DEBUG
			printf("[enc] Forecast %d %d\n", noutput_items, ninput_items_required[0]);
#endif
    }   

    int 
    turbo_encoder_impl::general_work(int noutput_items,
                               gr_vector_int& ninput_items,
                               gr_vector_const_void_star &input_items,
                               gr_vector_void_star &output_items)
    {   
      signed char *inbuffer  = (signed char*)input_items[0];
      signed char *outbuffer = (signed char*)output_items[0];
#ifdef _DEBUG
			printf("[enc] in[%d] out[%d]\n", ninput_items[0], noutput_items);
#endif

      for(int i = 0; i < noutput_items/output_multiple(); i++) {
				enc->encode(inbuffer+(i*d_input_size), outbuffer+(i*d_output_size));

#ifdef _DEBUG
				printf("enc_in = ");
				for(int j = 0; j< d_input_size; j++)
					printf("%d ", inbuffer[i*d_input_size+j]);
				printf("\n");
				printf("enc_out = ");
				for(int j = 0; j< d_output_size; j++)
					printf("%d ", outbuffer[i*d_input_size+j]);
				printf("\n");
#endif

      }


      consume_each(fixed_rate_noutput_to_ninput(noutput_items));
      return noutput_items;
    }   


  } /* namespace mods */
} /* namespace gr */

