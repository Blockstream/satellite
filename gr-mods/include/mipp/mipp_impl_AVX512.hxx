#include "mipp.h"

// -------------------------------------------------------------------------------------------------------- X86 AVX-512
// --------------------------------------------------------------------------------------------------------------------
#if defined(__MIC__) || defined(__KNCNI__) || defined(__AVX512__) || defined(__AVX512F__)

	// ---------------------------------------------------------------------------------------------------------- blend
	template <>
	inline reg blend<double>(const reg v1, const reg v2, const msk m) {
		return _mm512_castpd_ps(_mm512_mask_blend_pd((__mmask8)m, _mm512_castps_pd(v2), _mm512_castps_pd(v1)));
	}

	template <>
	inline reg blend<float>(const reg v1, const reg v2, const msk m) {
		return _mm512_mask_blend_ps((__mmask16)m, v2, v1);
	}

	template <>
	inline reg blend<int64_t>(const reg v1, const reg v2, const msk m) {
		return _mm512_castsi512_ps(_mm512_mask_blend_epi64((__mmask8)m, _mm512_castps_si512(v2), _mm512_castps_si512(v1)));
	}


	template <>
	inline reg blend<int32_t>(const reg v1, const reg v2, const msk m) {
		return _mm512_castsi512_ps(_mm512_mask_blend_epi32((__mmask16)m, _mm512_castps_si512(v2), _mm512_castps_si512(v1)));
	}

#if defined(__AVX512BW__)
	template <>
	inline reg blend<int16_t>(const reg v1, const reg v2, const msk m) {
		return _mm512_castsi512_ps(_mm512_mask_blend_epi16((__mmask32)m, _mm512_castps_si512(v2), _mm512_castps_si512(v1)));
	}

	template <>
	inline reg blend<int8_t>(const reg v1, const reg v2, const msk m) {
		return _mm512_castsi512_ps(_mm512_mask_blend_epi8((__mmask64)m, _mm512_castps_si512(v2), _mm512_castps_si512(v1)));
	}
#endif


	// ---------------------------------------------------------------------------------------------------------- loadu
#if defined(__AVX512F__)
	template <>
	inline reg loadu<float>(const float *mem_addr) {
		return _mm512_loadu_ps(mem_addr);
	}

	template <>
	inline reg loadu<double>(const double *mem_addr) {
		return _mm512_castpd_ps(_mm512_loadu_pd(mem_addr));
	}

	template <>
	inline reg loadu<int64_t>(const int64_t *mem_addr) {
		return _mm512_loadu_ps((const float*) mem_addr);
	}

	template <>
	inline reg loadu<int32_t>(const int32_t *mem_addr) {
		return _mm512_loadu_ps((const float*) mem_addr);
	}

	template <>
	inline reg loadu<int16_t>(const int16_t *mem_addr) {
		return _mm512_loadu_ps((const float*) mem_addr);
	}

	template <>
	inline reg loadu<int8_t>(const int8_t *mem_addr) {
		return _mm512_loadu_ps((const float*) mem_addr);
	}
#endif

	// ----------------------------------------------------------------------------------------------------------- load
#ifdef MIPP_ALIGNED_LOADS
	template <>
	inline reg load<float>(const float *mem_addr) {
		return _mm512_load_ps(mem_addr);
	}

	template <>
	inline reg load<double>(const double *mem_addr) {
		return _mm512_castpd_ps(_mm512_load_pd(mem_addr));
	}

	template <>
	inline reg load<int64_t>(const int64_t *mem_addr) {
		return _mm512_load_ps((const float*) mem_addr);
	}

	template <>
	inline reg load<int32_t>(const int32_t *mem_addr) {
		return _mm512_load_ps((const float*) mem_addr);
	}

	template <>
	inline reg load<int16_t>(const int16_t *mem_addr) {
		return _mm512_load_ps((const float*) mem_addr);
	}

	template <>
	inline reg load<int8_t>(const int8_t *mem_addr) {
		return _mm512_load_ps((const float*) mem_addr);
	}
#else
	template <>
	inline reg load<float>(const float *mem_addr) {
		return mipp::loadu<float>(mem_addr);
	}

	template <>
	inline reg load<double>(const double *mem_addr) {
		return mipp::loadu<double>(mem_addr);
	}

	template <>
	inline reg load<int64_t>(const int64_t *mem_addr) {
		return mipp::loadu<int64_t>(mem_addr);
	}

	template <>
	inline reg load<int32_t>(const int32_t *mem_addr) {
		return mipp::loadu<int32_t>(mem_addr);
	}

	template <>
	inline reg load<int16_t>(const int16_t *mem_addr) {
		return mipp::loadu<int16_t>(mem_addr);
	}

	template <>
	inline reg load<int8_t>(const int8_t *mem_addr) {
		return mipp::loadu<int8_t>(mem_addr);
	}
#endif

	// --------------------------------------------------------------------------------------------------------- storeu
#if defined(__AVX512F__)
	template <>
	inline void storeu<float>(float *mem_addr, const reg v) {
		_mm512_storeu_ps(mem_addr, v);
	}

	template <>
	inline void storeu<double>(double *mem_addr, const reg v) {
		_mm512_storeu_pd(mem_addr, _mm512_castps_pd(v));
	}

	template <>
	inline void storeu<int64_t>(int64_t *mem_addr, const reg v) {
		_mm512_storeu_ps((float *)mem_addr, v);
	}

	template <>
	inline void storeu<int32_t>(int32_t *mem_addr, const reg v) {
		_mm512_storeu_ps((float *)mem_addr, v);
	}

	template <>
	inline void storeu<int16_t>(int16_t *mem_addr, const reg v) {
		_mm512_storeu_ps((float *)mem_addr, v);
	}

	template <>
	inline void storeu<int8_t>(int8_t *mem_addr, const reg v) {
		_mm512_storeu_ps((float *)mem_addr, v);
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- store
#ifdef MIPP_ALIGNED_LOADS
	template <>
	inline void store<float>(float *mem_addr, const reg v) {
		_mm512_store_ps(mem_addr, v);
	}

	template <>
	inline void store<double>(double *mem_addr, const reg v) {
		_mm512_store_pd(mem_addr, _mm512_castps_pd(v));
	}

	template <>
	inline void store<int64_t>(int64_t *mem_addr, const reg v) {
		_mm512_store_ps((float *)mem_addr, v);
	}

	template <>
	inline void store<int32_t>(int32_t *mem_addr, const reg v) {
		_mm512_store_ps((float *)mem_addr, v);
	}

	template <>
	inline void store<int16_t>(int16_t *mem_addr, const reg v) {
		_mm512_store_ps((float *)mem_addr, v);
	}

	template <>
	inline void store<int8_t>(int8_t *mem_addr, const reg v) {
		_mm512_store_ps((float *)mem_addr, v);
	}
#else
	template <>
	inline void store<float>(float *mem_addr, const reg v) {
		mipp::storeu<float>(mem_addr, v);
	}

	template <>
	inline void store<double>(double *mem_addr, const reg v) {
		mipp::storeu<double>(mem_addr, v);
	}

	template <>
	inline void store<int64_t>(int64_t *mem_addr, const reg v) {
		mipp::storeu<int64_t>(mem_addr, v);
	}

	template <>
	inline void store<int32_t>(int32_t *mem_addr, const reg v) {
		mipp::storeu<int32_t>(mem_addr, v);
	}

	template <>
	inline void store<int16_t>(int16_t *mem_addr, const reg v) {
		mipp::storeu<int16_t>(mem_addr, v);
	}

	template <>
	inline void store<int8_t>(int8_t *mem_addr, const reg v) {
		mipp::storeu<int8_t>(mem_addr, v);
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- cmpeq
	template <>
	inline msk cmpeq<double>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_pd_mask(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _CMP_EQ_OQ);
	}

	template <>
	inline msk cmpeq<float>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_ps_mask(v1, v2, _CMP_EQ_OQ);
	}

#if defined(__AVX512F__)
	template <>
	inline msk cmpeq<int64_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpeq_epi64_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	template <>
	inline msk cmpeq<int32_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpeq_epi32_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

#if defined(__AVX512BW__)
	template <>
	inline msk cmpeq<int16_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpeq_epi16_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

	template <>
	inline msk cmpeq<int8_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpeq_epi8_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif


	// ----------------------------------------------------------------------------------------------------------- set1
#ifdef __AVX512F__
	template <>
	inline reg set1<float>(const float val) {
		return _mm512_set1_ps(val);
	}

	template <>
	inline reg set1<double>(const double val) {
		return _mm512_castpd_ps(_mm512_set1_pd(val));
	}

	template <>
	inline reg set1<int64_t>(const int64_t val) {
		return _mm512_castsi512_ps(_mm512_set1_epi64(val));
	}

	template <>
	inline reg set1<int32_t>(const int32_t val) {
		return _mm512_castsi512_ps(_mm512_set1_epi32(val));
	}

	template <>
	inline reg set1<int16_t>(const int16_t val) {
		return _mm512_castsi512_ps(_mm512_set1_epi16(val));
	}

	template <>
	inline reg set1<int8_t>(const int8_t val) {
		return _mm512_castsi512_ps(_mm512_set1_epi8(val));
	}

#elif defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg set1<double>(const double val) {
		double init[8] __attribute__((aligned(64))) = {val, val, val, val, val, val, val, val};
		return load<double>(init);
	}

	template <>
	inline reg set1<float>(const float val) {
		float init[16] __attribute__((aligned(64))) = {val, val, val, val, val, val, val, val, 
		                                               val, val, val, val, val, val, val, val};
		return load<float>(init);
	}

	template <>
	inline reg set1<int64_t>(const int64_t val) {
		int64_t init[8] __attribute__((aligned(64))) = {val, val, val, val, val, val, val, val};
		return load<int64_t>(init);
	}

	template <>
	inline reg set1<int32_t>(const int32_t val) {
		int32_t init[16] __attribute__((aligned(64))) = {val, val, val, val, val, val, val, val,
		                                                 val, val, val, val, val, val, val, val};
		return load<int32_t>(init);
	}
