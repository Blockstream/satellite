#ifndef TYPES_H_
#define TYPES_H_

#include <cstdint>

// type for the bits
//using B_8  = signed char;
//using B_16 = short;
//using B_32 = int;
//using B_64 = long long;
using B_8  = int8_t;
using B_16 = int16_t;
using B_32 = int32_t;
using B_64 = int64_t;

// type for the real numbers (before quantization)
using R_8  = float;
using R_16 = float;
using R_32 = float;
using R_64 = double;

// type for the real numbers (after  quantization)
using Q_8  = signed char;
using Q_16 = short;
using Q_32 = float;
using Q_64 = double;

// type for the real numbers inside the decoder (could be used or not depending on the decoder)
using QD_8  = short;
using QD_16 = short;
using QD_32 = float;
using QD_64 = double;

#if defined(PREC_8_BIT)
	using B  = B_8;
	using R  = R_8;
	using Q  = Q_8;
	using QD = QD_8;
#elif defined(PREC_16_BIT)
	using B  = B_16;
	using R  = R_16;
	using Q  = Q_16;
	using QD = QD_16;
#elif defined(PREC_64_BIT)
	using B  = B_64;
	using R  = R_64;
	using Q  = Q_64;
	using QD = QD_64;
#else // PREC_32_BIT
	using B  = B_32;
	using R  = R_32;
	using Q  = Q_32;
	using QD = QD_32;
	#ifndef PREC_32_BIT
	#define PREC_32_BIT
	#endif
#endif

#endif /* TYPES_H_ */
