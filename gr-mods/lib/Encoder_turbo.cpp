#include <vector>
#include <cmath>
#include <sstream>

#include "Tools/Exception/exception.hpp"

#include "Module/Encoder/Turbo/Encoder_turbo.hpp"

using namespace aff3ct::module;
using namespace aff3ct::tools;

// [sys | pn | pi | tailn | taili]

template <typename B>
Encoder_turbo<B>
::Encoder_turbo(const int& K, const int& N, const Interleaver<int> &pi,
                Encoder_sys<B> &enco_n, Encoder_sys<B> &enco_i, const int n_frames, const std::string name)
: Encoder<B>(K, N, n_frames, name),
  pi(pi),
  enco_n(enco_n),
  enco_i(enco_i),
  U_K_i(  K                                                                                  * n_frames),
  par_n(((N - (enco_n.tail_length() + enco_i.tail_length()) - K) / 2 + enco_n.tail_length()) * n_frames),
  par_i(((N - (enco_n.tail_length() + enco_i.tail_length()) - K) / 2 + enco_i.tail_length()) * n_frames)
{
	if (N - (enco_n.tail_length() + enco_i.tail_length()) != 3 * K)
	{
		std::stringstream message;
		message << "'N' - ('enco_n.tail_length()' + 'enco_i.tail_length()') has to be equal to 3 * 'K' ('N' = " << N
		        << ", 'enco_n.tail_length()' = " << enco_n.tail_length()
		        << ", 'enco_i.tail_length()' = " << enco_i.tail_length()
		        << ", 'K' = " << K << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	if ((int)pi.get_size() != K)
	{
		std::stringstream message;
		message << "'pi.get_size()' has to be equal to 'K' ('pi.get_size()' = " << pi.get_size()
		        << ", 'K' = " << K << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}
}

template <typename B>
void Encoder_turbo<B>
::encode(const B *U_K, B *X_N)
{
	pi.interleave(U_K, U_K_i.data(), 0, this->n_frames);

	enco_n.encode_sys(U_K,          par_n.data());
	enco_i.encode_sys(U_K_i.data(), par_i.data());

	const auto N_without_tb = this->N - (enco_n.tail_length() + enco_i.tail_length());
	const auto p_si = (N_without_tb - this->K) / 2; // size of the parity
	const auto t_n = enco_n.tail_length(); // tail_n
	const auto t_i = enco_i.tail_length(); // tail_i
	for (auto f = 0; f < this->n_frames; f++)
	{
		const auto off_U  = f * this->K;                    // off_U_K
		const auto off_X  = f * (N_without_tb + t_n + t_i); // off_U_N
		const auto off_pn = f * (p_si + t_n);               // off_par_n
		const auto off_pi = f * (p_si + t_i);               // off_par_i

		std::copy(  U_K         +off_U       ,   U_K         +off_U  +this->K  , X_N +off_X                       );
		std::copy(par_n.begin() +off_pn      , par_n.begin() +off_pn +p_si     , X_N +off_X +this->K              );
		std::copy(par_i.begin() +off_pi      , par_i.begin() +off_pi +p_si     , X_N +off_X +this->K + 1*p_si     );
		std::copy(par_n.begin() +off_pn +p_si, par_n.begin() +off_pn +p_si +t_n, X_N +off_X +this->K + 2*p_si     );
		std::copy(par_i.begin() +off_pi +p_si, par_i.begin() +off_pi +p_si +t_i, X_N +off_X +this->K + 2*p_si +t_n);
	}
}

// ==================================================================================== explicit template instantiation 
#include "Tools/types.h"
#ifdef MULTI_PREC
template class aff3ct::module::Encoder_turbo<B_8>;
template class aff3ct::module::Encoder_turbo<B_16>;
template class aff3ct::module::Encoder_turbo<B_32>;
template class aff3ct::module::Encoder_turbo<B_64>;
#else
template class aff3ct::module::Encoder_turbo<B>;
#endif
// ==================================================================================== explicit template instantiation