#endif

	// ---------------------------------------------------------------------------------------------------- set1 (mask)
	template <>
	inline msk set1<8>(const bool val) {
		auto r1 = set1<int64_t>(val ? (uint64_t)0xFFFFFFFFFFFFFFFF : 0);
		auto r2 = set1<int64_t>(      (uint64_t)0xFFFFFFFFFFFFFFFF    );

		return (msk) cmpeq<int64_t>(r1, r2);
	}

	template <>
	inline msk set1<16>(const bool val) {
		auto r1 = set1<int32_t>(val ? 0xFFFFFFFF : 0);
		auto r2 = set1<int32_t>(      0xFFFFFFFF    );

		return (msk) cmpeq<int32_t>(r1, r2);
	}

	template <>
	inline msk set1<32>(const bool val) {
		auto r1 = set1<int16_t>(val ? 0xFFFF : 0);
		auto r2 = set1<int16_t>(      0xFFFF    );

		return (msk) cmpeq<int16_t>(r1, r2);
	}

	template <>
	inline msk set1<64>(const bool val) {
		auto r1 = set1<int8_t>(val ? 0xFF : 0);
		auto r2 = set1<int8_t>(      0xFF    );

		return (msk) cmpeq<int8_t>(r1, r2);
	}

	// ----------------------------------------------------------------------------------------------------------- set0
#if defined(__AVX512F__)
	template <>
	inline reg set0<double>() {
		return _mm512_castpd_ps(_mm512_setzero_pd());
	}

	template <>
	inline reg set0<float>() {
		return _mm512_setzero_ps();
	}

	template <>
	inline reg set0<int32_t>() {
		return _mm512_castsi512_ps(_mm512_setzero_si512());
	}

	template <>
	inline reg set0<int16_t>() {
		return _mm512_castsi512_ps(_mm512_setzero_si512());
	}

	template <>
	inline reg set0<int8_t>() {
		return _mm512_castsi512_ps(_mm512_setzero_si512());
	}

#elif defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg set0<float>() {
		return set1<float>(0.f);
	}

	template <>
	inline reg set0<double>() {
		return set1<double>(0.0);
	}

	template <>
	inline reg set0<int32_t>() {
		return set1<int32_t>(0);
	}
#endif

	// ---------------------------------------------------------------------------------------------------- set0 (mask)
	template <>
	inline msk set0<8>() {
		auto r1 = set0<int32_t>(          );
		auto r2 = set1<int32_t>(0xFFFFFFFF);

		return (msk) cmpeq<int32_t>(r1, r2);
	}

	template <>
	inline msk set0<16>() {
		auto r1 = set0<int32_t>(          );
		auto r2 = set1<int32_t>(0xFFFFFFFF);

		return (msk) cmpeq<int32_t>(r1, r2);
	}

	template <>
	inline msk set0<32>() {
		auto r1 = set0<int32_t>(          );
		auto r2 = set1<int32_t>(0xFFFFFFFF);

		return (msk) cmpeq<int32_t>(r1, r2);
	}

	template <>
	inline msk set0<64>() {
		auto r1 = set0<int32_t>(          );
		auto r2 = set1<int32_t>(0xFFFFFFFF);

		return (msk) cmpeq<int32_t>(r1, r2);
	}

	// ------------------------------------------------------------------------------------------------------------ set
#if defined(__AVX512F__)
	template <>
	inline reg set<double>(const double vals[nElReg<double>()]) {
		return _mm512_castpd_ps(_mm512_set_pd(vals[7], vals[6], vals[5], vals[4], vals[3], vals[2], vals[1], vals[0]));
	}

	template <>
	inline reg set<float>(const float vals[nElReg<float>()]) {
		return _mm512_set_ps(vals[15], vals[14], vals[13], vals[12], vals[11], vals[10], vals[9], vals[8],
		                     vals[ 7], vals[ 6], vals[ 5], vals[ 4], vals[ 3], vals[ 2], vals[1], vals[0]);
	}

	template <>
	inline reg set<int64_t>(const int64_t vals[nElReg<int64_t>()]) {
		return _mm512_castsi512_ps(_mm512_set_epi64(vals[ 7], vals[ 6], vals[ 5], vals[ 4],
		                                            vals[ 3], vals[ 2], vals[ 1], vals[ 0]));
	}

	template <>
	inline reg set<int32_t>(const int32_t vals[nElReg<int32_t>()]) {
		return _mm512_castsi512_ps(_mm512_set_epi32(vals[15], vals[14], vals[13], vals[12],
		                                            vals[11], vals[10], vals[ 9], vals[ 8],
		                                            vals[ 7], vals[ 6], vals[ 5], vals[ 4],
		                                            vals[ 3], vals[ 2], vals[ 1], vals[ 0]));
	}

#ifdef __AVX512BW__
	template <>
	inline reg set<int16_t>(const int16_t vals[nElReg<int16_t>()]) {
		return _mm512_castsi512_ps(_mm512_set_epi16(vals[31], vals[30], vals[29], vals[28],
		                                            vals[27], vals[26], vals[25], vals[24],
		                                            vals[23], vals[22], vals[21], vals[20],
		                                            vals[19], vals[18], vals[17], vals[16],
		                                            vals[15], vals[14], vals[13], vals[12],
		                                            vals[11], vals[10], vals[ 9], vals[ 8],
		                                            vals[ 7], vals[ 6], vals[ 5], vals[ 4],
		                                            vals[ 3], vals[ 2], vals[ 1], vals[ 0]));
	}

	template <>
	inline reg set<int8_t>(const int8_t vals[nElReg<int8_t>()]) {
		return _mm512_castsi512_ps(_mm512_set_epi8((int8_t)vals[63], (int8_t)vals[62], (int8_t)vals[61], (int8_t)vals[60],
		                                           (int8_t)vals[59], (int8_t)vals[58], (int8_t)vals[57], (int8_t)vals[56],
		                                           (int8_t)vals[55], (int8_t)vals[54], (int8_t)vals[53], (int8_t)vals[52],
		                                           (int8_t)vals[51], (int8_t)vals[50], (int8_t)vals[49], (int8_t)vals[48],
		                                           (int8_t)vals[47], (int8_t)vals[46], (int8_t)vals[45], (int8_t)vals[44],
		                                           (int8_t)vals[43], (int8_t)vals[42], (int8_t)vals[41], (int8_t)vals[40],
		                                           (int8_t)vals[39], (int8_t)vals[38], (int8_t)vals[37], (int8_t)vals[36],
		                                           (int8_t)vals[35], (int8_t)vals[34], (int8_t)vals[33], (int8_t)vals[32],
		                                           (int8_t)vals[31], (int8_t)vals[30], (int8_t)vals[29], (int8_t)vals[28],
		                                           (int8_t)vals[27], (int8_t)vals[26], (int8_t)vals[25], (int8_t)vals[24],
		                                           (int8_t)vals[23], (int8_t)vals[22], (int8_t)vals[21], (int8_t)vals[20],
		                                           (int8_t)vals[19], (int8_t)vals[18], (int8_t)vals[17], (int8_t)vals[16],
		                                           (int8_t)vals[15], (int8_t)vals[14], (int8_t)vals[13], (int8_t)vals[12],
		                                           (int8_t)vals[11], (int8_t)vals[10], (int8_t)vals[ 9], (int8_t)vals[ 8],
		                                           (int8_t)vals[ 7], (int8_t)vals[ 6], (int8_t)vals[ 5], (int8_t)vals[ 4],
		                                           (int8_t)vals[ 3], (int8_t)vals[ 2], (int8_t)vals[ 1], (int8_t)vals[ 0]));
	}
#endif

#elif defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg set<double>(const double vals[nElReg<double>()]) {
		double init[8] __attribute__((aligned(64))) = {vals[0], vals[1], vals[2], vals[3],
		                                               vals[4], vals[5], vals[6], vals[7]};
		return load<double>(init);
	}

	template <>
	inline reg set<float>(const float vals[nElReg<float>()]) {
		float init[16] __attribute__((aligned(64))) = {vals[ 0], vals[ 1], vals[ 2], vals[ 3],
		                                               vals[ 4], vals[ 5], vals[ 6], vals[ 7],
		                                               vals[ 8], vals[ 9], vals[10], vals[11],
		                                               vals[12], vals[13], vals[14], vals[15]};
		return load<float>(init);
	}

	template <>
	inline reg set<int64_t>(const int64_t vals[nElReg<int64_t>()]) {
		int64_t init[8] __attribute__((aligned(64))) = {vals[0], vals[1], vals[2], vals[3],
		                                                vals[4], vals[5], vals[6], vals[7]};
		return load<int64_t>(init);
	}

	template <>
	inline reg set<int32_t>(const int32_t vals[nElReg<int32_t>()]) {
		int32_t init[16] __attribute__((aligned(64))) = {vals[ 0], vals[ 1], vals[ 2], vals[ 3],
		                                                 vals[ 4], vals[ 5], vals[ 6], vals[ 7],
		                                                 vals[ 8], vals[ 9], vals[10], vals[11],
		                                                 vals[12], vals[13], vals[14], vals[15]};
		return load<int32_t>(init);
	}
#endif

	// ----------------------------------------------------------------------------------------------------- set (mask)
#ifdef __AVX512F__
	template <>
	inline msk set<8>(const bool vals[8]) {
		uint64_t v[8] = {vals[0] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0,
		                 vals[1] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0,
		                 vals[2] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0,
		                 vals[3] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0,
		                 vals[4] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0,
		                 vals[5] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0,
		                 vals[6] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0,
		                 vals[7] ? (uint64_t)0xFFFFFFFFFFFFFFFF : (uint64_t)0};
		auto r1 = set <int64_t>((int64_t*)v);
		auto r2 = set1<int64_t>((uint64_t)0xFFFFFFFFFFFFFFFF);

//		return (msk)_mm512_test_epi64_mask(_mm512_castps_si512(r1), _mm512_castps_si512(r2));
		return (msk) cmpeq<int64_t>(r1, r2);
	}
