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


#ifndef INCLUDED_MODS_FRAME_SYNC_FAST_H
#define INCLUDED_MODS_FRAME_SYNC_FAST_H

#include <mods/api.h>
#include <gnuradio/block.h>

namespace gr {
  namespace mods {

    /*!
     * \brief <+description of block+>
     * \ingroup mods
     *
     */
    class MODS_API frame_sync_fast : virtual public gr::block
    {
     public:
      typedef boost::shared_ptr<frame_sync_fast> sptr;

      virtual float get_avg_timing_metric() = 0;
      /*!
       * \brief Return a shared_ptr to a new instance of mods::frame_sync_fast.
       *
       * To avoid accidental use of raw pointers, mods::frame_sync_fast's
       * constructor is in a private implementation
       * class. mods::frame_sync_fast::make is the public interface for
       * creating new instances.
       */
      static sptr make(float treshold, int preamble_len, int payload_len, int n_init_peak, int equalize, int fix_phase, int const_order, int verbosity);

    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_FRAME_SYNC_FAST_H */
