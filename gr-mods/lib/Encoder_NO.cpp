#include <stdexcept>

#include "Encoder_NO.hpp"

using namespace aff3ct::module;

template <typename B>
Encoder_NO<B>
::Encoder_NO(const int K, const int n_frames, const std::string name)
: Encoder<B>(K, K, n_frames, name)
{
}

template <typename B>
Encoder_NO<B>
::~Encoder_NO()
{
}

template <typename B>
void Encoder_NO<B>
::encode(const B *U_K, B *X_K)
{
	std::copy(U_K, U_K + this->K * this->n_frames, X_K);
}

// ==================================================================================== explicit template instantiation 
#include "Tools/types.h"
#ifdef MULTI_PREC
template class aff3ct::module::Encoder_NO<B_8>;
template class aff3ct::module::Encoder_NO<B_16>;
template class aff3ct::module::Encoder_NO<B_32>;
template class aff3ct::module::Encoder_NO<B_64>;
#else
template class aff3ct::module::Encoder_NO<B>;
#endif
// ==================================================================================== explicit template instantiation