#endif

	template <>
	inline msk set<16>(const bool vals[16]) {
		uint32_t v[16] = {vals[ 0] ? 0xFFFFFFFF : 0, vals[ 1] ? 0xFFFFFFFF : 0,
		                  vals[ 2] ? 0xFFFFFFFF : 0, vals[ 3] ? 0xFFFFFFFF : 0,
		                  vals[ 4] ? 0xFFFFFFFF : 0, vals[ 5] ? 0xFFFFFFFF : 0,
		                  vals[ 6] ? 0xFFFFFFFF : 0, vals[ 7] ? 0xFFFFFFFF : 0,
		                  vals[ 8] ? 0xFFFFFFFF : 0, vals[ 9] ? 0xFFFFFFFF : 0,
		                  vals[10] ? 0xFFFFFFFF : 0, vals[11] ? 0xFFFFFFFF : 0,
		                  vals[12] ? 0xFFFFFFFF : 0, vals[13] ? 0xFFFFFFFF : 0,
		                  vals[14] ? 0xFFFFFFFF : 0, vals[15] ? 0xFFFFFFFF : 0};
		auto r1 = set <int32_t>((int32_t*)v);
		auto r2 = set1<int32_t>(0xFFFFFFFF);

//		return (msk)_mm512_test_epi32_mask(_mm512_castps_si512(r1), _mm512_castps_si512(r2));
		return (msk) cmpeq<int32_t>(r1, r2);
	}

#ifdef __AVX512BW__
	template <>
	inline msk set<32>(const bool vals[32]) {
		uint16_t v[32] = {vals[ 0] ? 0xFFFF : 0, vals[ 1] ? 0xFFFF : 0,
		                  vals[ 2] ? 0xFFFF : 0, vals[ 3] ? 0xFFFF : 0,
		                  vals[ 4] ? 0xFFFF : 0, vals[ 5] ? 0xFFFF : 0,
		                  vals[ 6] ? 0xFFFF : 0, vals[ 7] ? 0xFFFF : 0,
		                  vals[ 8] ? 0xFFFF : 0, vals[ 9] ? 0xFFFF : 0,
		                  vals[10] ? 0xFFFF : 0, vals[11] ? 0xFFFF : 0,
		                  vals[12] ? 0xFFFF : 0, vals[13] ? 0xFFFF : 0,
		                  vals[14] ? 0xFFFF : 0, vals[15] ? 0xFFFF : 0,
		                  vals[16] ? 0xFFFF : 0, vals[17] ? 0xFFFF : 0,
		                  vals[18] ? 0xFFFF : 0, vals[19] ? 0xFFFF : 0,
		                  vals[20] ? 0xFFFF : 0, vals[21] ? 0xFFFF : 0,
		                  vals[22] ? 0xFFFF : 0, vals[23] ? 0xFFFF : 0,
		                  vals[24] ? 0xFFFF : 0, vals[25] ? 0xFFFF : 0,
		                  vals[26] ? 0xFFFF : 0, vals[27] ? 0xFFFF : 0,
		                  vals[28] ? 0xFFFF : 0, vals[29] ? 0xFFFF : 0,
		                  vals[30] ? 0xFFFF : 0, vals[31] ? 0xFFFF : 0}; 
		auto r1 = set <int16_t>((int16_t*)v);
		auto r2 = set1<int16_t>(0xFFFF);

//		return (msk)_mm512_test_epi16_mask(_mm512_castps_si512(r1), _mm512_castps_si512(r2));
		return (msk) cmpeq<int16_t>(r1, r2);
	}

	template <>
	inline msk set<64>(const bool vals[64]) {
		uint8_t v[64] = {vals[ 0] ? 0xFF : 0, vals[ 1] ? 0xFF : 0, vals[ 2] ? 0xFF : 0, vals[ 3] ? 0xFF : 0,
		                 vals[ 4] ? 0xFF : 0, vals[ 5] ? 0xFF : 0, vals[ 6] ? 0xFF : 0, vals[ 7] ? 0xFF : 0,
		                 vals[ 8] ? 0xFF : 0, vals[ 9] ? 0xFF : 0, vals[10] ? 0xFF : 0, vals[11] ? 0xFF : 0,
		                 vals[12] ? 0xFF : 0, vals[13] ? 0xFF : 0, vals[14] ? 0xFF : 0, vals[15] ? 0xFF : 0,
		                 vals[16] ? 0xFF : 0, vals[17] ? 0xFF : 0, vals[18] ? 0xFF : 0, vals[19] ? 0xFF : 0,
		                 vals[20] ? 0xFF : 0, vals[21] ? 0xFF : 0, vals[22] ? 0xFF : 0, vals[23] ? 0xFF : 0,
		                 vals[24] ? 0xFF : 0, vals[25] ? 0xFF : 0, vals[26] ? 0xFF : 0, vals[27] ? 0xFF : 0,
		                 vals[28] ? 0xFF : 0, vals[29] ? 0xFF : 0, vals[30] ? 0xFF : 0, vals[31] ? 0xFF : 0,
		                 vals[32] ? 0xFF : 0, vals[33] ? 0xFF : 0, vals[34] ? 0xFF : 0, vals[35] ? 0xFF : 0,
		                 vals[36] ? 0xFF : 0, vals[37] ? 0xFF : 0, vals[38] ? 0xFF : 0, vals[39] ? 0xFF : 0,
		                 vals[40] ? 0xFF : 0, vals[41] ? 0xFF : 0, vals[42] ? 0xFF : 0, vals[43] ? 0xFF : 0,
		                 vals[44] ? 0xFF : 0, vals[45] ? 0xFF : 0, vals[46] ? 0xFF : 0, vals[47] ? 0xFF : 0,
		                 vals[48] ? 0xFF : 0, vals[49] ? 0xFF : 0, vals[50] ? 0xFF : 0, vals[51] ? 0xFF : 0,
		                 vals[52] ? 0xFF : 0, vals[53] ? 0xFF : 0, vals[54] ? 0xFF : 0, vals[55] ? 0xFF : 0,
		                 vals[56] ? 0xFF : 0, vals[57] ? 0xFF : 0, vals[58] ? 0xFF : 0, vals[59] ? 0xFF : 0,
		                 vals[60] ? 0xFF : 0, vals[61] ? 0xFF : 0, vals[62] ? 0xFF : 0, vals[63] ? 0xFF : 0};
		auto r1 = set <int8_t>((int8_t*)v);
		auto r2 = set1<int8_t>(0xFF);

//		return (msk)_mm512_test_epi8_mask(_mm512_castps_si512(r1), _mm512_castps_si512(r2));
		return (msk) cmpeq<int8_t>(r1, r2);
	}
#endif

	// ------------------------------------------------------------------------------------------------------- cvt_reg
	template <>
	inline reg cvt_reg<8>(const msk m) {
		auto one  = set1<int64_t>((uint64_t)0xFFFFFFFFFFFFFFFF);
		auto zero = set1<int64_t>(0);

		return blend<int64_t>(one, zero, m);
	}

	template <>
	inline reg cvt_reg<16>(const msk m) {
		auto one  = set1<int32_t>(0xFFFFFFFF);
		auto zero = set1<int32_t>(0);

		return blend<int32_t>(one, zero, m);
	}

#ifdef __AVX512BW__
	template <>
	inline reg cvt_reg<32>(const msk m) {
		auto one  = set1<int16_t>(0xFFFF);
		auto zero = set1<int16_t>(0);

		return blend<int16_t>(one, zero, m);
	}

	template <>
	inline reg cvt_reg<64>(const msk m) {
		auto one  = set1<int8_t>(0xFF);
		auto zero = set1<int8_t>(0);

		return blend<int8_t>(one, zero, m);
	}
#endif


	// ------------------------------------------------------------------------------------------------------------ low
#if defined(__AVX512F__)
	template <>
	inline reg_2 low<double>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 0));
	}

	template <>
	inline reg_2 low<float>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 0));
	}

	template <>
	inline reg_2 low<int64_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 0));
	}

	template <>
	inline reg_2 low<int32_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 0));
	}

	template <>
	inline reg_2 low<int16_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 0));
	}

	template <>
	inline reg_2 low<int8_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 0));
	}
#endif

	// ----------------------------------------------------------------------------------------------------------- high
