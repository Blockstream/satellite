/* -*- c++ -*- */

#define MODS_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "mods_swig_doc.i"

%{
#include "mods/frame_sync_fast.h"
#include "mods/turbo_encoder.h"
#include "mods/turbo_decoder.h"
%}


%include "mods/frame_sync_fast.h"
GR_SWIG_BLOCK_MAGIC2(mods, frame_sync_fast);
%include "mods/turbo_encoder.h"
GR_SWIG_BLOCK_MAGIC2(mods, turbo_encoder);
%include "mods/turbo_decoder.h"
GR_SWIG_BLOCK_MAGIC2(mods, turbo_decoder);
