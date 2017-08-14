#include <string>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <stdexcept>
#include <sstream>

#include "Tools/Exception/exception.hpp"
#include "Tools/Perf/Reorderer/Reorderer.hpp"

#include "Module/Decoder/Turbo/Decoder_turbo.hpp"

using namespace aff3ct::module;
using namespace aff3ct::tools;

template <typename B, typename R>
Decoder_turbo<B,R>
::Decoder_turbo(const int& K,
                const int& N,
                const int& n_ite,
                const Interleaver<int> &pi,
                Decoder_SISO<R> &siso_n,
                Decoder_SISO<R> &siso_i,
                const bool buffered_encoding,
                const std::string name)
: Decoder_SIHO<B,R>(K, N, siso_n.get_n_frames(), siso_n.get_simd_inter_frame_level(), name),
  n_ite(n_ite),
  buffered_encoding(buffered_encoding),
  pi(pi),
  siso_n(siso_n),
  siso_i(siso_i),
  l_sn ((K                                                        + (siso_n.tail_length() / 2)) * siso_n.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_si ((K                                                        + (siso_i.tail_length() / 2)) * siso_i.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_sen((K                                                        + (siso_n.tail_length() / 2)) * siso_n.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_sei((K                                                        + (siso_i.tail_length() / 2)) * siso_i.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_pn (((N - (siso_n.tail_length() + siso_i.tail_length()) -K)/2 + (siso_n.tail_length() / 2)) * siso_n.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_pi (((N - (siso_n.tail_length() + siso_i.tail_length()) -K)/2 + (siso_i.tail_length() / 2)) * siso_i.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_e1n((K                                                                                    ) * siso_n.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_e2n((K                                                                                    ) * siso_n.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_e1i((K                                                                                    ) * siso_i.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  l_e2i((K                                                                                    ) * siso_i.get_simd_inter_frame_level() + mipp::nElReg<R>()),
  s    ((K                                                                                    ) * siso_n.get_simd_inter_frame_level())
{
	if (siso_n.get_K() != K)
	{
		std::stringstream message;
		message << "'siso_n.get_K()' has to be equal to 'K' ('siso_n.get_K()' = " << siso_n.get_K()
		        << ", 'K' = " << K << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	if (siso_i.get_K() != K)
	{
		std::stringstream message;
		message << "'siso_i.get_K()' has to be equal to 'K' ('siso_i.get_K()' = " << siso_i.get_K()
		        << ", 'K' = " << K << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	if (N - (siso_n.tail_length() + siso_i.tail_length()) != K * 3)
	{
		std::stringstream message;
		message << "'N' - ('siso_n.tail_length()' + 'siso_i.tail_length()') has to be equal to 'K' * 3 ('N' = "
		        << N << ", 'siso_n.tail_length()' = " << siso_n.tail_length()
		        << ", 'siso_i.tail_length()' = " << siso_i.tail_length() << ", 'K' = " << K << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	if (n_ite <= 0)
	{
		std::stringstream message;
		message << "'n_ite' has to be greater than 0 ('n_ite' = " << n_ite << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	if ((int)pi.get_size() != K)
	{
		std::stringstream message;
		message << "'pi.get_size()' has to be equal to 'K' ('pi.get_size()' = " << pi.get_size()
		        << ", 'K' = " << K << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (siso_n.get_n_frames() != siso_i.get_n_frames())
	{
		std::stringstream message;
		message << "'siso_n.get_n_frames()' has to be equal to 'siso_i.get_n_frames()' ('siso_n.get_n_frames()' = "
		        << siso_n.get_n_frames() << ", 'siso_i.get_n_frames()' = " << siso_i.get_n_frames() << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	if (siso_n.get_simd_inter_frame_level() != siso_i.get_simd_inter_frame_level())
	{
		std::stringstream message;
		message << "'siso_n.get_simd_inter_frame_level()' has to be equal to 'siso_i.get_simd_inter_frame_level()' "
		        << "('siso_n.get_simd_inter_frame_level()' = " << siso_n.get_simd_inter_frame_level()
		        << ", 'siso_i.get_simd_inter_frame_level()' = " << siso_i.get_simd_inter_frame_level() << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}
}

template <typename B, typename R>
Decoder_turbo<B,R>
::~Decoder_turbo()
{
}

template <typename B, typename R>
void Decoder_turbo<B,R>
::add_handler_siso_n(std::function<bool(const int,
                                        const mipp::vector<R>&,
                                              mipp::vector<R>&,
                                              mipp::vector<B>&)> callback)
{
	this->callbacks_siso_n.push_back(callback);
}

template <typename B, typename R>
void Decoder_turbo<B,R>
::add_handler_siso_i(std::function<bool(const int, const mipp::vector<R>&, mipp::vector<R>&)> callback)
{
	this->callbacks_siso_i.push_back(callback);
}

template <typename B, typename R>
void Decoder_turbo<B,R>
::add_handler_end(std::function<void(const int)> callback)
{
	this->callbacks_end.push_back(callback);
}

template <typename B, typename R>
void Decoder_turbo<B,R>
::_load(const R *Y_N, const int frame_id)
{
	if (buffered_encoding)
		this->buffered_load(Y_N, frame_id);
	else
		this->standard_load(Y_N, frame_id);
}

template <typename B, typename R>
void Decoder_turbo<B,R>
::buffered_load(const R *Y_N, const int frame_id)
{
	const auto tail_n = siso_n.tail_length();
	const auto tail_i = siso_i.tail_length();
	
	const auto N_without_tb = this->N - (siso_n.tail_length() + siso_i.tail_length());

	const auto p_size = (N_without_tb - this->K) / 2; // size of the parity
	if (this->get_simd_inter_frame_level() == 1)
	{
		std::copy(Y_N                     , Y_N + this->K           , l_sn.begin());
		std::copy(Y_N + this->K           , Y_N + this->K + 1*p_size, l_pn.begin());
		std::copy(Y_N + this->K + 1*p_size, Y_N + this->K + 2*p_size, l_pi.begin());
		pi.interleave(l_sn.data(), l_si.data(), frame_id, this->get_simd_inter_frame_level());

		// tails bit in the natural domain
		std::copy(Y_N + N_without_tb           , Y_N + N_without_tb + tail_n/2, l_pn.begin() +p_size);
		std::copy(Y_N + N_without_tb + tail_n/2, Y_N + N_without_tb + tail_n  , l_sn.begin() +p_size);

		// tails bit in the interleaved domain
		std::copy(Y_N + N_without_tb + tail_n           , Y_N + N_without_tb + tail_n + tail_i/2, l_pi.begin() +p_size);
		std::copy(Y_N + N_without_tb + tail_n + tail_i/2, Y_N + N_without_tb + tail_n + tail_i  , l_si.begin() +p_size);
	}
	else
	{
		const auto n_frames = this->get_simd_inter_frame_level();
		const auto frame_size = this->N;

		std::vector<const R*> frames(n_frames);
		for (auto f = 0; f < n_frames; f++)
			frames[f] = Y_N + f*frame_size;
		Reorderer<R>::apply(frames, l_sn.data(), this->K);

		for (auto f = 0; f < n_frames; f++)
			frames[f] = Y_N + f*frame_size +this->K;
		Reorderer<R>::apply(frames, l_pn.data(), p_size);

		for (auto f = 0; f < n_frames; f++)
			frames[f] = Y_N + f*frame_size +this->K + p_size;
		Reorderer<R>::apply(frames, l_pi.data(), p_size);

		pi.interleave(l_sn.data(), l_si.data(), frame_id, this->get_simd_inter_frame_level(), true);

		// tails bit in the natural domain
		for (auto f = 0; f < n_frames; f++)
			frames[f] = Y_N + f*frame_size +N_without_tb + tail_n/2;
		Reorderer<R>::apply(frames, &l_sn[this->K*n_frames], tail_n/2);

		for (auto f = 0; f < n_frames; f++)
			frames[f] = Y_N + f*frame_size +N_without_tb;
		Reorderer<R>::apply(frames, &l_pn[p_size*n_frames], tail_n/2);

		// tails bit in the interleaved domain
		for (auto f = 0; f < n_frames; f++)
			frames[f] = Y_N + f*frame_size +N_without_tb + tail_n + tail_i/2;
		Reorderer<R>::apply(frames, &l_si[this->K*n_frames], tail_i/2);

		for (auto f = 0; f < n_frames; f++)
			frames[f] = Y_N + f*frame_size +N_without_tb + tail_n;
		Reorderer<R>::apply(frames, &l_pi[p_size*n_frames], tail_i/2);
	}
	std::fill(l_e1n.begin(), l_e1n.end(), (R)0);
}

template <typename B, typename R>
void Decoder_turbo<B,R>
::standard_load(const R *Y_N, const int frame_id)
{
	const auto tail_n = siso_n.tail_length();
	const auto tail_i = siso_i.tail_length();

	if (this->get_simd_inter_frame_level() == 1)
	{
		for (auto i = 0; i < this->K; i++)
		{
			l_sn[i] = Y_N[i*3 +0];
			l_pn[i] = Y_N[i*3 +1];
			l_pi[i] = Y_N[i*3 +2];
		}
		pi.interleave(l_sn.data(), l_si.data(), frame_id, this->get_simd_inter_frame_level());

		// tails bit in the natural domain
		for (auto i = 0; i < tail_n/2; i++)
		{
			l_sn[this->K +i] = Y_N[this->K*3 + 2*i +0];
			l_pn[this->K +i] = Y_N[this->K*3 + 2*i +1];
		}

		// tails bit in the interleaved domain
		for (auto i = 0; i < tail_i/2; i++)
		{
			l_si[this->K +i] = Y_N[this->K*3 + tail_n + 2*i +0];
			l_pi[this->K +i] = Y_N[this->K*3 + tail_n + 2*i +1];
		}
	}
	else // inter frame => input reordering
	{
		const auto n_frames = this->get_simd_inter_frame_level();

		for (auto i = 0; i < this->K; i++)
		{
			for (auto j = 0; j < n_frames; j++)
			{
				l_sn[i*n_frames +j] = Y_N[j*((this->K*3) + tail_n + tail_i) + i * 3 +0];
				l_pn[i*n_frames +j] = Y_N[j*((this->K*3) + tail_n + tail_i) + i * 3 +1];
				l_pi[i*n_frames +j] = Y_N[j*((this->K*3) + tail_n + tail_i) + i * 3 +2];
			}
		}
		pi.interleave(l_sn.data(), l_si.data(), frame_id, this->get_simd_inter_frame_level(), true);

		// tails bit in the natural domain
		for (auto i = 0; i < tail_n/2; i++)
		{
			for (auto j = 0; j < n_frames; j++)
			{
				l_sn[(this->K +i)*n_frames +j] = Y_N[j*((this->K*3) + tail_n + tail_i) + this->K*3 + 2*i +0];
				l_pn[(this->K +i)*n_frames +j] = Y_N[j*((this->K*3) + tail_n + tail_i) + this->K*3 + 2*i +1];
			}
		}

		// tails bit in the interleaved domain
		for (auto i = 0; i < tail_i/2; i++)
		{
			for (auto j = 0; j < n_frames; j++)
			{
				l_si[(this->K +i)*n_frames +j] = Y_N[j*((this->K*3) + tail_n + tail_i) + this->K*3 + tail_n + 2*i +0];
				l_pi[(this->K +i)*n_frames +j] = Y_N[j*((this->K*3) + tail_n + tail_i) + this->K*3 + tail_n + 2*i +1];
			}
		}
	}

	std::fill(l_e1n.begin(), l_e1n.end(), (R)0);
}

template <typename B, typename R>
void Decoder_turbo<B,R>
::_store(B *V_K) const
{
	if (this->get_simd_inter_frame_level() == 1)
	{
		std::copy(s.data(), s.data() + this->K, V_K);
	}
	else // inter frame => output reordering
	{
		const auto n_frames = this->get_simd_inter_frame_level();

		std::vector<B*> frames(n_frames);
		for (auto f = 0; f < n_frames; f++)
			frames[f] = V_K + f*this->K;
		Reorderer<B>::apply_rev(s.data(), frames, this->K);
	}
}

// ==================================================================================== explicit template instantiation
#include "Tools/types.h"
#ifdef MULTI_PREC
template class aff3ct::module::Decoder_turbo<B_8,Q_8>;
template class aff3ct::module::Decoder_turbo<B_16,Q_16>;
template class aff3ct::module::Decoder_turbo<B_32,Q_32>;
template class aff3ct::module::Decoder_turbo<B_64,Q_64>;
#else
template class aff3ct::module::Decoder_turbo<B,Q>;
#endif
// ==================================================================================== explicit template instantiation