#if defined(__AVX512F__)
	template <>
	inline reg_2 high<double>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 1));
	}

	template <>
	inline reg_2 high<float>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 1));
	}

	template <>
	inline reg_2 high<int64_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 1));
	}

	template <>
	inline reg_2 high<int32_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 1));
	}

	template <>
	inline reg_2 high<int16_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 1));
	}

	template <>
	inline reg_2 high<int8_t>(const reg v) {
		return _mm256_castpd_ps(_mm512_extractf64x4_pd(_mm512_castps_pd(v), 1));
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- cmask
	template <>
	inline reg cmask<float>(const uint32_t val[nElReg<float>()]) {
		int8_t val_bis[nElReg<int8_t>()] = {(int8_t)(val[ 0]*4 + 0), (int8_t)(val[ 0]*4 + 1),
		                                    (int8_t)(val[ 0]*4 + 2), (int8_t)(val[ 0]*4 + 3),
		                                    (int8_t)(val[ 1]*4 + 0), (int8_t)(val[ 1]*4 + 1),
		                                    (int8_t)(val[ 1]*4 + 2), (int8_t)(val[ 1]*4 + 3),
		                                    (int8_t)(val[ 2]*4 + 0), (int8_t)(val[ 2]*4 + 1),
		                                    (int8_t)(val[ 2]*4 + 2), (int8_t)(val[ 2]*4 + 3),
		                                    (int8_t)(val[ 3]*4 + 0), (int8_t)(val[ 3]*4 + 1),
		                                    (int8_t)(val[ 3]*4 + 2), (int8_t)(val[ 3]*4 + 3),
		                                    (int8_t)(val[ 4]*4 + 0), (int8_t)(val[ 4]*4 + 1),
		                                    (int8_t)(val[ 4]*4 + 2), (int8_t)(val[ 4]*4 + 3),
		                                    (int8_t)(val[ 5]*4 + 0), (int8_t)(val[ 5]*4 + 1),
		                                    (int8_t)(val[ 5]*4 + 2), (int8_t)(val[ 5]*4 + 3),
		                                    (int8_t)(val[ 6]*4 + 0), (int8_t)(val[ 6]*4 + 1),
		                                    (int8_t)(val[ 6]*4 + 2), (int8_t)(val[ 6]*4 + 3),
		                                    (int8_t)(val[ 7]*4 + 0), (int8_t)(val[ 7]*4 + 1),
		                                    (int8_t)(val[ 7]*4 + 2), (int8_t)(val[ 7]*4 + 3),
		                                    (int8_t)(val[ 8]*4 + 0), (int8_t)(val[ 8]*4 + 1),
		                                    (int8_t)(val[ 8]*4 + 2), (int8_t)(val[ 8]*4 + 3),
		                                    (int8_t)(val[ 9]*4 + 0), (int8_t)(val[ 9]*4 + 1),
		                                    (int8_t)(val[ 9]*4 + 2), (int8_t)(val[ 9]*4 + 3),
		                                    (int8_t)(val[10]*4 + 0), (int8_t)(val[10]*4 + 1),
		                                    (int8_t)(val[10]*4 + 2), (int8_t)(val[10]*4 + 3),
		                                    (int8_t)(val[11]*4 + 0), (int8_t)(val[11]*4 + 1),
		                                    (int8_t)(val[11]*4 + 2), (int8_t)(val[11]*4 + 3),
		                                    (int8_t)(val[12]*4 + 0), (int8_t)(val[12]*4 + 1),
		                                    (int8_t)(val[12]*4 + 2), (int8_t)(val[12]*4 + 3),
		                                    (int8_t)(val[13]*4 + 0), (int8_t)(val[13]*4 + 1),
		                                    (int8_t)(val[13]*4 + 2), (int8_t)(val[13]*4 + 3),
		                                    (int8_t)(val[14]*4 + 0), (int8_t)(val[14]*4 + 1),
		                                    (int8_t)(val[14]*4 + 2), (int8_t)(val[14]*4 + 3),
		                                    (int8_t)(val[15]*4 + 0), (int8_t)(val[15]*4 + 1),
		                                    (int8_t)(val[15]*4 + 2), (int8_t)(val[15]*4 + 3)};
		return mipp::set<int8_t>(val_bis);
	}

	template <>
	inline reg cmask<int32_t>(const uint32_t val[nElReg<int32_t>()]) {
		int8_t val_bis[nElReg<int8_t>()] = {(int8_t)(val[ 0]*4 + 0), (int8_t)(val[ 0]*4 + 1),
		                                    (int8_t)(val[ 0]*4 + 2), (int8_t)(val[ 0]*4 + 3),
		                                    (int8_t)(val[ 1]*4 + 0), (int8_t)(val[ 1]*4 + 1),
		                                    (int8_t)(val[ 1]*4 + 2), (int8_t)(val[ 1]*4 + 3),
		                                    (int8_t)(val[ 2]*4 + 0), (int8_t)(val[ 2]*4 + 1),
		                                    (int8_t)(val[ 2]*4 + 2), (int8_t)(val[ 2]*4 + 3),
		                                    (int8_t)(val[ 3]*4 + 0), (int8_t)(val[ 3]*4 + 1),
		                                    (int8_t)(val[ 3]*4 + 2), (int8_t)(val[ 3]*4 + 3),
		                                    (int8_t)(val[ 4]*4 + 0), (int8_t)(val[ 4]*4 + 1),
		                                    (int8_t)(val[ 4]*4 + 2), (int8_t)(val[ 4]*4 + 3),
		                                    (int8_t)(val[ 5]*4 + 0), (int8_t)(val[ 5]*4 + 1),
		                                    (int8_t)(val[ 5]*4 + 2), (int8_t)(val[ 5]*4 + 3),
		                                    (int8_t)(val[ 6]*4 + 0), (int8_t)(val[ 6]*4 + 1),
		                                    (int8_t)(val[ 6]*4 + 2), (int8_t)(val[ 6]*4 + 3),
		                                    (int8_t)(val[ 7]*4 + 0), (int8_t)(val[ 7]*4 + 1),
		                                    (int8_t)(val[ 7]*4 + 2), (int8_t)(val[ 7]*4 + 3),
		                                    (int8_t)(val[ 8]*4 + 0), (int8_t)(val[ 8]*4 + 1),
		                                    (int8_t)(val[ 8]*4 + 2), (int8_t)(val[ 8]*4 + 3),
		                                    (int8_t)(val[ 9]*4 + 0), (int8_t)(val[ 9]*4 + 1),
		                                    (int8_t)(val[ 9]*4 + 2), (int8_t)(val[ 9]*4 + 3),
		                                    (int8_t)(val[10]*4 + 0), (int8_t)(val[10]*4 + 1),
		                                    (int8_t)(val[10]*4 + 2), (int8_t)(val[10]*4 + 3),
		                                    (int8_t)(val[11]*4 + 0), (int8_t)(val[11]*4 + 1),
		                                    (int8_t)(val[11]*4 + 2), (int8_t)(val[11]*4 + 3),
		                                    (int8_t)(val[12]*4 + 0), (int8_t)(val[12]*4 + 1),
		                                    (int8_t)(val[12]*4 + 2), (int8_t)(val[12]*4 + 3),
		                                    (int8_t)(val[13]*4 + 0), (int8_t)(val[13]*4 + 1),
		                                    (int8_t)(val[13]*4 + 2), (int8_t)(val[13]*4 + 3),
		                                    (int8_t)(val[14]*4 + 0), (int8_t)(val[14]*4 + 1),
		                                    (int8_t)(val[14]*4 + 2), (int8_t)(val[14]*4 + 3),
		                                    (int8_t)(val[15]*4 + 0), (int8_t)(val[15]*4 + 1),
		                                    (int8_t)(val[15]*4 + 2), (int8_t)(val[15]*4 + 3)};
		return mipp::set<int8_t>(val_bis);
	}

	template <>
	inline reg cmask<int16_t>(const uint32_t val[nElReg<int16_t>()]) {
		int8_t val_bis[nElReg<int8_t>()] = {(int8_t)(val[ 0]*2 + 0), (int8_t)(val[ 0]*2 + 1),
		                                    (int8_t)(val[ 1]*2 + 0), (int8_t)(val[ 1]*2 + 1),
		                                    (int8_t)(val[ 2]*2 + 0), (int8_t)(val[ 2]*2 + 1),
		                                    (int8_t)(val[ 3]*2 + 0), (int8_t)(val[ 3]*2 + 1),
		                                    (int8_t)(val[ 4]*2 + 0), (int8_t)(val[ 4]*2 + 1),
		                                    (int8_t)(val[ 5]*2 + 0), (int8_t)(val[ 5]*2 + 1),
		                                    (int8_t)(val[ 6]*2 + 0), (int8_t)(val[ 6]*2 + 1),
		                                    (int8_t)(val[ 7]*2 + 0), (int8_t)(val[ 7]*2 + 1),
		                                    (int8_t)(val[ 8]*2 + 0), (int8_t)(val[ 8]*2 + 1),
		                                    (int8_t)(val[ 9]*2 + 0), (int8_t)(val[ 9]*2 + 1),
		                                    (int8_t)(val[10]*2 + 0), (int8_t)(val[10]*2 + 1),
		                                    (int8_t)(val[11]*2 + 0), (int8_t)(val[11]*2 + 1),
		                                    (int8_t)(val[12]*2 + 0), (int8_t)(val[12]*2 + 1),
		                                    (int8_t)(val[13]*2 + 0), (int8_t)(val[13]*2 + 1),
		                                    (int8_t)(val[14]*2 + 0), (int8_t)(val[14]*2 + 1),
		                                    (int8_t)(val[15]*2 + 0), (int8_t)(val[15]*2 + 1),
		                                    (int8_t)(val[16]*2 + 0), (int8_t)(val[16]*2 + 1),
		                                    (int8_t)(val[17]*2 + 0), (int8_t)(val[17]*2 + 1),
		                                    (int8_t)(val[18]*2 + 0), (int8_t)(val[18]*2 + 1),
		                                    (int8_t)(val[19]*2 + 0), (int8_t)(val[19]*2 + 1),
		                                    (int8_t)(val[20]*2 + 0), (int8_t)(val[20]*2 + 1),
		                                    (int8_t)(val[21]*2 + 0), (int8_t)(val[21]*2 + 1),
		                                    (int8_t)(val[22]*2 + 0), (int8_t)(val[22]*2 + 1),
		                                    (int8_t)(val[23]*2 + 0), (int8_t)(val[23]*2 + 1),
		                                    (int8_t)(val[24]*2 + 0), (int8_t)(val[24]*2 + 1),
		                                    (int8_t)(val[25]*2 + 0), (int8_t)(val[25]*2 + 1),
		                                    (int8_t)(val[26]*2 + 0), (int8_t)(val[26]*2 + 1),
		                                    (int8_t)(val[27]*2 + 0), (int8_t)(val[27]*2 + 1),
		                                    (int8_t)(val[28]*2 + 0), (int8_t)(val[28]*2 + 1),
		                                    (int8_t)(val[29]*2 + 0), (int8_t)(val[29]*2 + 1),
		                                    (int8_t)(val[30]*2 + 0), (int8_t)(val[30]*2 + 1),
		                                    (int8_t)(val[31]*2 + 0), (int8_t)(val[31]*2 + 1)};
		return mipp::set<int8_t>(val_bis);
	}

	template <>
	inline reg cmask<int8_t>(const uint32_t val[nElReg<int8_t>()]) {
		int8_t val_bis[nElReg<int8_t>()] = {(int8_t)val[ 0], (int8_t)val[ 1], (int8_t)val[ 2], (int8_t)val[ 3],
		                                    (int8_t)val[ 4], (int8_t)val[ 5], (int8_t)val[ 6], (int8_t)val[ 7],
		                                    (int8_t)val[ 8], (int8_t)val[ 9], (int8_t)val[10], (int8_t)val[11],
		                                    (int8_t)val[12], (int8_t)val[13], (int8_t)val[14], (int8_t)val[15],
		                                    (int8_t)val[16], (int8_t)val[17], (int8_t)val[18], (int8_t)val[19],
		                                    (int8_t)val[20], (int8_t)val[21], (int8_t)val[22], (int8_t)val[23],
		                                    (int8_t)val[24], (int8_t)val[25], (int8_t)val[26], (int8_t)val[27],
		                                    (int8_t)val[28], (int8_t)val[29], (int8_t)val[30], (int8_t)val[31],
		                                    (int8_t)val[32], (int8_t)val[33], (int8_t)val[34], (int8_t)val[35],
		                                    (int8_t)val[36], (int8_t)val[37], (int8_t)val[38], (int8_t)val[39],
		                                    (int8_t)val[40], (int8_t)val[41], (int8_t)val[42], (int8_t)val[43],
		                                    (int8_t)val[44], (int8_t)val[45], (int8_t)val[46], (int8_t)val[47],
		                                    (int8_t)val[48], (int8_t)val[49], (int8_t)val[50], (int8_t)val[51],
		                                    (int8_t)val[52], (int8_t)val[53], (int8_t)val[54], (int8_t)val[55],
		                                    (int8_t)val[56], (int8_t)val[57], (int8_t)val[58], (int8_t)val[59],
		                                    (int8_t)val[60], (int8_t)val[61], (int8_t)val[62], (int8_t)val[63]};
		return mipp::set<int8_t>(val_bis);
	}

	// ---------------------------------------------------------------------------------------------------------- shuff
#if defined(__AVX512BW__)
	template <>
	inline reg shuff<float>(const reg v, const reg cm) {
		return _mm512_castsi512_ps(_mm512_shuffle_epi8(_mm512_castps_si512(v), _mm512_castps_si512(cm)));
	}

	template <>
	inline reg shuff<int32_t>(const reg v, const reg cm) {
		return _mm512_castsi512_ps(_mm512_shuffle_epi8(_mm512_castps_si512(v), _mm512_castps_si512(cm)));
	}

	template <>
	inline reg shuff<int16_t>(const reg v, const reg cm) {
		return _mm512_castsi512_ps(_mm512_shuffle_epi8(_mm512_castps_si512(v), _mm512_castps_si512(cm)));
	}

	template <>
	inline reg shuff<int8_t>(const reg v, const reg cm) {
		return _mm512_castsi512_ps(_mm512_shuffle_epi8(_mm512_castps_si512(v), _mm512_castps_si512(cm)));
	}
#endif

	// ----------------------------------------------------------------------------------------------------------- andb
	template <>
	inline reg andb<double>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_and_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andb<float>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_and_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andb<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_and_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andb<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_and_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andb<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_and_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	// ---------------------------------------------------------------------------------------------------- andb (mask)
	template <>
	inline msk andb<8>(const msk v1, const msk v2) {
		return _mm512_kand(v1, v2);
	}

	template <>
	inline msk andb<16>(const msk v1, const msk v2) {
		return _mm512_kand(v1, v2);
	}

#if defined(__AVX512BW__)
	template <>
	inline msk andb<32>(const msk v1, const msk v2) {
		return _mm512_kand(v1, v2);
	}

	template <>
	inline msk andb<64>(const msk v1, const msk v2) {
		return _mm512_kand(v1, v2);
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- andnb
	template <>
	inline reg andnb<float>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_andnot_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andnb<double>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_andnot_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andnb<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_andnot_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andnb<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_andnot_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg andnb<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_andnot_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	// --------------------------------------------------------------------------------------------------- andnb (mask)
	template <>
	inline msk andnb<8>(const msk v1, const msk v2) {
		return _mm512_kandn(v1, v2);
	}

	template <>
	inline msk andnb<16>(const msk v1, const msk v2) {
		return _mm512_kandn(v1, v2);
	}

#if defined(__AVX512BW__)
	template <>
	inline msk andnb<32>(const msk v1, const msk v2) {
		return _mm512_kandn(v1, v2);
	}

	template <>
	inline msk andnb<64>(const msk v1, const msk v2) {
		return _mm512_kandn(v1, v2);
	}
#endif

	// ----------------------------------------------------------------------------------------------------------- notb
	template <>
	inline reg notb<double>(const reg v) {
		return andnb<double>(v, set1<int64_t>(0xFFFFFFFFFFFFFFFF));
	}

	template <>
	inline reg notb<float>(const reg v) {
		return andnb<float>(v, set1<int32_t>(0xFFFFFFFF));
	}

	template <>
	inline reg notb<int32_t>(const reg v) {
		return andnb<int32_t>(v, set1<int32_t>(0xFFFFFFFF));
	}

	template <>
	inline reg notb<int16_t>(const reg v) {
#ifdef _MSC_VER
#pragma warning( disable : 4309 )
#endif
		return andnb<int16_t>(v, set1<int16_t>(0xFFFF));
#ifdef _MSC_VER
#pragma warning( default : 4309 )
#endif
	}

	template <>
	inline reg notb<int8_t>(const reg v) {
#ifdef _MSC_VER
#pragma warning( disable : 4309 )
#endif
		return andnb<int8_t>(v, set1<int8_t>(0xFF));
#ifdef _MSC_VER
#pragma warning( default : 4309 )
#endif
	}

	// ---------------------------------------------------------------------------------------------------- notb (mask)
	template <>
	inline msk notb<8>(const msk v) {
		return _mm512_knot(v);
	}

	template <>
	inline msk notb<16>(const msk v) {
		return _mm512_knot(v);
	}

#if defined(__AVX512BW__)
	template <>
	inline msk notb<32>(const msk v) {
		return _mm512_knot(v);
	}

	template <>
	inline msk notb<64>(const msk v) {
		return _mm512_knot(v);
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ orb
	template <>
	inline reg orb<float>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_or_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg orb<double>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_or_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg orb<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_or_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg orb<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_or_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg orb<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_or_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	// ----------------------------------------------------------------------------------------------------- orb (mask)
	template <>
	inline msk orb<8>(const msk v1, const msk v2) {
		return _mm512_kor(v1, v2);
	}

	template <>
	inline msk orb<16>(const msk v1, const msk v2) {
		return _mm512_kor(v1, v2);
	}

#if defined(__AVX512BW__)
	template <>
	inline msk orb<32>(const msk v1, const msk v2) {
		return _mm512_kor(v1, v2);
	}

	template <>
	inline msk orb<64>(const msk v1, const msk v2) {
		return _mm512_kor(v1, v2);
	}
#endif

	// ----------------------------------------------------------------------------------------------------------- xorb
	template <>
	inline reg xorb<float>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_xor_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg xorb<double>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_xor_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg xorb<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_xor_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg xorb<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_xor_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg xorb<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_xor_si512(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	// ---------------------------------------------------------------------------------------------------- xorb (mask)
	template <>
	inline msk xorb<8>(const msk v1, const msk v2) {
		return _mm512_kxor(v1, v2);
	}

	template <>
	inline msk xorb<16>(const msk v1, const msk v2) {
		return _mm512_kxor(v1, v2);
	}

#if defined(__AVX512BW__)
	template <>
	inline msk xorb<32>(const msk v1, const msk v2) {
		return _mm512_kxor(v1, v2);
	}

	template <>
	inline msk xorb<64>(const msk v1, const msk v2) {
		return _mm512_kxor(v1, v2);
	}
#endif

	// --------------------------------------------------------------------------------------------------------- lshift
#if defined(__AVX512F__)
	template <>
	inline reg lshift<double>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_slli_epi64(_mm512_castps_si512(v1), n));
	}
#endif

	template <>
	inline reg lshift<float>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_slli_epi32(_mm512_castps_si512(v1), n));
	}

