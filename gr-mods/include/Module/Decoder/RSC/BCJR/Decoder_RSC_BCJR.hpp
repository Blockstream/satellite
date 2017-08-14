#ifndef DECODER_RSC_BCJR_HPP_
#define DECODER_RSC_BCJR_HPP_

#include <vector>
#include <mipp/mipp.h>

#include "../../Decoder_SISO_SIHO.hpp"

namespace aff3ct
{
namespace module
{
template <typename B = int, typename R = float>
class Decoder_RSC_BCJR : public Decoder_SISO_SIHO<B,R>
{
protected:
	const int  n_states;
	const int  n_ff;
	const bool buffered_encoding;

	const std::vector<std::vector<int>> &trellis;

	mipp::vector<R> sys, par; // input LLR from the channel
	mipp::vector<R> ext;      // extrinsic LLRs
	mipp::vector<B> s;        // hard decision

	Decoder_RSC_BCJR(const int K,
	                 const std::vector<std::vector<int>> &trellis,
	                 const bool buffered_encoding = true,
	                 const int n_frames = 1,
	                 const int simd_inter_frame_level = 1,
	                 const std::string name = "Decoder_RSC_BCJR");
	virtual ~Decoder_RSC_BCJR();

public:
	virtual int tail_length() const { return 2 * n_ff; }

protected:
	virtual void _load       (const R *Y_N                            );
	        void _decode_siho(const R *Y_N, B *V_K, const int frame_id);
	virtual void _store      (              B *V_K                    ) const;
};
}
}

#include "Decoder_RSC_BCJR.hxx"

#endif /* DECODER_RSC_BCJR_HPP_ */
