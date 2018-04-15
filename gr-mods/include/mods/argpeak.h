/* -*- c++ -*- */
/*
 * Copyright 2007,2013 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * GNU Radio is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * GNU Radio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with GNU Radio; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifndef INCLUDED_MODS_ARGPEAK_H
#define INCLUDED_MODS_ARGPEAK_H

#include <mods/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace mods {

    /*!
     * \brief Searches for a peak in the input vector. The peak is considered to
     * be the maximum value in the vector, as long as the maximum is higher than
     * the second maximum by a predefined difference.
     */
    class MODS_API argpeak : virtual public gr::sync_block
    {
    public:
      // gr::blocks::argpeak::sptr
      typedef boost::shared_ptr<argpeak> sptr;

      static sptr make(size_t vlen, float max_thresh);
    };

  } /* namespace mods */
} /* namespace gr */

#endif /* INCLUDED_MODS_ARGPEAK_H */
