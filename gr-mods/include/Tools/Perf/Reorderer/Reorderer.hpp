/*!
 * \file
 * \brief Reorders a list of frames.
 *
 * \section LICENSE
 * This file is under MIT license (https://opensource.org/licenses/MIT).
 */
#ifndef REORDERER_HPP_
#define REORDERER_HPP_

#include <vector>

namespace aff3ct
{
namespace tools
{
/*!
 * \class Reorderer
 *
 * \brief Reorders a list of frames (the reordering code is dynamic).
 *
 * \tparam T: the type of data to reorder.
 */
template <typename T>
struct Reorderer
{
public:
	/*!
	 * \brief Applies the reordering from a list of frames.
	 *
	 * \param in_data:     a vector of frames (all the frames have to have the same size and the number of frames have
	 *                     to be a power of 2).
	 * \param out_data:    the reordered frames (interleaved regularly | e0_f0| e0_f1 | e0_f2 | e0_f3 | e1_f0 |...).
	 * \param data_length: the size of one frame.
	 */
	static void apply(const std::vector<const T*> in_data, T* out_data, const int data_length);

	/*!
	 * \brief Reverses the reordering.
	 *
	 * \param in_data:     the reordered frames (interleaved regularly | e0_f0| e0_f1 | e0_f2 | e0_f3 | e1_f0 |...),
	 *                     the number of frames have to be a power of 2 and have to have the same size.
	 * \param out_data:    a vector of frames.
	 * \param data_length: the size of one frame.
	 */
	static void apply_rev(const T* in_data, std::vector<T*> out_data, const int data_length);
};

/*!
 * \class Reorderer_static
 *
 * \brief Reorders a list of frames (the reordering code is static).
 *
 * \tparam T:        the type of data to reorder.
 * \tparam N_FRAMES: the number of frames to reorder (have to be a power of 2).
 */
template <typename T, int N_FRAMES>
struct Reorderer_static
{
public:
	/*!
	 * \brief Applies the reordering from a list of frames.
	 *
	 * \param in_data:     a vector of frames (all the frames have to have the same size and the number of frames have
	 *                     to be a power of 2).
	 * \param out_data:    the reordered frames (interleaved regularly | e0_f0| e0_f1 | e0_f2 | e0_f3 | e1_f0 |...).
	 * \param data_length: the size of one frame.
	 */
	static void apply(const std::vector<const T*> in_data, T* out_data, const int data_length);

	/*!
	 * \brief Reverses the reordering.
	 *
	 * \param in_data:     the reordered frames (interleaved regularly | e0_f0| e0_f1 | e0_f2 | e0_f3 | e1_f0 |...),
	 *                     the number of frames have to be a power of 2 and have to have the same size.
	 * \param out_data:    a vector of frames.
	 * \param data_length: the size of one frame.
	 */
	static void apply_rev(const T* in_data, std::vector<T*> out_data, const int data_length);
};
}
}

#include "Reorderer.hxx"

#endif /* REORDERER_HPP_ */
