/*!
 * \file
 * \brief Interleaves or deinterleaves a vector.
 *
 * \section LICENSE
 * This file is under MIT license (https://opensource.org/licenses/MIT).
 */
#ifndef INTERLEAVER_HPP_
#define INTERLEAVER_HPP_

#include <typeinfo>
#include <string>
#include <vector>
#include <sstream>
#include <mipp/mipp.h>

#include "Tools/Exception/exception.hpp"

#include "Module/Module.hpp"

namespace aff3ct
{
namespace module
{
/*!
 * \class Interleaver_i
 *
 * \brief Interleaves or deinterleaves a vector.
 *
 * \tparam T: type of the integers used in the lookup tables to store indirections.
 *
 * Please use Interleaver for inheritance (instead of Interleaver_i)
 */
template <typename T = int>
class Interleaver_i : public Module
{
protected:
	const int size;
	bool uniform;
	std::vector<T> pi;     /*!< Lookup table for the interleaving process */
	std::vector<T> pi_inv; /*!< Lookup table for the deinterleaving process */

	bool init_called;

public:
	/*!
	 * \brief Constructor.
	 *
	 * \param size:     number of the data to interleave or to deinterleave.
	 * \param n_frames: number of frames to process in the Interleaver.
	 * \param name:     Interleaver's name.
	 */
	Interleaver_i(const int size, const bool uniform = false, const int n_frames = 1,
	              const std::string name = "Interleaver_i")
	: Module(n_frames, name),
	  size(size), uniform(uniform), pi(size * n_frames), pi_inv(size * n_frames), init_called(false)
	{
		if (size <= 0)
		{
			std::stringstream message;
			message << "'size' has to be greater than 0 ('size' = " << size << ").";
			throw tools::invalid_argument(__FILE__, __LINE__, __func__, message.str());
		}
	}

	/*!
	 * \brief Destructor.
	 */
	virtual ~Interleaver_i()
	{
	}

	void init()
	{
		this->refresh();
		init_called = true;
	}

	bool is_uniform()
	{
		return this->uniform;
	}

	/*!
	 * \brief Gets the lookup table required for the interleaving process.
	 *
	 * \return a vector of indirections.
	 */
	const std::vector<T>& get_lut() const
	{
		return pi;
	}

	/*!
	 * \brief Gets the lookup table required for the deinterleaving process.
	 *
	 * \return a vector of indirections.
	 */
	const std::vector<T>& get_lut_inv() const
	{
		return pi_inv;
	}

	int get_size() const
	{
		return size;
	}

