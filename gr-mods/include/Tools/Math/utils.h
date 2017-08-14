#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#include <algorithm>
#include <sstream>
#include <vector>
#include <cstdint>
#include <limits>

#include "Tools/Exception/exception.hpp"

namespace aff3ct
{
namespace tools
{
template <typename R> inline R       div2(R       val) { return val * (R)0.500; }
template <>           inline int32_t div2(int32_t val) { return val >> 1;       }
template <>           inline int16_t div2(int16_t val) { return val >> 1;       }
template <>           inline int8_t  div2(int8_t  val) { return val >> 1;       }

template <typename R> inline R       div4(R       val) { return val * (R)0.250; }
template <>           inline int32_t div4(int32_t val) { return val >> 2;       }
template <>           inline int16_t div4(int16_t val) { return val >> 2;       }
template <>           inline int8_t  div4(int8_t  val) { return val >> 2;       }

template <typename R> inline R       div8(R       val) { return val * (R)0.125; }
template <>           inline int32_t div8(int32_t val) { return val >> 3;       }
template <>           inline int16_t div8(int16_t val) { return val >> 3;       }
template <>           inline int8_t  div8(int8_t  val) { return val >> 3;       }

// init value depending on the domain
template <typename R>
constexpr R init_LR () { return (R)1; }

template <typename R>
constexpr R init_LLR() { return (R)0; }

// saturate values in function of the domain
template <typename R>
constexpr R sat_val() { return std::numeric_limits<R>::infinity(); }

template <> constexpr double  sat_val<double >() { return std::numeric_limits<double>::infinity(); }
template <> constexpr float   sat_val<float  >() { return std::numeric_limits<float >::infinity(); }
template <> constexpr int32_t sat_val<int32_t>() { return 1073741823;                              }
template <> constexpr int16_t sat_val<int16_t>() { return 16382;                                   }
template <> constexpr int8_t  sat_val<int8_t >() { return 63;                                      }

template <typename R>
constexpr std::pair<R, R> sat_vals() { return std::make_pair(-sat_val<R>(), sat_val<R>()); }

// return the initial value for a bit
template <typename B>
constexpr B bit_init() { return (B)(((B)1) << (sizeof(B) * 8 -1)); }

// make a saturation on a the value "val"
template <typename T>
inline T saturate(const T val, const T min, const T max) { return std::min(std::max(val, min), max); }

// make a saturation on a full vector
template <typename T, class A = std::allocator<T>>
inline void saturate(std::vector<T,A> &array, const T min, const T max)
{
	const auto loop_size = (int)array.size();
	for (auto i = 0; i < loop_size; i++)
		array[i] = saturate<T>(array[i], min, max);
}

template <typename B, typename R>
B sgn(R val) { return (B)((R(0) < val) - (val < R(0))); }


template <typename T>
constexpr bool is_power_of_2(T x)
{
	return (x > 0) && !(x & (x - 1));
}

template <typename R, typename function_type>
inline R integral(function_type func, const R min, const R max, const int number_steps)
{
	if (max < min)
	{
		std::stringstream message;
		message << "'max' has to be equal or greater than 'min' ('max' = " << max << ", 'min' = " << min << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	if (number_steps <= 0)
	{
		std::stringstream message;
		message << "'number_steps' has to be greater than 0 ('number_steps' = " << number_steps << ").";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}

	R step = (max - min) / number_steps; // width of rectangle
	R area = (R)0;

	for (auto i = 0; i < number_steps; i++)
		area += func(min + ((R)i + (R)0.5) * step) * step;

	return area;
}
}
}

#endif /* MATH_UTILS_H */