#if defined(__AVX512F__)
	template <>
	inline reg lshift<int64_t>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_slli_epi64(_mm512_castps_si512(v1), n));
	}
#endif

	template <>
	inline reg lshift<int32_t>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_slli_epi32(_mm512_castps_si512(v1), n));
	}

#if defined(__AVX512BW__)
	template <>
	inline reg lshift<int16_t>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_slli_epi16(_mm512_castps_si512(v1), n));
	}

	template <>
	inline reg lshift<int8_t>(const reg v1, const uint32_t n) {
		auto msk = set1<int8_t>((1 << n) -1);
		reg lsh = lshift<int16_t>(v1, n);
		lsh = andnb<int16_t>(msk, lsh);
		return lsh;
	}
#endif

	// -------------------------------------------------------------------------------------------------- lshift (mask)
	// TODO: write the corresponding assembly code (because the intrinsic does not exist). => KSHIFTL
	/*
	template <>
	inline msk lshift<8>(const msk v1, const uint32_t n) {
		return ???;
	}

	template <>
	inline msk lshift<16>(const msk v1, const uint32_t n) {
		return ???;
	}

#if defined(__AVX512BW__)
	template <>
	inline msk lshift<32>(const msk v1, const uint32_t n) {
		return ???;
	}

	template <>
	inline msk lshift<64>(const msk v1, const uint32_t n) {
		return ???;
	}
#endif
	*/

	// --------------------------------------------------------------------------------------------------------- rshift
