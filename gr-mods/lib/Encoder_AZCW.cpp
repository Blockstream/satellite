#include "Encoder_AZCW.hpp"

using namespace aff3ct::module;

template <typename B>
Encoder_AZCW<B>
::Encoder_AZCW(const int K, const int N, const int n_frames, const std::string name)
: Encoder_sys<B>(K, N, n_frames, name)
{
}

template <typename B>
Encoder_AZCW<B>
::~Encoder_AZCW()
{
}

template <typename B>
void Encoder_AZCW<B>
::encode(const B *U_K, B *X_N)
{
	std::fill(X_N, X_N + this->N * this->n_frames, (B)0);
}

template <typename B>
void Encoder_AZCW<B>
::encode_sys(const B *U_K, B *par)
{
	std::fill(par, par + (this->N - this->K) * this->n_frames, (B)0);
}

// ==================================================================================== explicit template instantiation 
#include "Tools/types.h"
#ifdef MULTI_PREC
template class aff3ct::module::Encoder_AZCW<B_8>;
template class aff3ct::module::Encoder_AZCW<B_16>;
template class aff3ct::module::Encoder_AZCW<B_32>;
template class aff3ct::module::Encoder_AZCW<B_64>;
#else
template class aff3ct::module::Encoder_AZCW<B>;
#endif
// ==================================================================================== explicit template instantiation
