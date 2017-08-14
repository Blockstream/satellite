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
#include "turbo_decoder_impl.h"

#undef _DEBUG

namespace gr {
  namespace mods {

    turbo_decoder::sptr
    turbo_decoder::make(int N, int K)
    {
      return gnuradio::get_initial_sptr
        (new turbo_decoder_impl(N, K));
    }

    /*
     * The private constructor
     */
    turbo_decoder_impl::turbo_decoder_impl(int N, int K)
      : gr::block("turbo_decoder",
              gr::io_signature::make(1, 1, sizeof(signed char)),
              gr::io_signature::make(1, 1, sizeof(unsigned char)))
    {

			std::vector<int> poly = {013, 015};
			int tail_length = (int)(2 * std::floor(std::log2((float)std::max(poly[0], poly[1]))));
  		int N_cw        = 2 * K + tail_length;

			interleaver = new module::Interleaver_LTE<int> (K);
			interleaver->init();

			sub_enc = new module::Encoder_RSC_generic_sys<B_8> (K, N_cw, true, poly);
			std::vector<std::vector<int>> trellis = sub_enc->get_trellis();

#ifdef _DEBUG
			printf("Treliss: ");
			for(int i =0; i<8; i++)
				printf("%d ", trellis[0][i]);
			printf("\n");
#endif

    	sub_dec = new module::Decoder_RSC_BCJR_seq_very_fast <B_8,Q_8,QD_8,tools::max<Q_8>,tools::max<QD_8>> (K, trellis);

    	dec = new module::Decoder_turbo_fast<B_8,Q_8>(K, N, 6, *interleaver, *sub_dec, *sub_dec);

      set_fixed_rate(true);
      set_relative_rate((double)K/(double)N);
      set_output_multiple(K);

      d_input_size  = N * sizeof(signed char);
      d_output_size = K * sizeof(signed char);
		}

    /*
     * Our virtual destructor.
     */
    turbo_decoder_impl::~turbo_decoder_impl()
    {
    }

    int
    turbo_decoder_impl::fixed_rate_ninput_to_noutput(int ninput)
    {
#ifdef _DEBUG
			printf("[dec] input to output: %f\n", 0.5 + ninput*relative_rate());
#endif
      return (int)(0.5 + ninput*relative_rate());
    }   

    int 
    turbo_decoder_impl::fixed_rate_noutput_to_ninput(int noutput)
    {   
#ifdef _DEBUG
			printf("[dec] output to input: %f\n", 0.5 + noutput/relative_rate());
#endif
      return (int)(0.5 + noutput/relative_rate());
    }   

    void
    turbo_decoder_impl::forecast(int noutput_items,
                           gr_vector_int& ninput_items_required)
    {   
      ninput_items_required[0] = fixed_rate_noutput_to_ninput(noutput_items);
#ifdef _DEBUG
			printf("[dec] Forecast %d %d\n", noutput_items, ninput_items_required[0]);
#endif
    }   

    int 
    turbo_decoder_impl::general_work(int noutput_items,
                               gr_vector_int& ninput_items,
                               gr_vector_const_void_star &input_items,
                               gr_vector_void_star &output_items)
    {   

      signed char *inbuffer  = (signed char*)input_items[0];
      signed char *outbuffer = (signed char*)output_items[0];
#ifdef _DEBUG
			printf("[dec] in[%d] out[%d]\n", ninput_items[0], noutput_items);
#endif

      for(int i = 0; i < noutput_items/output_multiple(); i++) {
				dec->_decode_siho(inbuffer+(i*d_input_size), outbuffer+(i*d_output_size), 0);

#ifdef _DEBUG
				printf("dec_in = ");
				for(int j = 0; j< d_input_size; j++)
					printf("%d ", inbuffer[i*d_input_size+j]);
				printf("\n");
				printf("dec_out = ");
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

