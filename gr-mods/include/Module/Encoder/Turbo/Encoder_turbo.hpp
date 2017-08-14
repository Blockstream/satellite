#ifndef ENCODER_TURBO_HPP_
#define ENCODER_TURBO_HPP_

#include <string>
#include <vector>

#include "../../Interleaver/Interleaver.hpp"

#include "../Encoder.hpp"
#include "../Encoder_sys.hpp"

namespace aff3ct
{
namespace module
{
template <typename B = int>
class Encoder_turbo : public Encoder<B>
{
protected:
	const Interleaver<int> &pi; // the interleaver

	Encoder_sys<B> &enco_n; // polar systematic encoder
	Encoder_sys<B> &enco_i; // sub encoder

	std::vector<B> U_K_i;   // internal buffer for the systematic bits in the interleaved domain
	std::vector<B> par_n;   // internal buffer for the encoded    bits in the natural     domain
	std::vector<B> par_i;   // internal buffer for the encoded    bits in the interleaved domain

public:
	Encoder_turbo(const int& K, const int& N, const Interleaver<int> &pi,
	              Encoder_sys<B> &enco_n, Encoder_sys<B> &enco_i, const int n_frames = 1,
	              const std::string name = "Encoder_turbo");
	virtual ~Encoder_turbo() {}

	int tail_length() const { return enco_n.tail_length() + enco_i.tail_length(); }

	virtual void encode(const B *U_K, B *X_N); using Encoder<B>::encode;
};
}
}

#endif // ENCODER_TURBO_HPP_
