#ifndef DECODER_TURBO_HPP_
#define DECODER_TURBO_HPP_

#include <vector>
#include <functional>
#include <mipp/mipp.h>

#include "Module/Interleaver/Interleaver.hpp"

#include "../Decoder_SIHO.hpp"
#include "../Decoder_SISO.hpp"

namespace aff3ct
{
namespace module
{
template <typename B = int, typename R = float>
class Decoder_turbo : public Decoder_SIHO<B,R>
{
protected:
	const int  n_ite; // number of iterations
	const bool buffered_encoding;

	const Interleaver<int> &pi;
	Decoder_SISO<R> &siso_n;
	Decoder_SISO<R> &siso_i;

	mipp::vector<R> l_sn;  // systematic LLRs                  in the natural     domain
	mipp::vector<R> l_si;  // systematic LLRs                  in the interleaved domain
	mipp::vector<R> l_sen; // systematic LLRs + extrinsic LLRs in the natural     domain
	mipp::vector<R> l_sei; // systematic LLRs + extrinsic LLRs in the interleaved domain
	mipp::vector<R> l_pn;  // parity     LLRs                  in the natural     domain
	mipp::vector<R> l_pi;  // parity     LLRs                  in the interleaved domain
	mipp::vector<R> l_e1n; // extrinsic  LLRs                  in the natural     domain
	mipp::vector<R> l_e2n; // extrinsic  LLRs                  in the natural     domain
	mipp::vector<R> l_e1i; // extrinsic  LLRs                  in the interleaved domain
	mipp::vector<R> l_e2i; // extrinsic  LLRs                  in the interleaved domain
	mipp::vector<B> s;     // bit decision

	std::vector<std::function<bool(const int ite,
	                               const mipp::vector<R>& sys,
	                                     mipp::vector<R>& ext,
	                                     mipp::vector<B>& s)>> callbacks_siso_n;
	std::vector<std::function<bool(const int ite,
	                               const mipp::vector<R>& sys,
	                                     mipp::vector<R>& ext)>> callbacks_siso_i;
	std::vector<std::function<void(const int n_ite)>> callbacks_end;

	Decoder_turbo(const int& K,
	              const int& N,
	              const int& n_ite,
	              const Interleaver<int> &pi,
	              Decoder_SISO<R> &siso_n,
	              Decoder_SISO<R> &siso_i,
	              const bool buffered_encoding = true,
	              const std::string name = "Decoder_turbo");
	virtual ~Decoder_turbo();

public:
	void add_handler_siso_n(std::function<bool(const int,
	                                           const mipp::vector<R>&,
	                                                 mipp::vector<R>&,
	                                                 mipp::vector<B>&)> callback);
	void add_handler_siso_i(std::function<bool(const int,
	                                           const mipp::vector<R>&,
	                                                 mipp::vector<R>&)> callback);
	void add_handler_end(std::function<void(const int)> callback);

protected:
	virtual void _load (const R *Y_N, const int frame_id);
	virtual void _store(      B *V_K                    ) const;

private:
	void buffered_load(const R *Y_N, const int frame_id);
	void standard_load(const R *Y_N, const int frame_id);
};
}
}

#endif /* DECODER_TURBO_HPP_ */
