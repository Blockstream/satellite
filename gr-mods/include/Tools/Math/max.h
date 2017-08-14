#ifndef MAX_H
#define MAX_H

#include <mipp/mipp.h>

#ifndef _MSC_VER
#ifndef __forceinline
#define __forceinline inline __attribute__((always_inline))
#endif
#endif

namespace aff3ct
{
namespace tools
{
// -------------------------------------------------------------------------- special function prototypes for templates

template <typename R>
using proto_max = R (*)(const R& a, const R& b);

template <typename R>
using proto_max_i = mipp::Reg<R> (*)(const mipp::Reg<R> a, const mipp::Reg<R> b);

// ------------------------------------------------------------------------------------------- special function headers

template <typename R> __forceinline R max          (const R& a, const R& b);
template <typename R> __forceinline R max_linear   (const R& a, const R& b);
template <typename R> __forceinline R max_star     (const R& a, const R& b);
template <typename R> __forceinline R max_star_safe(const R& a, const R& b);

template <typename R> __forceinline mipp::Reg<R> max_i       (const mipp::Reg<R> a, const mipp::Reg<R> b);
template <typename R> __forceinline mipp::Reg<R> max_linear_i(const mipp::Reg<R> a, const mipp::Reg<R> b);
template <typename R> __forceinline mipp::Reg<R> max_star_i  (const mipp::Reg<R> a, const mipp::Reg<R> b);
}
}

#include "max.hxx"

#endif /* MAX_H */
