#include <cmath>     // min(), fabs(), copysign()...
#include <algorithm> // min()

#include "Tools/Exception/exception.hpp"

#include "max.h"

namespace aff3ct
{
namespace tools
{
template <typename R>
inline R max(const R& a, const R& b)
{
	return std::max(a, b);
}

template <typename R>
inline R max_linear(const R& a, const R& b)
{
	//return std::max(a, b) + std::max((R)0, (R)((R)0.25 * ((R)2.77 - std::abs(a - b))));
	return std::max(a, b) + std::max((R)0, (R)((R)0.301 - ((R)0.5 * std::abs(a - b))));
}

template <typename R>
inline R max_star(const R& a, const R& b) 
{
	// the two next statements are equivalent !
	// return std::max(a, b) + std::log((R)1 + std::exp(-std::abs(a - b)));
	return std::max(a, b) + (R)std::log1p(std::exp(-std::abs(a - b)));
}

template <typename R>
inline R max_star_safe(const R& a, const R& b) 
{
	throw runtime_error(__FILE__, __LINE__, __func__, "This method is not defined in fixed-point arithmetic.");

	return (R)0;
}

template <>
inline float max_star_safe(const float& a, const float& b)
{
	float d = std::abs(a - b);

	if (d >= (float)37 || std::isnan(d))
		d = (float)0.0; // exp(-d);
	else if (d < (float)37 && d >= 9)
		d = std::exp(-d);
	else
		d = (float)std::log1p(std::exp(-d));

	return std::max(a, b) + d;
}

template <>
inline double max_star_safe(const double& a, const double& b)
{
	double d = std::abs(a - b);

	if (d >= (double)37 || std::isnan(d))
		d = (double)0.0; // exp(-d);
	else if (d < (double)37 && d >= 9)
		d = std::exp(-d);
	else
		d = (double)std::log1p(std::exp(-d));

	return std::max(a, b) + d;
}

template <typename R>
inline mipp::Reg<R> max_i(const mipp::Reg<R> a, const mipp::Reg<R> b)
{
	return mipp::max(a, b);
}

template <typename R>
inline mipp::Reg<R> max_linear_i(const mipp::Reg<R> a, const mipp::Reg<R> b)
{
	mipp::Reg<R> zero = (R)0.0, cst1 = (R)0.301, cst2 = (R)0.5;
	return mipp::max(a, b) + mipp::max(zero, (cst1 - (mipp::abs(a - b) * cst2)));
}

template <typename R>
inline mipp::Reg<R> max_star_i(const mipp::Reg<R> a, const mipp::Reg<R> b)
{
	mipp::Reg<R> zero = (R)0.0, one = (R)1.0;
	return mipp::max(a, b) + mipp::log(one + mipp::exp(zero - mipp::abs(a - b)));
}
}
}