#if defined(__AVX512F__)
	template <>
	inline reg rshift<double>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_srli_epi64(_mm512_castps_si512(v1), n));
	}
#endif

	template <>
	inline reg rshift<float>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_srli_epi32(_mm512_castps_si512(v1), n));
	}

#if defined(__AVX512F__)
	template <>
	inline reg rshift<int64_t>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_srli_epi64(_mm512_castps_si512(v1), n));
	}
#endif

	template <>
	inline reg rshift<int32_t>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_srli_epi32(_mm512_castps_si512(v1), n));
	}

#if defined(__AVX512BW__)
	template <>
	inline reg rshift<int16_t>(const reg v1, const uint32_t n) {
		return _mm512_castsi512_ps(_mm512_srli_epi16(_mm512_castps_si512(v1), n));
	}

	template <>
	inline reg rshift<int8_t>(const reg v1, const uint32_t n) {
		auto msk = set1<int8_t>((1 << (8 -n)) -1);
		reg rsh = rshift<int16_t>(v1, n);
		rsh = andb<int16_t>(msk, rsh);
		return rsh;
	}
#endif

	// -------------------------------------------------------------------------------------------------- rshift (mask)
	// TODO: write the corresponding assembly code (because the intrinsic does not exist). => KSHIFTR
	/*
	template <>
	inline msk rshift<8>(const msk v1, const uint32_t n) {
		return ???;
	}

	template <>
	inline msk rshift<16>(const msk v1, const uint32_t n) {
		return ???;
	}

#if defined(__AVX512BW__)
	template <>
	inline msk rshift<32>(const msk v1, const uint32_t n) {
		return ???;
	}

	template <>
	inline msk rshift<64>(const msk v1, const uint32_t n) {
		return ???;
	}
#endif
	*/

	// --------------------------------------------------------------------------------------------------------- cmpneq
	template <>
	inline msk cmpneq<double>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_pd_mask(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _CMP_NEQ_OQ);
	}

	template <>
	inline msk cmpneq<float>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_ps_mask(v1, v2, _CMP_NEQ_OQ);
	}

#if defined(__AVX512F__)
	template <>
	inline msk cmpneq<int64_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpneq_epi64_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	template <>
	inline msk cmpneq<int32_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpneq_epi32_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

#if defined(__AVX512BW__)
	template <>
	inline msk cmpneq<int16_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpneq_epi16_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

	template <>
	inline msk cmpneq<int8_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpneq_epi8_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- cmplt
	template <>
	inline msk cmplt<double>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_pd_mask(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _CMP_LT_OS);
	}

	template <>
	inline msk cmplt<float>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_ps_mask(v1, v2, _CMP_LT_OS);
	}

#if defined(__AVX512F__)
	template <>
	inline msk cmplt<int64_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmplt_epi64_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	template <>
	inline msk cmplt<int32_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmplt_epi32_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

#if defined(__AVX512BW__)
	template <>
	inline msk cmplt<int16_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmplt_epi16_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

	template <>
	inline msk cmplt<int8_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmplt_epi8_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- cmple
	template <>
	inline msk cmple<double>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_pd_mask(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _CMP_LE_OS);
	}

	template <>
	inline msk cmple<float>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_ps_mask(v1, v2, _CMP_LE_OS);
	}

#if defined(__AVX512F__)
	template <>
	inline msk cmple<int64_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmple_epi64_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	template <>
	inline msk cmple<int32_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmple_epi32_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

#if defined(__AVX512BW__)
	template <>
	inline msk cmple<int16_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmple_epi16_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

	template <>
	inline msk cmple<int8_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmple_epi8_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif
	
	// ---------------------------------------------------------------------------------------------------------- cmpgt
	template <>
	inline msk cmpgt<double>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_pd_mask(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _CMP_GT_OS);
	}

	template <>
	inline msk cmpgt<float>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_ps_mask(v1, v2, _CMP_GT_OS);
	}

#if defined(__AVX512F__)
	template <>
	inline msk cmpgt<int64_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpgt_epi64_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	template <>
	inline msk cmpgt<int32_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpgt_epi32_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

#if defined(__AVX512BW__)
	template <>
	inline msk cmpgt<int16_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpgt_epi16_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

	template <>
	inline msk cmpgt<int8_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpgt_epi8_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- cmpge
	template <>
	inline msk cmpge<double>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_pd_mask(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _CMP_GE_OS);
	}

	template <>
	inline msk cmpge<float>(const reg v1, const reg v2) {
		return (msk) _mm512_cmp_ps_mask(v1, v2, _CMP_GE_OS);
	}

#if defined(__AVX512F__)
	template <>
	inline msk cmpge<int64_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpge_epi64_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	template <>
	inline msk cmpge<int32_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpge_epi32_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

