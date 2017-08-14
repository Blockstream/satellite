#ifndef ENCODER_RSC_SYS_HPP_
#define ENCODER_RSC_SYS_HPP_

#include "../Encoder_sys.hpp"

namespace aff3ct
{
namespace module
{
template <typename B = int>
class Encoder_RSC_sys : public Encoder_sys<B>
{
protected:
	const int n_ff;     // number of D flip-flop
	const int n_states; // number of states in the trellis

	const bool buffered_encoding;

public:
	Encoder_RSC_sys(const int& K, const int& N, const int n_ff, const int& n_frames, const bool buffered_encoding,
	                const std::string name = "Encoder_RSC_sys");
	virtual ~Encoder_RSC_sys() {}

	int get_n_ff   ();
	int tail_length() const;

	virtual std::vector<std::vector<int>> get_trellis();

protected:
	void _encode    (const B *U_K, B *X_N, const int frame_id);
	void _encode_sys(const B *U_K, B *par, const int frame_id);

	void __encode(const B* U_K, B* X_N, const int stride = 1, const bool only_parity = false);
	
	virtual int inner_encode(const int bit_sys, int &state) = 0;
	virtual int tail_bit_sys(const int &state             ) = 0;
};
}
}

#endif /* ENCODER_RSC_SYS_HPP_ */
