#include <chrono>

#include "Module/Decoder/NO/Decoder_NO.hpp"

using namespace aff3ct::module;

template <typename B, typename R>
Decoder_NO<B,R>
::Decoder_NO(const int K, const int n_frames, const std::string name)
: Decoder_SISO_SIHO<B,R>(K, K, n_frames, 1, name)
{
}

template <typename B, typename R>
Decoder_NO<B,R>
::~Decoder_NO()
{
}

template <typename B, typename R>
void Decoder_NO<B,R>
::_decode_siso(const R *sys, const R *par, R *ext, const int frame_id)
{
	std::copy(sys, sys + this->K, ext);
}

template <typename B, typename R>
void Decoder_NO<B,R>
::_decode_siso(const R *Y_K1, R *Y_K2, const int frame_id)
{
	std::copy(Y_K1, Y_K1 + this->K, Y_K2);
}

template <typename B, typename R>
void Decoder_NO<B,R>
::_decode_siho(const R *Y_K, B *V_K, const int frame_id)
{
	auto t_store = std::chrono::steady_clock::now(); // --------------------------------------------------------- STORE
	// take the hard decision
	auto vec_loop_size = (this->K / mipp::nElReg<R>()) * mipp::nElReg<R>();
	for (auto i = 0; i < vec_loop_size; i += mipp::nElReg<R>())
	{
		const auto r_Y_N = mipp::Reg<R>(&Y_K[i]);
		const auto r_s = mipp::cast<R,B>(r_Y_N) >> (sizeof(B) * 8 - 1); // s[i] = Y_Ki] < 0;
		r_s.store(&V_K[i]);
	}
	for (auto i = vec_loop_size; i < this->K; i++)
		V_K[i] = Y_K[i] < 0;
	auto d_store = std::chrono::steady_clock::now() - t_store;

	this->d_store_total += d_store;
}

// ==================================================================================== explicit template instantiation 
#include "Tools/types.h"
#ifdef MULTI_PREC
template class aff3ct::module::Decoder_NO<B_8,Q_8>;
template class aff3ct::module::Decoder_NO<B_16,Q_16>;
template class aff3ct::module::Decoder_NO<B_32,Q_32>;
template class aff3ct::module::Decoder_NO<B_64,Q_64>;
#else
template class aff3ct::module::Decoder_NO<B,Q>;
#endif
// ==================================================================================== explicit template instantiation
