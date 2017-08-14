#include <chrono>
#include <limits>
#include <sstream>
#include <mipp/mipp.h>

#include "Tools/Exception/exception.hpp"
#include "Tools/Perf/Reorderer/Reorderer.hpp"

#include "Decoder_RSC_BCJR.hpp"

namespace aff3ct
{
namespace module
{
template <typename B, typename R>
Decoder_RSC_BCJR<B,R>
::Decoder_RSC_BCJR(const int K, 
                   const std::vector<std::vector<int>> &trellis, 
                   const bool buffered_encoding,
                   const int n_frames,
                   const int simd_inter_frame_level,
                   const std::string name)
: Decoder_SISO_SIHO<B,R>(K, 2*(K + (int)std::log2(trellis[0].size())), n_frames, simd_inter_frame_level, name),
  n_states((int)trellis[0].size()),
  n_ff((int)std::log2(n_states)),
  buffered_encoding(buffered_encoding),
  trellis(trellis),
  sys((K+n_ff) * simd_inter_frame_level + mipp::nElReg<R>()),
  par((K+n_ff) * simd_inter_frame_level + mipp::nElReg<R>()),
  ext( K       * simd_inter_frame_level + mipp::nElReg<R>()),
  s  ( K       * simd_inter_frame_level + mipp::nElReg<B>())
{
	if (!tools::is_power_of_2(n_states))
	{
		std::stringstream message;
		message << "'n_states' has to be a power of 2 ('n_states' = " << n_states << ").";
		throw tools::invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}
}

template <typename B, typename R>
Decoder_RSC_BCJR<B,R>
::~Decoder_RSC_BCJR()
{
}

template <typename B, typename R>
void Decoder_RSC_BCJR<B,R>
::_load(const R *Y_N)
{
	if (buffered_encoding)
	{
		const auto tail     = this->tail_length();
		const auto n_frames = Decoder_SIHO<B,R>::get_simd_inter_frame_level();

		if (n_frames == 1)
		{
			std::copy(Y_N + 0*this->K, Y_N + 1*this->K, sys.begin());
			std::copy(Y_N + 1*this->K, Y_N + 2*this->K, par.begin());

			// tails bit
			std::copy(Y_N + 2*this->K         , Y_N + 2*this->K + tail/2, par.begin() +this->K);
			std::copy(Y_N + 2*this->K + tail/2, Y_N + 2*this->K + tail  , sys.begin() +this->K);
		}
		else
		{
			const auto frame_size = 2*this->K + tail;

			std::vector<const R*> frames(n_frames);
			for (auto f = 0; f < n_frames; f++)
				frames[f] = Y_N + f*frame_size;
			tools::Reorderer<R>::apply(frames, sys.data(), this->K);

			for (auto f = 0; f < n_frames; f++)
				frames[f] = Y_N + f*frame_size +this->K;
			tools::Reorderer<R>::apply(frames, par.data(), this->K);

			// tails bit
			for (auto f = 0; f < n_frames; f++)
				frames[f] = Y_N + f*frame_size + 2*this->K + tail/2;
			tools::Reorderer<R>::apply(frames, &sys[this->K*n_frames], tail/2);

			for (auto f = 0; f < n_frames; f++)
				frames[f] = Y_N + f*frame_size + 2*this->K;
			tools::Reorderer<R>::apply(frames, &par[this->K*n_frames], tail/2);
		}
	}
	else
	{
		const auto n_frames = this->get_simd_inter_frame_level();

		// reordering
		for (auto i = 0; i < this->K + n_ff; i++)
		{
			for (auto f = 0; f < n_frames; f++)
			{
				sys[(i*n_frames) +f] = Y_N[f*2*(this->K +n_ff) + i*2 +0];
				par[(i*n_frames) +f] = Y_N[f*2*(this->K +n_ff) + i*2 +1];
			}
		}
	}
}

template <typename B, typename R>
void Decoder_RSC_BCJR<B,R>
::_decode_siho(const R *Y_N, B *V_K, const int frame_id)
{
	auto t_load = std::chrono::steady_clock::now(); // ----------------------------------------------------------- LOAD
	_load(Y_N);
	auto d_load = std::chrono::steady_clock::now() - t_load;

	auto t_decod = std::chrono::steady_clock::now(); // -------------------------------------------------------- DECODE
	this->_decode_siso(sys.data(), par.data(), ext.data(), frame_id);
	auto d_decod = std::chrono::steady_clock::now() - t_decod;

	auto t_store = std::chrono::steady_clock::now(); // --------------------------------------------------------- STORE
	// take the hard decision
	for (auto i = 0; i < this->K * this->simd_inter_frame_level; i += mipp::nElReg<R>())
	{
		const auto r_post = mipp::Reg<R>(&ext[i]) + mipp::Reg<R>(&sys[i]);

		// s[i] = post[i] < 0;
		const auto r_s = mipp::cast<R,B>(r_post) >> (sizeof(B) * 8 - 1);

		r_s.store(&s[i]);
	}

	_store(V_K);
	auto d_store = std::chrono::steady_clock::now() - t_store;

	this->d_load_total  += d_load;
	this->d_decod_total += d_decod;
	this->d_store_total += d_store;
}

template <typename B, typename R>
void Decoder_RSC_BCJR<B,R>
::_store(B *V_K) const
{
	if (this->get_simd_inter_frame_level() == 1)
	{
		std::copy(s.begin(), s.begin() + this->K, V_K);
	}
	else // inter frame => output reordering
	{
		const auto n_frames = this->get_simd_inter_frame_level();

		std::vector<B*> frames(n_frames);
		for (auto f = 0; f < n_frames; f++)
			frames[f] = V_K + f*this->K;
		tools::Reorderer<B>::apply_rev(s.data(), frames, this->K);
	}
}
}
}
