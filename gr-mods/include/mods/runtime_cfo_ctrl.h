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


#ifndef INCLUDED_MODS_RUNTIME_CFO_CTRL_H
#define INCLUDED_MODS_RUNTIME_CFO_CTRL_H

#include <mods/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace mods {

    /*!
     * \brief <+description of block+>
     * \ingroup mods
     *
     */
    class MODS_API runtime_cfo_ctrl : virtual public gr::sync_block
    {
     public:
      typedef boost::shared_ptr<runtime_cfo_ctrl> sptr;

      virtual void set_avg_len(int avg_len) = 0;
      virtual float get_cfo_estimate() = 0;
      virtual int get_rf_center_freq() = 0;
      virtual void set_rf_center_freq(int freq) = 0;
      virtual int get_cfo_est_state() = 0;
      /*!
       * \brief Return a shared_ptr to a new instance of mods::runtime_cfo_ctrl.
       *
       * To avoid accidental use of raw pointers, mods::runtime_cfo_ctrl's
       * constructor is in a private implementation
       * class. mods::runtime_cfo_ctrl::make is the public interface for
       * creating new instances.
       */
      static sptr make(int avg_len, float abs_cfo_threshold, int rf_center_freq);
    };

  } // namespace mods
} // namespace gr

#endif /* INCLUDED_MODS_RUNTIME_CFO_CTRL_H */