	/*!
	 * \brief Interleaves a vector.
	 *
	 * \tparam D: type of data in the input and the output vectors.
	 *
	 * \param natural_vec:      an input vector in the natural domain.
	 * \param interleaved_vec:  an output vector in the interleaved domain.
	 * \param frame_reordering: true means that the frames have been reordered for efficient SIMD computations. In this
	 *                          case the interleaving process is different (true supposes that there is more than one
	 *                          frame to interleave).
	 * \param n_frames:         you should not use this parameter unless you know what you are doing, this parameter
	 *                          redefine the number of frames to interleave specifically in this method.
	 */
	template <typename D, class A = std::allocator<D>>
	inline void interleave(const std::vector<D,A> &natural_vec, std::vector<D,A> &interleaved_vec) const
	{
		if (natural_vec.size() != interleaved_vec.size())
		{
			std::stringstream message;
			message << "'natural_vec.size()' has to be equal to 'interleaved_vec.size()' ('natural_vec.size()' = "
			        << natural_vec.size() << ", 'interleaved_vec.size()' = " << interleaved_vec.size() << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if ((int)natural_vec.size() < this->get_size() * this->n_frames)
		{
			std::stringstream message;
			message << "'natural_vec.size()' has to be equal or greater than 'get_size()' * 'n_frames' "
			        << "('natural_vec.size()' = " << natural_vec.size() << ", 'get_size()' = " << this->get_size()
			        << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->interleave(natural_vec.data(), interleaved_vec.data());
	}

	template <typename D>
	inline void interleave(const D *natural_vec, D *interleaved_vec) const
	{
		for (auto f = 0; f < this->n_frames; f++)
			this->interleave(natural_vec     + f * this->get_size(),
			                 interleaved_vec + f * this->get_size(),
			                 f);
	}

	template <typename D>
	inline void interleave(const D *natural_vec, D *interleaved_vec,
	                       const int  frame_id,
	                       const int  n_frames = 1,
	                       const bool frame_reordering = false) const
	{
		this->_interleave(natural_vec, interleaved_vec, pi, frame_reordering, n_frames, frame_id);
	}

	/*!
	 * \brief Deinterleaves a vector.
	 *
	 * \tparam D: type of data in the input and the output vectors.
	 *
	 * \param interleaved_vec:  an input vector in the interleaved domain.
	 * \param natural_vec:      an output vector in the natural domain.
	 * \param frame_reordering: true means that the frames have been reordered for efficient SIMD computations. In this
	 *                          case the deinterleaving process is different (true supposes that there is more than one
	 *                          frame to deinterleave).
	 * \param n_frames:         you should not use this parameter unless you know what you are doing, this parameter
	 *                          redefine the number of frames to deinterleave specifically in this method.
	 */
	template <typename D, class A = std::allocator<D>>
	inline void deinterleave(const std::vector<D,A> &interleaved_vec, std::vector<D,A> &natural_vec) const
	{
		if (natural_vec.size() != interleaved_vec.size())
		{
			std::stringstream message;
			message << "'natural_vec.size()' has to be equal to 'interleaved_vec.size()' ('natural_vec.size()' = "
			        << natural_vec.size() << ", 'interleaved_vec.size()' = " << interleaved_vec.size() << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		if ((int)natural_vec.size() < this->get_size() * this->n_frames)
		{
			std::stringstream message;
			message << "'natural_vec.size()' has to be equal or greater than 'get_size()' * 'n_frames' "
			        << "('natural_vec.size()' = " << natural_vec.size() << ", 'get_size()' = " << this->get_size()
			        << ", 'n_frames' = " << this->n_frames << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->deinterleave(interleaved_vec.data(), natural_vec.data());
	}

	template <typename D>
	inline void deinterleave(const D *interleaved_vec, D *natural_vec) const
	{
		for (auto f = 0; f < this->n_frames; f++)
			this->deinterleave(interleaved_vec + f * this->get_size(),
			                   natural_vec     + f * this->get_size(),
			                   f);
	}

	template <typename D>
	inline void deinterleave(const D *interleaved_vec, D *natural_vec,
	                         const int  frame_id,
	                         const int  n_frames = 1,
	                         const bool frame_reordering = false) const
	{
		this->_interleave(interleaved_vec, natural_vec, pi_inv, frame_reordering, n_frames, frame_id);
	}

	/*!
	 * \brief Compares two interleavers: the comparison only considers the lookup tables.
	 *
	 * \param interleaver: an other interleaver.
	 *
	 * \return true if the two interleavers are the same (if they have the same lookup tables), false otherwise.
	 */
	bool operator==(Interleaver_i<T> &interleaver) const
	{
		if (interleaver.size != this->size)
			return false;

		if (interleaver.uniform != this->uniform)
			return false;

		if (interleaver.pi.size() != this->pi.size())
			return false;

		if (interleaver.pi_inv.size() != this->pi_inv.size())
			return false;

		for (auto i = 0; i < (int)this->pi.size(); i++)
			if (this->pi[i] != interleaver.pi[i])
				return false;

		for (auto i = 0; i < (int)this->pi_inv.size(); i++)
			if (this->pi_inv[i] != interleaver.pi_inv[i])
				return false;

		return true;
	}

	bool operator!=(Interleaver_i<T> &interleaver) const
	{
		return !(*this == interleaver);
	}

	void refresh()
	{
		this->gen_lut(this->pi.data(), 0);
		for (auto i = 0; i < (int)this->get_size(); i++)
			this->pi_inv[this->pi[i]] = i;

		if (uniform)
		{
			for (auto f = 1; f < this->n_frames; f++)
			{
				const auto off = f * this->size;

				this->gen_lut(this->pi.data() + off, f);

				for (auto i = 0; i < this->get_size(); i++)
					this->pi_inv[off + this->pi[off +i]] = i;
			}
		}
		else
		{
			for (auto f = 1; f < this->n_frames; f++)
			{
				std::copy(pi    .data(), pi    .data() + size, pi    .data() + f * size);
				std::copy(pi_inv.data(), pi_inv.data() + size, pi_inv.data() + f * size);
			}
		}
	}

protected:
	/*!
	 * \brief Generates the interleaving and deinterleaving lookup tables. This method defines the interleaver and have
	 *        to be called in the constructor.
	 */
	virtual void gen_lut(T *lut, const int frame_id) = 0;

private:
	template <typename D>
	inline void _interleave(const D *in_vec, D *out_vec,
	                        const std::vector<T> &lookup_table,
	                        const bool frame_reordering,
	                        const int  n_frames,
	                        const int  frame_id) const
	{
		if (!init_called)
		{
			std::string message = "'init' method has to be called first, before trying to (de)interleave something.";
			throw tools::length_error(__FILE__, __LINE__, __func__, message);
		}

		if (frame_reordering)
		{
			if (!this->uniform)
			{
				// vectorized interleaving
				if (n_frames == mipp::nElReg<D>())
				{
					for (auto i = 0; i < this->get_size(); i++)
						mipp::store<D>(&out_vec[i * mipp::nElReg<D>()],
						               mipp::load<D>(&in_vec[lookup_table[i] * mipp::nElReg<D>()]));
				}
				else
				{
					for (auto i = 0; i < this->get_size(); i++)
					{
						const auto off1 =              i  * n_frames;
						const auto off2 = lookup_table[i] * n_frames;
						for (auto f = 0; f < n_frames; f++)
							out_vec[off1 +f] = in_vec[off2 +f];
					}
				}
			}
			else
			{
				auto cur_frame_id = frame_id % this->n_frames;
				for (auto f = 0; f < n_frames; f++)
				{
					const auto lut = lookup_table.data() + cur_frame_id * this->get_size();
					for (auto i = 0; i < this->get_size(); i++)
						out_vec[i * n_frames +f] = in_vec[lut[i] * n_frames +f];
					cur_frame_id = (cur_frame_id +1) % this->n_frames;
				}
			}
		}
		else
		{
			if (!this->uniform)
			{
				// TODO: vectorize this code with the new AVX gather instruction
				for (auto f = 0; f < n_frames; f++)
				{
					const auto off = f * this->get_size();
					for (auto i = 0; i < this->get_size(); i++)
						out_vec[off + i] = in_vec[off + lookup_table[i]];
				}
			}
			else
			{
				auto cur_frame_id = frame_id % this->n_frames;
				// TODO: vectorize this code with the new AVX gather instruction
				for (auto f = 0; f < n_frames; f++)
				{
					const auto lut = lookup_table.data() + cur_frame_id * this->get_size();
					const auto off = f * this->get_size();
					for (auto i = 0; i < this->get_size(); i++)
						out_vec[off + i] = in_vec[off + lut[i]];
					cur_frame_id = (cur_frame_id +1) % this->n_frames;
				}
			}
		}
	}
};
}
}

#include "SC_Interleaver.hpp"

#endif /* INTERLEAVER_HPP_ */
