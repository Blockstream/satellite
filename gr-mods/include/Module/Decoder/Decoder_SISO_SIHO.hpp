/*!
 * \file
 * \brief A Decoder_SISO is both a "Soft Input Hard Output" decoder and a "Soft Input Soft Output" decoder.
 *
 * \section LICENSE
 * This file is under MIT license (https://opensource.org/licenses/MIT).
 */
#ifndef DECODER_SISO_SIHO_HPP_
#define DECODER_SISO_SIHO_HPP_

#include "Decoder_SIHO.hpp"
#include "Decoder_SISO.hpp"

namespace aff3ct
{
namespace module
{
/*!
 * \class Decoder_SISO_SIHO
 *
 * \brief A Decoder_SISO_SIHO is both a "Soft Input Hard Output" decoder and a "Soft Input Soft Output" decoder.
 *
 * \tparam B: type of the bits in the decoder.
 * \tparam R: type of the reals (floating-point or fixed-point representation) in the decoder.
 */
template <typename B = int, typename R = float>
class Decoder_SISO_SIHO : public Decoder_SIHO<B,R>, public Decoder_SISO<R>
{
public:
	/*!
	 * \brief Constructor.
	 *
	 * \param K:                      number of information bits in the frame.
	 * \param N:                      size of one frame.
	 * \param n_frames:               number of frames to process in the decoder.
	 * \param simd_inter_frame_level: number of frames absorbed by the SIMD instructions.
	 * \param name:                   decoder name.
	 */
	Decoder_SISO_SIHO(const int K, const int N, const int n_frames = 1, const int simd_inter_frame_level = 1,
	                  std::string name = "Decoder_SISO_SIHO")
	: Decoder_SIHO<B,R>(K, N, n_frames, simd_inter_frame_level, name          ),
	  Decoder_SISO<  R>(K, N, n_frames, simd_inter_frame_level, name + "_siso")
	{
	}

	/*!
	 * \brief Destructor.
	 */
	virtual ~Decoder_SISO_SIHO() {}

	/*!
	 * \brief Gets the number of frames.
	 *
	 * \return the number of frames to process in the decoder.
	 */
	virtual int get_n_frames() const
	{
		return Decoder_SISO<R>::n_frames;
	}

	int get_K() const
	{
		return Decoder_SISO<R>::K_siso;
	}

	int get_N() const
	{
		return Decoder_SISO<R>::N_siso;
	}

	/*!
	 * \brief Gets the number of frames absorbed by the SIMD instructions.
	 *
	 * \return the number of frames absorbed by the SIMD instructions.
	 */
	int get_simd_inter_frame_level() const
	{
		return Decoder_SISO<R>::simd_inter_frame_level_siso;
	}

	int get_n_dec_waves() const
	{
		return Decoder_SISO<R>::n_dec_waves;
	}
};
}
}

#endif /* DECODER_SISO_SIHO_HPP_ */
