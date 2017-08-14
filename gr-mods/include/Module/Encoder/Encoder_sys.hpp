/*!
 * \file
 * \brief Encodes a vector of information bits (a message) and adds some redundancy (parity bits).
 *
 * \section LICENSE
 * This file is under MIT license (https://opensource.org/licenses/MIT).
 */
#ifndef ENCODER_SYS_HPP_
#define ENCODER_SYS_HPP_

#include <sstream>

#include "Tools/Exception/exception.hpp"

#include "Encoder.hpp"

namespace aff3ct
{
namespace module
{
/*!
 * \class Encoder_sys
 *
 * \brief Encodes a vector of information bits (a message) and adds some redundancy (parity bits).
 *        The encoding is systematic: the informations bits are included in the final encoded codeword.
 *
 * \tparam B: type of the bits in the encoder.
 */
template <typename B = int>
class Encoder_sys : public Encoder<B>
{
public:
	/*!
	 * \brief Constructor.
	 *
	 * \param K:        number of information bits in the frame.
	 * \param N:        size of one frame.
	 * \param n_frames: number of frames to process in the Encoder_sys.
	 * \param name:     Encoder_sys's name.
	 */
	Encoder_sys(const int K, const int N, const int n_frames = 1, const std::string name = "Encoder_sys") 
	: Encoder<B>(K, N, n_frames, name.c_str())
	{
	}

	/*!
	 * \brief Destructor.
	 */
	virtual ~Encoder_sys()
	{
	}

	/*!
	 * \brief Encodes a vector of information bits (a message).
	 *
	 * \param U_K: a vector of information bits (a message).
	 * \param par: a vector of the parity bits only (without the systematic bits), may contain the tail bits.
	 *             par = [par | tail bit sys | tail bits par]
	 */
	template <class A = std::allocator<B>>
	void encode_sys(const std::vector<B,A>& U_K, std::vector<B,A>& par)
	{
		if (this->K * this->n_frames != (int)U_K.size())
		{
			std::stringstream message;
			message << "'U_K.size()' has to be equal to 'K' * 'n_frames' ('U_K.size()' = " << U_K.size()
			        << ", 'K' = " << this->K << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if ((this->N - this->K) * this->n_frames != (int)par.size())
		{
			std::stringstream message;
			message << "'par.size()' has to be equal to ('N' - 'K') * 'n_frames' ('par.size()' = " << par.size()
			        << ", 'N' = " << this->N << ", 'K' = " << this->K << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->encode_sys(U_K.data(), par.data());
	}

	virtual void encode_sys(const B *U_K, B *par)
	{
		for (auto f = 0; f < this->n_frames; f++)
			this->_encode_sys(U_K + f *            this->K,
			                  par + f * (this->N - this->K),
			                  f);
	}

protected:
	virtual void _encode_sys(const B *U_K, B *par, const int frame_id)
	{
		throw tools::unimplemented_error(__FILE__, __LINE__, __func__);
	}
};
}
}

#endif /* ENCODER_SYS_HPP_ */
