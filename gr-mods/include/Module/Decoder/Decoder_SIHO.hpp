/*!
 * \file
 * \brief A Decoder is an algorithm dedicated to find the initial sequence of information bits (before the noise).
 *
 * \section LICENSE
 * This file is under MIT license (https://opensource.org/licenses/MIT).
 */
#ifndef DECODER_SIHO_HPP_
#define DECODER_SIHO_HPP_

#include <cmath>
#include <chrono>
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
 * \class Decoder_SIHO_i
 *
 * \brief A Decoder is an algorithm dedicated to find the initial sequence of information bits (before the noise).
 *
 * \tparam B: type of the bits in the Decoder.
 * \tparam R: type of the reals (floating-point or fixed-point representation) in the Decoder.
 *
 * The Decoder takes a soft input (real numbers) and return a hard output (bits).
 * Please use Decoder for inheritance (instead of Decoder_SIHO_i).
 */
template <typename B = int, typename R = float>
class Decoder_SIHO_i : public Module
{
private:
	const int n_inter_frame_rest;

	std::vector<R> Y_N;
	std::vector<B> V_KN;

protected:
	const int K; /*!< Number of information bits in one frame */
	const int N; /*!< Size of one frame (= number of bits in one frame) */
	const int simd_inter_frame_level; /*!< Number of frames absorbed by the SIMD instructions. */
	const int n_dec_waves;

	std::chrono::nanoseconds d_load_total;
	std::chrono::nanoseconds d_decod_total;
	std::chrono::nanoseconds d_store_total;

public:
	/*!
	 * \brief Constructor.
	 *
	 * \param K:                      number of information bits in the frame.
	 * \param N:                      size of one frame.
	 * \param n_frames:               number of frames to process in the Decoder.
	 * \param simd_inter_frame_level: number of frames absorbed by the SIMD instructions.
	 * \param name:                   Decoder's name.
	 */
	Decoder_SIHO_i(const int K, const int N, const int n_frames = 1, const int simd_inter_frame_level = 1,
	               std::string name = "Decoder_SIHO_i")
	: Module(n_frames, name),
	  n_inter_frame_rest(this->n_frames % simd_inter_frame_level),
	  Y_N (n_inter_frame_rest ? simd_inter_frame_level * N : 0),
	  V_KN(n_inter_frame_rest ? simd_inter_frame_level * N : 0),
	  K(K),
	  N(N),
	  simd_inter_frame_level(simd_inter_frame_level),
	  n_dec_waves((int)std::ceil((float)this->n_frames / (float)simd_inter_frame_level))
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

