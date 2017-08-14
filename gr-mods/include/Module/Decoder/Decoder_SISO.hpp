/*!
 * \file
 * \brief A SISO (Soft Input Soft Output) is a type of decoder which takes a soft input and return a soft output.
 *
 * \section LICENSE
 * This file is under MIT license (https://opensource.org/licenses/MIT).
 */
#ifndef DECODER_SISO_HPP_
#define DECODER_SISO_HPP_

#include <cmath>
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
 * \class Decoder_SISO_i
 *
 * \brief A Decoder_SISO (Soft Input Soft Output) is a type of decoder which takes a soft input and return a soft output.
 *
 * \tparam R: type of the reals (floating-point or fixed-point representation) in the Decoder_SISO.
 *
 * Please use Decoder_SISO for inheritance (instead of Decoder_SISO_i).
 */
template <typename R = float>
class Decoder_SISO_i : public Module
{
private:
	const int n_inter_frame_rest_siso;

	std::vector<R> Y_N1;
	std::vector<R> Y_N2;

protected:
	const int K_siso; /*!< Number of information bits in one frame */
	const int N_siso; /*!< Size of one frame (= number of bits in one frame) */
	const int simd_inter_frame_level_siso;
	const int n_dec_waves_siso;

public:
	/*!
	 * \brief Constructor.
	 *
	 * \param K:                      number of information bits in the frame.
	 * \param N:                      size of one frame.
	 * \param n_frames:               number of frames to process in the Decoder_SISO.
	 * \param simd_inter_frame_level: number of frames absorbed by the SIMD instructions.
	 * \param name:                   decoder name.
	 */
	Decoder_SISO_i(const int K, const int N, const int n_frames = 1, const int simd_inter_frame_level = 1,
	               std::string name = "Decoder_SISO_i")
	: Module(n_frames, name),
	  n_inter_frame_rest_siso(this->n_frames % simd_inter_frame_level),
	  Y_N1(n_inter_frame_rest_siso ? simd_inter_frame_level * N : 0),
	  Y_N2(n_inter_frame_rest_siso ? simd_inter_frame_level * N : 0),
	  K_siso(K),
	  N_siso(N),
	  simd_inter_frame_level_siso(simd_inter_frame_level),
	  n_dec_waves_siso((int)std::ceil((float)this->n_frames / (float)simd_inter_frame_level))
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
	virtual ~Decoder_SISO_i() {};

	int get_K() const
	{
		return this->K_siso;
	}

	int get_N() const
	{
		return this->N_siso;
	}

	/*!
	 * \brief Gets the number of frames absorbed by the SIMD instructions.
	 *
	 * \return the number of frames absorbed by the SIMD instructions.
	 */
	int get_simd_inter_frame_level() const
	{
		return this->simd_inter_frame_level_siso;
	}

	int get_n_dec_waves() const
	{
		return this->n_dec_waves_siso;
	}

