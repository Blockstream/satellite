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


#ifndef INCLUDED_MODS_DA_CARRIER_PHASE_REC_H
#define INCLUDED_MODS_DA_CARRIER_PHASE_REC_H

#include <mods/api.h>
#include <gnuradio/block.h>

namespace gr {
  namespace mods {

    /*!
     * \brief <+description of block+>
     * \ingroup mods
     *
     */
    class MODS_API da_carrier_phase_rec : virtual public gr::block
    {
     public:
      typedef boost::shared_ptr<da_carrier_phase_rec> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of mods::da_carrier_phase_rec.
       *
       * To avoid accidental use of raw pointers, mods::da_carrier_phase_rec's
       * constructor is in a private implementation
       * class. mods::da_carrier_phase_rec::make is the public interface for
       * creating new instances.
       */
      static sptr make(const std::vector<gr_complex> &preamble_syms, float noise_bw, float damp_factor, int M, bool data_aided, bool reset_per_frame);
    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_DA_CARRIER_PHASE_REC_H */