		if (simd_inter_frame_level <= 0)
		{
			std::stringstream message;
			message << "'simd_inter_frame_level' has to be greater than 0 ('simd_inter_frame_level' = "
			        << simd_inter_frame_level << ").";
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
	virtual ~Decoder_SIHO_i()
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
	 * \brief Gets the number of frames absorbed by the SIMD instructions.
	 *
	 * \return the number of frames absorbed by the SIMD instructions.
	 */
	int get_simd_inter_frame_level() const
	{
		return this->simd_inter_frame_level;
	}

	int get_n_dec_waves() const
	{
		return this->n_dec_waves;
	}

	/*!
	 * \brief Decodes the noisy frame.
	 *
	 * \param Y_N: a noisy frame.
	 * \param V_K: a decoded codeword (only the information bits).
	 */
	template <class AR = std::allocator<R>, class AB = std::allocator<B>>
	void decode_siho(const std::vector<R,AR>& Y_N, std::vector<B,AB>& V_K)
	{
		if (this->N * this->n_frames != (int)Y_N.size())
		{
			std::stringstream message;
			message << "'Y_N.size()' has to be equal to 'N' * 'n_frames' ('Y_N.size()' = " << Y_N.size()
			        << ", 'N' = " << this->N << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if (this->K * this->n_frames != (int)V_K.size())
		{
			std::stringstream message;
			message << "'V_K.size()' has to be equal to 'K' * 'n_frames' ('V_K.size()' = " << V_K.size()
			        << ", 'K' = " << this->K << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->decode_siho(Y_N.data(), V_K.data());
	}

	virtual void decode_siho(const R *Y_N, B *V_K)
	{
		this->d_load_total  = std::chrono::nanoseconds(0);
		this->d_decod_total = std::chrono::nanoseconds(0);
		this->d_store_total = std::chrono::nanoseconds(0);

		auto w = 0;
		for (w = 0; w < this->n_dec_waves -1; w++)
			this->_decode_siho(Y_N + w * this->N * this->simd_inter_frame_level,
			                   V_K + w * this->K * this->simd_inter_frame_level,
			                   w * simd_inter_frame_level);

		if (this->n_inter_frame_rest == 0)
			this->_decode_siho(Y_N + w * this->N * this->simd_inter_frame_level,
			                   V_K + w * this->K * this->simd_inter_frame_level,
			                   w * simd_inter_frame_level);
		else
		{
			const auto waves_off1 = w * this->simd_inter_frame_level * this->N;
			std::copy(Y_N + waves_off1,
			          Y_N + waves_off1 + this->n_inter_frame_rest * this->N,
			          this->Y_N.begin());

			this->_decode_siho(this->Y_N.data(), this->V_KN.data(), w * simd_inter_frame_level);

			const auto waves_off2 = w * this->simd_inter_frame_level * this->K;
			std::copy(this->V_KN.begin(),
			          this->V_KN.begin() + this->n_inter_frame_rest * this->K,
			          V_K + waves_off2);
		}
	}

	template <class AR = std::allocator<R>, class AB = std::allocator<B>>
	void decode_siho_coded(const std::vector<R,AR>& Y_N, std::vector<B,AB>& V_N)
	{
		if (this->N * this->n_frames != (int)Y_N.size())
		{
			std::stringstream message;
			message << "'Y_N.size()' has to be equal to 'N' * 'n_frames' ('Y_N.size()' = " << Y_N.size()
			        << ", 'N' = " << this->N << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if (this->N * this->n_frames != (int)V_N.size())
		{
			std::stringstream message;
			message << "'V_N.size()' has to be equal to 'N' * 'n_frames' ('V_N.size()' = " << V_N.size()
			        << ", 'N' = " << this->N << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->decode_siho_coded(Y_N.data(), V_N.data());
	}

	virtual void decode_siho_coded(const R *Y_N, B *V_N)
	{
		this->d_load_total  = std::chrono::nanoseconds(0);
		this->d_decod_total = std::chrono::nanoseconds(0);
		this->d_store_total = std::chrono::nanoseconds(0);

		auto w = 0;
		for (w = 0; w < this->n_dec_waves -1; w++)
			this->_decode_siho_coded(Y_N + w * this->N * this->simd_inter_frame_level,
			                         V_N + w * this->N * this->simd_inter_frame_level,
			                         w * simd_inter_frame_level);

		if (this->n_inter_frame_rest == 0)
			this->_decode_siho_coded(Y_N + w * this->N * this->simd_inter_frame_level,
			                         V_N + w * this->N * this->simd_inter_frame_level,
			                         w * simd_inter_frame_level);
		else
		{
			const auto waves_off1 = w * this->simd_inter_frame_level * this->N;
			std::copy(Y_N + waves_off1,
			          Y_N + waves_off1 + this->n_inter_frame_rest * this->N,
			          this->Y_N.begin());

			this->_decode_siho_coded(this->Y_N.data(), this->V_KN.data(), w * simd_inter_frame_level);

			const auto waves_off2 = w * this->simd_inter_frame_level * this->N;
			std::copy(this->V_KN.begin(),
			          this->V_KN.begin() + this->n_inter_frame_rest * this->N,
			          V_N + waves_off2);
		}
	}

	/*!
	 * \brief Gets the duration of the data loading in the decoding process.
	 *
	 * \return the duration of the data loading in the decoding process.
	 */
	std::chrono::nanoseconds get_load_duration() const
	{
		return this->d_load_total;
	}

	/*!
	 * \brief Gets the duration of the decoding process (without loads and stores).
	 *
	 * \return the duration of the decoding process (without loads and stores).
	 */
	std::chrono::nanoseconds get_decode_duration() const
	{
		return this->d_decod_total;
	}

	/*!
	 * \brief Gets the duration of the data storing in the decoding process.
	 *
	 * \return the duration of the data storing in the decoding process.
	 */
	std::chrono::nanoseconds get_store_duration() const
	{
		return this->d_store_total;
	}

protected:
	virtual void _decode_siho(const R *Y_N, B *V_K, const int frame_id)
	{
		throw tools::unimplemented_error(__FILE__, __LINE__, __func__);
	}

	virtual void _decode_siho_coded(const R *Y_N, B *V_N, const int frame_id)
	{
		throw tools::unimplemented_error(__FILE__, __LINE__, __func__);
	}
};
}
}

#include "SC_Decoder_SIHO.hpp"

#endif /* DECODER_SIHO_HPP_ */
