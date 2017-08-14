/*!
 * \file
 * \brief Encodes a vector of information bits (a message) and adds some redundancy (parity bits).
 *
 * \section LICENSE
 * This file is under MIT license (https://opensource.org/licenses/MIT).
 */
#ifndef ENCODER_HPP_
#define ENCODER_HPP_

#include <string>
#include <vector>
#include <sstream>

#include "Tools/Exception/exception.hpp"

#include "Module/Module.hpp"

namespace aff3ct
{
namespace module
{
/*!
 * \class Encoder_i
 *
 * \brief Encodes a vector of information bits (a message) and adds some redundancy (parity bits).
 *
 * \tparam B: type of the bits in the encoder.
 *
 * Please use Encoder for inheritance (instead of Encoder_i)
 */
template <typename B = int>
class Encoder_i : public Module
{
protected:
	const int K; /*!< Number of information bits in one frame */
	const int N; /*!< Size of one frame (= number of bits in one frame) */

public:
	/*!
	 * \brief Constructor.
	 *
	 * \param K:        number of information bits in the frame.
	 * \param N:        size of one frame.
	 * \param n_frames: number of frames to process in the Encoder.
	 * \param name:     Encoder's name.
	 */
	Encoder_i(const int K, const int N, const int n_frames = 1, const std::string name = "Encoder_i")
	: Module(n_frames, name), K(K), N(N)
	{
		if (K <= 0)
		{
			std::stringstream message;
			message << "'K' has to be greater than 0 ('K' = " << K << ").";
			throw tools::invalid_argument(__FILE__, __LINE__, __func__, message.str());
		}

		if (N <= 0)
		{
			std::stringstream message;
			message << "'N' has to be greater than 0 ('N' = " << N << ").";
			throw tools::invalid_argument(__FILE__, __LINE__, __func__, message.str());
		}

		if (K > N)
		{
			std::stringstream message;
			message << "'K' has to be smaller or equal to 'N' ('K' = " << K << ", 'N' = " << N << ").";
			throw tools::invalid_argument(__FILE__, __LINE__, __func__, message.str());
		}
	}

	/*!
	 * \brief Destructor.
	 */
	virtual ~Encoder_i()
	{
	}

	int get_K() const
	{
		return this->K;
	}

	int get_N() const
	{
		return this->N;
	}

	/*!
	 * \brief Encodes a vector of information bits (a message).
	 *
	 * \param U_K: a vector of information bits (a message).
	 * \param X_N: an encoded frame with redundancy added (parity bits).
	 */
	template <class A = std::allocator<B>>
	void encode(const std::vector<B,A>& U_K, std::vector<B,A>& X_N)
	{
		if (this->K * this->n_frames != (int)U_K.size())
		{
			std::stringstream message;
			message << "'U_K.size()' has to be equal to 'K' * 'n_frames' ('U_K.size()' = " << U_K.size()
			        << ", 'K' = " << this->K
			        << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if (this->N * this->n_frames != (int)X_N.size())
		{
			std::stringstream message;
			message << "'X_N.size()' has to be equal to 'N' * 'n_frames' ('X_N.size()' = " << X_N.size()
			        << ", 'N' = " << this->N << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->encode(U_K.data(), X_N.data());
	}

	virtual void encode(const B *U_K, B *X_N)
	{
		for (auto f = 0; f < this->n_frames; f++)
			this->_encode(U_K + f * this->K,
			              X_N + f * this->N,
			              f);
	}

	/*!
	 * \brief Gets the number of tail bits.
	 *
	 * Some encoders need to add some additional bits in order to work. This is often the case for the cyclic codes.
	 * Other codes do not require this feature and so, the tail bits length is 0.
	 *
	 * \return the number of tail bits.
	 */
	virtual int tail_length() const { return 0; }

protected:
	virtual void _encode(const B *U_K, B *X_N, const int frame_id)
	{
		throw tools::unimplemented_error(__FILE__, __LINE__, __func__);
	}
};
}
}

#include "SC_Encoder.hpp"

#endif /* ENCODER_HPP_ */