#if defined(__AVX512BW__)
	template <>
	inline msk cmpge<int16_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpge_epi16_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}

	template <>
	inline msk cmpge<int8_t>(const reg v1, const reg v2) {
		return (msk) _mm512_cmpge_epi8_mask(_mm512_castps_si512(v1), _mm512_castps_si512(v2));
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ add
	// ------------------ double
	template <>
	inline reg add<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_add_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg mask<double,add<double>>(const msk m, const reg src, const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_mask_add_pd(_mm512_castps_pd(src), (__mmask8)m, _mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline Reg<double> mask<double,add<double>>(const Msk<8> m, const Reg<double> src, const Reg<double> v1, const Reg<double> v2) {
		return mask<double,add<double>>(m.m, src.r, v1.r, v2.r);
	}

#if defined(__AVX512F__)
	template <>
	inline reg maskz<double,add<double>>(const msk m, const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_maskz_add_pd((__mmask8)m, _mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline Reg<double> maskz<double,add<double>>(const Msk<8> m, const Reg<double> v1, const Reg<double> v2) {
		return maskz<double,add<double>>(m.m, v1.r, v2.r);
	}
#endif

	// ------------------ float
	template <>
	inline reg add<float>(const reg v1, const reg v2) {
		return _mm512_add_ps(v1, v2);
	}

	template <>
	inline reg mask<float,add<float>>(const msk m, const reg src, const reg v1, const reg v2) {
		return _mm512_mask_add_ps(src, (__mmask16)m, v1, v2);
	}

	template <>
	inline Reg<float> mask<float,add<float>>(const Msk<16> m, const Reg<float> src, const Reg<float> v1, const Reg<float> v2) {
		return mask<float,add<float>>(m.m, src.r, v1.r, v2.r);
	}

#if defined(__AVX512F__)
	template <>
	inline reg maskz<float,add<float>>(const msk m, const reg v1, const reg v2) {
		return _mm512_maskz_add_ps((__mmask16)m, v1, v2);
	}

	template <>
	inline Reg<float> maskz<float,add<float>>(const Msk<16> m, const Reg<float> v1, const Reg<float> v2) {
		return maskz<float,add<float>>(m.m, v1.r, v2.r);
	}
#endif

	// ------------------ int64
#if defined(__AVX512F__)
	template <>
	inline reg add<int64_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_add_epi64(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg mask<int64_t,add<int64_t>>(const msk m, const reg src, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_mask_add_epi64(_mm512_castps_si512(src), (__mmask8)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int64_t> mask<int64_t,add<int64_t>>(const Msk<8> m, const Reg<int64_t> src, const Reg<int64_t> v1, const Reg<int64_t> v2) {
		return mask<int64_t,add<int64_t>>(m.m, src.r, v1.r, v2.r);
	}

	template <>
	inline reg maskz<int64_t,add<int64_t>>(const msk m, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_maskz_add_epi64((__mmask8)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int64_t> maskz<int64_t,add<int64_t>>(const Msk<8> m, const Reg<int64_t> v1, const Reg<int64_t> v2) {
		return maskz<int64_t,add<int64_t>>(m.m, v1.r, v2.r);
	}
#endif

	// ------------------ int32
	template <>
	inline reg add<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_add_epi32(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg mask<int32_t,add<int32_t>>(const msk m, const reg src, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_mask_add_epi32(_mm512_castps_si512(src), (__mmask16)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int32_t> mask<int32_t,add<int32_t>>(const Msk<16> m, const Reg<int32_t> src, const Reg<int32_t> v1, const Reg<int32_t> v2) {
		return mask<int32_t,add<int32_t>>(m.m, src.r, v1.r, v2.r);
	}

#if defined(__AVX512F__)
	template <>
	inline reg maskz<int32_t,add<int32_t>>(const msk m, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_maskz_add_epi32((__mmask16)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int32_t> maskz<int32_t,add<int32_t>>(const Msk<16> m, const Reg<int32_t> v1, const Reg<int32_t> v2) {
		return maskz<int32_t,add<int32_t>>(m.m, v1.r, v2.r);
	}
#endif

#if defined(__AVX512BW__)
	// ------------------ int16
	template <>
	inline reg add<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_add_epi16(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg mask<int16_t,add<int16_t>>(const msk m, const reg src, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_mask_add_epi16(_mm512_castps_si512(src), (__mmask32)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int16_t> mask<int16_t,add<int16_t>>(const Msk<32> m, const Reg<int16_t> src, const Reg<int16_t> v1, const Reg<int16_t> v2) {
		return mask<int16_t,add<int16_t>>(m.m, src.r, v1.r, v2.r);
	}

	template <>
	inline reg maskz<int16_t,add<int16_t>>(const msk m, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_maskz_add_epi16((__mmask32)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int16_t> maskz<int16_t,add<int16_t>>(const Msk<32> m, const Reg<int16_t> v1, const Reg<int16_t> v2) {
		return maskz<int16_t,add<int16_t>>(m.m, v1.r, v2.r);
	}

	// ------------------ int8
	template <>
	inline reg add<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_add_epi8(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg mask<int8_t,add<int8_t>>(const msk m, const reg src, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_mask_add_epi8(_mm512_castps_si512(src), (__mmask64)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int8_t> mask<int8_t,add<int8_t>>(const Msk<64> m, const Reg<int8_t> src, const Reg<int8_t> v1, const Reg<int8_t> v2) {
		return mask<int8_t,add<int8_t>>(m.m, src.r, v1.r, v2.r);
	}

	template <>
	inline reg maskz<int8_t,add<int8_t>>(const msk m, const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_maskz_add_epi8((__mmask64)m, _mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline Reg<int8_t> maskz<int8_t,add<int8_t>>(const Msk<64> m, const Reg<int8_t> v1, const Reg<int8_t> v2) {
		return maskz<int8_t,add<int8_t>>(m.m, v1.r, v2.r);
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ sub
	template <>
	inline reg sub<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_sub_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg sub<float>(const reg v1, const reg v2) {
		return _mm512_sub_ps(v1, v2);
	}

#if defined(__AVX512F__)
	template <>
	inline reg sub<int64_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_sub_epi64(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}
#endif

	template <>
	inline reg sub<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_sub_epi32(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

#if defined(__AVX512BW__)
	template <>
	inline reg sub<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_sub_epi16(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg sub<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_sub_epi8(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ mul
	template <>
	inline reg mul<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_mul_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg mul<float>(const reg v1, const reg v2) {
		return _mm512_mul_ps(v1, v2);
	}

	template <>
	inline reg mul<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_mullo_epi32(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	// ------------------------------------------------------------------------------------------------------------ div
#if defined(__AVX512F__)
	template <>
	inline reg div<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_div_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg div<float>(const reg v1, const reg v2) {
		return _mm512_div_ps(v1, v2);
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ min
#if defined(__AVX512F__)
	template <>
	inline reg min<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_min_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg min<float>(const reg v1, const reg v2) {
		return _mm512_min_ps(v1, v2);
	}

	template <>
	inline reg min<int64_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_min_epi64(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg min<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_min_epi32(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

#if defined(__AVX512BW__)
	template <>
	inline reg min<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_min_epi16(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg min<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_min_epi8(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}
#endif

#elif defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg min<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_gmin_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg min<float>(const reg v1, const reg v2) {
		return _mm512_gmin_ps(v1, v2);
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ max
#if defined(__AVX512F__)
	template <>
	inline reg max<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_max_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg max<float>(const reg v1, const reg v2) {
		return _mm512_max_ps(v1, v2);
	}

	template <>
	inline reg max<int64_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_max_epi64(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg max<int32_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_max_epi32(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

#if defined(__AVX512BW__)
	template <>
	inline reg max<int16_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_max_epi16(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}

	template <>
	inline reg max<int8_t>(const reg v1, const reg v2) {
		return _mm512_castsi512_ps(_mm512_max_epi8(_mm512_castps_si512(v1), _mm512_castps_si512(v2)));
	}
#endif

#elif defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg max<double>(const reg v1, const reg v2) {
		return _mm512_castpd_ps(_mm512_gmax_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2)));
	}

	template <>
	inline reg min<float>(const reg v1, const reg v2) {
		return _mm512_gmax_ps(v1, v2);
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ msb
	template <>
	inline reg msb<double>(const reg v1) {
		// msb_mask = 1000000000000000000000000000000000000000000000000000000000000000 // 64 bits
		const reg msb_mask = set1<int64_t>(0x8000000000000000);

		// indices = 63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32...
		// mask    =  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0...
		// v1      =  ù  €  è  é  à  &  z  y  x  w  v  u  t  s  r  q  p  o  n  m  l  k  j  i  h  g  f  e  d  c  b  a...
		// res     =  ù  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0...
		return andb<double>(v1, msb_mask);
	}

	template <>
	inline reg msb<double>(const reg v1, const reg v2) {
		reg msb_v1_v2 = xorb<double>(v1, v2);
		    msb_v1_v2 = msb<double>(msb_v1_v2);
		return msb_v1_v2;
	}

	template <>
	inline reg msb<float>(const reg v1) {
		// msb_mask = 10000000000000000000000000000000 // 32 bits
		const reg msb_mask = set1<int32_t>(0x80000000);

		// indices = 31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
		// mask    =  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
		// v1      =  ù  €  è  é  à  &  z  y  x  w  v  u  t  s  r  q  p  o  n  m  l  k  j  i  h  g  f  e  d  c  b  a
		// res     =  ù  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
		return andb<float>(v1, msb_mask);
	}

	template <>
	inline reg msb<float>(const reg v1, const reg v2) {
		reg msb_v1_v2 = xorb<float>(v1, v2);
		    msb_v1_v2 = msb<float>(msb_v1_v2);
		return msb_v1_v2;
	}

	template <>
	inline reg msb<int16_t>(const reg v1) {
#ifdef _MSC_VER
#pragma warning( disable : 4309 )
#endif
		const reg msb_mask = set1<int16_t>(0x8000);
		return andb<int16_t>(v1, msb_mask);
#ifdef _MSC_VER
#pragma warning( default : 4309 )
#endif
	}

	template <>
	inline reg msb<int8_t>(const reg v1) {
#ifdef _MSC_VER
#pragma warning( disable : 4309 )
#endif
		// msb_mask = 10000000 // 8 bits
		const reg msb_mask = set1<int8_t>(0x80);
#ifdef _MSC_VER
#pragma warning( default : 4309 )
#endif
		// indices = 7  6  5  4  3  2  1  0
		// mask    = 1  0  0  0  0  0  0  0
		// v1      = h  g  f  e  d  c  b  a
		// res     = h  0  0  0  0  0  0  0
		return andb<int8_t>(v1, msb_mask);
	}

	template <>
	inline reg msb<int16_t>(const reg v1, const reg v2) {
		reg msb_v1_v2 = xorb<int16_t>(v1, v2);
		    msb_v1_v2 = msb<int16_t>(msb_v1_v2);
		return msb_v1_v2;
	}

	template <>
	inline reg msb<int8_t>(const reg v1, const reg v2) {
		reg msb_v1_v2 = xorb<int8_t>(v1, v2);
		    msb_v1_v2 = msb<int8_t>(msb_v1_v2);
		return msb_v1_v2;
	}

	// ----------------------------------------------------------------------------------------------------------- sign
	template <>
	inline msk sign<double>(const reg v1) {
		return cmplt<double>(v1, set0<double>());
	}

	template <>
	inline msk sign<float>(const reg v1) {
		return cmplt<float>(v1, set0<float>());
	}

	template <>
	inline msk sign<int32_t>(const reg v1) {
		return cmpgt<int32_t>(set0<int32_t>(), v1);
	}

	template <>
	inline msk sign<int16_t>(const reg v1) {
		return cmpgt<int16_t>(set0<int16_t>(), v1);
	}

	template <>
	inline msk sign<int8_t>(const reg v1) {
		return cmpgt<int8_t>(set0<int8_t>(), v1);
	}

	// ------------------------------------------------------------------------------------------------------------ neg
	template <>
	inline reg neg<double>(const reg v1, const reg v2) {
		return xorb<double>(v1, msb<double>(v2));
	}

	template <>
	inline reg neg<double>(const reg v1, const msk v2) {
		return neg<double>(v1, cvt_reg<8>(v2));
	}

	template <>
	inline reg neg<float>(const reg v1, const reg v2) {
		return xorb<float>(v1, msb<float>(v2));
	}

	template <>
	inline reg neg<float>(const reg v1, const msk v2) {
		return neg<float>(v1, cvt_reg<16>(v2));
	}

	// ------------------------------------------------------------------------------------------------------------ abs
	/*
	template <>
	inline reg abs<double>(const reg v1) {
		return _mm512_castpd_ps(_mm512_abs_pd(_mm512_castps_pd(v1)));
	}

	template <>
	inline reg abs<float>(const reg v1) {
		return _mm512_abs_ps(v1);
	}

#if defined(__AVX512F__)
	template <>
	inline reg abs<int64_t>(const reg v1) {
		return _mm512_castsi512_ps(_mm512_abs_epi64(_mm512_castps_si512(v1)));
	}

	template <>
	inline reg abs<int32_t>(const reg v1) {
		return _mm512_castsi512_ps(_mm512_abs_epi32(_mm512_castps_si512(v1)));
	}
#endif

#if defined(__AVX512BW__)
	template <>
	inline reg abs<int16_t>(const reg v1) {
		return _mm512_castsi512_ps(_mm512_abs_epi16(_mm512_castps_si512(v1)));
	}

	template <>
	inline reg abs<int8_t>(const reg v1) {
		return _mm512_castsi512_ps(_mm512_abs_epi8(_mm512_castps_si512(v1)));
	}
#endif
	*/

	// ----------------------------------------------------------------------------------------------------------- sqrt
#if defined(__AVX512F__)
	template <>
	inline reg sqrt<double>(const reg v1) {
		return _mm512_castpd_ps(_mm512_sqrt_pd(_mm512_castps_pd(v1)));
	}

	template <>
	inline reg sqrt<float>(const reg v1) {
		return _mm512_sqrt_ps(v1);
	}
#endif

	// ---------------------------------------------------------------------------------------------------------- rsqrt
#if defined(__AVX512ER__)
	template <>
	inline reg rsqrt<double>(const reg v1) {
		return _mm512_castpd_ps(_mm512_rsqrt28_pd(_mm512_castps_pd(v1)));
	}

	template <>
	inline reg rsqrt<float>(const reg v1) {
		return _mm512_rsqrt28_ps(v1);
	}

#elif defined(__AVX512F__)
	template <>
	inline reg rsqrt<double>(const reg v1) {
		return _mm512_castpd_ps(_mm512_rsqrt14_pd(_mm512_castps_pd(v1)));
	}

	template <>
	inline reg rsqrt<float>(const reg v1) {
		return _mm512_rsqrt14_ps(v1);
	}

#elif defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg rsqrt<float>(const reg v1) {
		return _mm512_rsqrt23_ps(v1);
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ log
#if defined(__AVX512F__)
#if defined(__INTEL_COMPILER) || defined(__ICL) || defined(__ICC)
	template <>
	inline reg log<double>(const reg v) {
		return _mm512_castpd_ps(_mm512_log_pd(_mm512_castps_pd(v)));
	}

	template <>
	inline reg log<float>(const reg v) {
		return _mm512_log_ps(v);
	}
#endif
#endif

	// ------------------------------------------------------------------------------------------------------------ exp
#if defined(__AVX512F__)
#if defined(__INTEL_COMPILER) || defined(__ICL) || defined(__ICC)
	template <>
	inline reg exp<double>(const reg v) {
		return _mm512_castpd_ps(_mm512_exp_pd(_mm512_castps_pd(v)));
	}

	template <>
	inline reg exp<float>(const reg v) {
		return _mm512_exp_ps(v);
	}
#endif
#endif

	// ------------------------------------------------------------------------------------------------------------ sin
#if defined(__AVX512F__)
#if defined(__INTEL_COMPILER) || defined(__ICL) || defined(__ICC)
	template <>
	inline reg sin<double>(const reg v) {
		return _mm512_castpd_ps(_mm512_sin_pd(_mm512_castps_pd(v)));
	}

	template <>
	inline reg sin<float>(const reg v) {
		return _mm512_sin_ps(v);
	}
#endif
#endif

	// ------------------------------------------------------------------------------------------------------------ cos
#if defined(__AVX512F__)
#if defined(__INTEL_COMPILER) || defined(__ICL) || defined(__ICC)
	template <>
	inline reg cos<double>(const reg v) {
		return _mm512_castpd_ps(_mm512_cos_pd(_mm512_castps_pd(v)));
	}

	template <>
	inline reg cos<float>(const reg v) {
		return _mm512_cos_ps(v);
	}
#endif
#endif

	// --------------------------------------------------------------------------------------------------------- sincos
#if defined(__AVX512F__)
#if defined(__INTEL_COMPILER) || defined(__ICL) || defined(__ICC)
	template <>
	inline void sincos<double>(const reg x, reg &s, reg &c) {
		s = (reg)_mm512_sincos_pd((__m512d*) &c, (__m512d)x);
	}

	template <>
	inline void sincos<float>(const reg x, reg &s, reg &c) {
		s = _mm512_sincos_ps(&c, x);
	}
#endif
#endif

	// ---------------------------------------------------------------------------------------------------------- fmadd
	template <>
	inline reg fmadd<double>(const reg v1, const reg v2, const reg v3) {
		return _mm512_castpd_ps(_mm512_fmadd_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _mm512_castps_pd(v3)));
	}

	template <>
	inline reg fmadd<float>(const reg v1, const reg v2, const reg v3) {
		return _mm512_fmadd_ps(v1, v2, v3);
	}

#if defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg fmadd<int32_t>(const reg v1, const reg v2, const reg v3) {
		return _mm512_castsi512_ps(_mm512_fmadd_epi32(_mm512_castps_si512(v1), _mm512_castps_si512(v2), _mm512_castps_si512(v3)));
	}
#endif

	// --------------------------------------------------------------------------------------------------------- fnmadd
	template <>
	inline reg fnmadd<double>(const reg v1, const reg v2, const reg v3) {
		return _mm512_castpd_ps(_mm512_fnmadd_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _mm512_castps_pd(v3)));
	}

	template <>
	inline reg fnmadd<float>(const reg v1, const reg v2, const reg v3) {
		return _mm512_fnmadd_ps(v1, v2, v3);
	}

	// ---------------------------------------------------------------------------------------------------------- fmsub
	template <>
	inline reg fmsub<double>(const reg v1, const reg v2, const reg v3) {
		return _mm512_castpd_ps(_mm512_fmsub_pd(_mm512_castps_pd(v1), _mm512_castps_pd(v2), _mm512_castps_pd(v3)));
	}

	template <>
	inline reg fmsub<float>(const reg v1, const reg v2, const reg v3) {
		return _mm512_fmsub_ps(v1, v2, v3);
	}

	// ----------------------------------------------------------------------------------------------------------- lrot

	// ----------------------------------------------------------------------------------------------------------- rrot

	// ----------------------------------------------------------------------------------------------------------- div2
	template <>
	inline reg div2<float>(const reg v1) {
		return mul<float>(v1, set1<float>(0.5f));
	}

	template <>
	inline reg div2<double>(const reg v1) {
		return mul<double>(v1, set1<double>(0.5));
	}

	template <>
	inline reg div2<int32_t>(const reg v1) {
		// return _mm512_castsi512_ps(_mm512_srai_epi32(_mm512_castps_si512(v1), 1)); // seems to do not work
		reg abs_v1 = abs<int32_t>(v1);
		reg sh = rshift<int32_t>(abs_v1, 1);
		sh = neg<int32_t>(sh, v1);
		return sh;
	}

#if defined(__AVX512BW__)
	template <>
	inline reg div2<int16_t>(const reg v1) {
		// return _mm512_castsi512_ps(_mm512_srai_epi16(_mm512_castps_si512(v1), 1)); // seems to do not work
		reg abs_v1 = abs<int16_t>(v1);
		reg sh = rshift<int16_t>(abs_v1, 1);
		sh = neg<int16_t>(sh, v1);
		return sh;
	}

	template <>
	inline reg div2<int8_t>(const reg v1) {
		reg abs_v1 = abs<int8_t>(v1);
		reg sh16 = rshift<int16_t>(abs_v1, 1);
		sh16 = andnb<int8_t>(set1<int8_t>(0x80), sh16);
		reg sh8 = neg<int8_t>(sh16, v1);
		return sh8;
	}
#endif

	// ----------------------------------------------------------------------------------------------------------- div4
	template <>
	inline reg div4<float>(const reg v1) {
		return mul<float>(v1, set1<float>(0.25f));
	}

	template <>
	inline reg div4<double>(const reg v1) {
		return mul<double>(v1, set1<double>(0.25));
	}

	template <>
	inline reg div4<int32_t>(const reg v1) {
		// return _mm512_castsi512_ps(_mm512_srai_epi32(_mm512_castps_si512(v1), 2)); // seems to do not work
		reg abs_v1 = abs<int32_t>(v1);
		reg sh = rshift<int32_t>(abs_v1, 2);
		sh = neg<int32_t>(sh, v1);
		return sh;
	}

#if defined(__AVX512BW__)
	template <>
	inline reg div4<int16_t>(const reg v1) {
		// return _mm512_castsi512_ps(_mm512_srai_epi16(_mm512_castps_si512(v1), 2)); // seems to do not work
		reg abs_v1 = abs<int16_t>(v1);
		reg sh = rshift<int16_t>(abs_v1, 2);
		sh = neg<int16_t>(sh, v1);
		return sh;
	}

	template <>
	inline reg div4<int8_t>(const reg v1) {
		reg abs_v1 = abs<int8_t>(v1);
		reg sh16 = rshift<int16_t>(abs_v1, 2);
		sh16 = andnb<int8_t>(set1<int8_t>(0xc0), sh16);
		reg sh8 = neg<int8_t>(sh16, v1);
		return sh8;
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ sat
	template <>
	inline reg sat<float>(const reg v1, float min, float max) {
		return mipp::min<float>(mipp::max<float>(v1, set1<float>(min)), set1<float>(max));
	}

	template <>
	inline reg sat<double>(const reg v1, double min, double max) {
		return mipp::min<double>(mipp::max<double>(v1, set1<double>(min)), set1<double>(max));
	}

	template <>
	inline reg sat<int32_t>(const reg v1, int32_t min, int32_t max) {
		return mipp::min<int32_t>(mipp::max<int32_t>(v1, set1<int32_t>(min)), set1<int32_t>(max));
	}

	template <>
	inline reg sat<int16_t>(const reg v1, int16_t min, int16_t max) {
		return mipp::min<int16_t>(mipp::max<int16_t>(v1, set1<int16_t>(min)), set1<int16_t>(max));
	}

	template <>
	inline reg sat<int8_t>(const reg v1, int8_t min, int8_t max) {
		return mipp::min<int8_t>(mipp::max<int8_t>(v1, set1<int8_t>(min)), set1<int8_t>(max));
	}

	// ---------------------------------------------------------------------------------------------------------- round
#ifdef __AVX512F__
	template <>
	inline reg round<double>(const reg v) {
		// TODO: not sure if it works
		return _mm512_castpd_ps(_mm512_roundscale_round_pd(_mm512_castps_pd(v), 0, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC));
	}

	template <>
	inline reg round<float>(const reg v) {
		// TODO: not sure if it works
		return _mm512_roundscale_round_ps(v, 0, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
	}

#elif defined(__MIC__) || defined(__KNCNI__)
	template <>
	inline reg round<float>(const reg v) {
		return _mm512_round_ps(v, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC, _MM_EXPADJ_NONE);
	}
#endif

	// ------------------------------------------------------------------------------------------------------------ cvt
#ifdef __AVX512F__
	template <>
	inline reg cvt<float,int32_t>(const reg v) {
		return _mm512_castsi512_ps(_mm512_cvtps_epi32(v));
	}

	template <>
	inline reg cvt<int32_t,float>(const reg v) {
		return _mm512_cvtepi32_ps(_mm512_castps_si512(v));
	}

	template <>
	inline reg cvt<int16_t,int32_t>(const reg_2 v) {
		return _mm512_castsi512_ps(_mm512_cvtepi16_epi32(_mm256_castps_si256(v)));
	}
#endif

#ifdef __AVX512BW__
	template <>
	inline reg cvt<int8_t,int16_t>(const reg_2 v) {
		return _mm512_castsi512_ps(_mm512_cvtepi8_epi16(_mm_castps_si256(v)));
	}
#endif

	// ----------------------------------------------------------------------------------------------------------- pack

	// ------------------------------------------------------------------------------------------------------ reduction

#endif