	/*!
	 * \brief Decodes a given noisy codeword. This prototype supposes that the encoded frame is systematic, can't be
	 *        used otherwise.
	 *
	 * \param sys: systematic LLRs (original noised information bits) from the channel.
	 * \param par: parity LLRs from the channel.
	 * \param ext: extrinsic information about the systematic bits.
	 */
	template <class A = std::allocator<R>>
	void decode_siso(const std::vector<R,A> &sys, const std::vector<R,A> &par, std::vector<R,A> &ext,
	                 const int n_frames = -1)
	{
		if (n_frames != -1 && n_frames <= 0)
		{
			std::stringstream message;
			message << "'n_frames' has to be greater than 0 or equal to -1 ('n_frames' = " << n_frames << ").";
			throw tools::invalid_argument(__FILE__, __LINE__, __func__, message.str());
		}

		const int real_n_frames = (n_frames != -1) ? n_frames : this->n_frames;

		if ((this->K_siso + this->tail_length() / 2) * real_n_frames != (int)sys.size())
		{
			std::stringstream message;
			message << "'sys.size()' has to be equal to ('K_siso' + 'tail_length()' / 2) * 'real_n_frames' "
			        << "('sys.size()' = " << sys.size()
			        << ", 'K_siso' = " << this->K_siso
			        << ", 'tail_length()' = " << this->tail_length()
			        << ", 'real_n_frames' = " << real_n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if (((this->N_siso - this->K_siso) - this->tail_length() / 2) * real_n_frames != (int)par.size())
		{
			std::stringstream message;
			message << "'par.size()' has to be equal to (('N_siso' - 'K_siso') - 'tail_length()' / 2) * "
			        << "'real_n_frames' ('par.size()' = " << par.size()
			        << ", 'N_siso' = " << this->N_siso
			        << ", 'K_siso' = " << this->K_siso
			        << ", 'tail_length()' = " << this->tail_length()
			        << ", 'real_n_frames' = " << real_n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if (this->K_siso * real_n_frames != (int)ext.size())
		{
			std::stringstream message;
			message << "'ext.size()' has to be equal to 'K_siso' * 'real_n_frames' ('ext.size()' = " << ext.size()
			        << ", 'K_siso' = " << this->K_siso << ", 'real_n_frames' = " << real_n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->decode_siso(sys.data(), par.data(), ext.data(), real_n_frames);
	}

	virtual void decode_siso(const R *sys, const R *par, R *ext, const int n_frames = -1)
	{
		const int real_n_frames = (n_frames != -1) ? n_frames : this->n_frames;

		const auto n_dec_waves_siso = real_n_frames / this->simd_inter_frame_level_siso;
		for (auto w = 0; w < n_dec_waves_siso; w++)
			this->_decode_siso(sys + w * (               this->K_siso) * this->simd_inter_frame_level_siso,
			                   par + w * (this->N_siso - this->K_siso) * this->simd_inter_frame_level_siso,
			                   ext + w * (               this->K_siso) * this->simd_inter_frame_level_siso,
			                   w * simd_inter_frame_level_siso);
	}

	/*!
	 * \brief Decodes a given noisy codeword.
	 *
	 * \param Y_N1: a completely noisy codeword from the channel.
	 * \param Y_N2: an extrinsic information about all the bits in the frame.
	 */
	template <class A = std::allocator<R>>
	void decode_siso(const std::vector<R,A> &Y_N1, std::vector<R,A> &Y_N2)
	{
		if (this->N_siso * this->n_frames != (int)Y_N1.size())
		{
			std::stringstream message;
			message << "'Y_N1.size()' has to be equal to 'N_siso' * 'n_frames' ('Y_N1.size()' = " << Y_N1.size()
			        << ", 'N_siso' = " << this->N_siso << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if (this->N_siso * this->n_frames != (int)Y_N2.size())
		{
			std::stringstream message;
			message << "'Y_N2.size()' has to be equal to 'N_siso' * 'n_frames' ('Y_N2.size()' = " << Y_N2.size()
			        << ", 'N_siso' = " << this->N_siso << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->decode_siso(Y_N1.data(), Y_N2.data());
	}

	virtual void decode_siso(const R *Y_N1, R *Y_N2)
	{
		auto w = 0;
		for (w = 0; w < this->n_dec_waves_siso -1; w++)
			this->_decode_siso(Y_N1 + w * this->N_siso * this->simd_inter_frame_level_siso,
			                   Y_N2 + w * this->N_siso * this->simd_inter_frame_level_siso,
			                   w * simd_inter_frame_level_siso);

		if (this->n_inter_frame_rest_siso == 0)
			this->_decode_siso(Y_N1 + w * this->N_siso * this->simd_inter_frame_level_siso,
			                   Y_N2 + w * this->N_siso * this->simd_inter_frame_level_siso,
			                   w * simd_inter_frame_level_siso);
		else
		{
			const auto waves_off1 = w * this->simd_inter_frame_level_siso * this->N_siso;
			std::copy(Y_N1 + waves_off1,
			          Y_N1 + waves_off1 + this->n_inter_frame_rest_siso * this->N_siso,
			          this->Y_N1.begin());

			this->_decode_siso(this->Y_N1.data(), this->Y_N2.data(), w * simd_inter_frame_level_siso);

			const auto waves_off2 = w * this->simd_inter_frame_level_siso * this->N_siso;
			std::copy(this->Y_N2.begin(),
			          this->Y_N2.begin() + this->n_inter_frame_rest_siso * this->N_siso,
			          Y_N2 + waves_off2);
		}
	}

	/*!
	 * \brief Gets the number of tail bits.
	 *
	 * \return the number of tail bits.
	 */
	virtual int tail_length() const
	{
		return 0;
	}

protected:
	virtual void _decode_siso(const R *sys, const R *par, R *ext, const int frame_id)
	{
		throw tools::unimplemented_error(__FILE__, __LINE__, __func__);
	}

	virtual void _decode_siso(const R *Y_N1, R *Y_N2, const int frame_id)
	{
		throw tools::unimplemented_error(__FILE__, __LINE__, __func__);
	}
};
}
}

#include "SC_Decoder_SISO.hpp"

#endif /* DECODER_SISO_HPP_ */
