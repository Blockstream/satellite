#ifndef SC_DECODER_HIHO_HPP_
#define SC_DECODER_HIHO_HPP_

#ifdef SYSTEMC_MODULE
#include <vector>
#include <string>
#include <sstream>
#include <systemc>
#include <tlm>
#include <tlm_utils/simple_target_socket.h>
#include <tlm_utils/simple_initiator_socket.h>
#include <mipp/mipp.h>

#include "Tools/Exception/exception.hpp"

namespace aff3ct
{
namespace module
{
template <typename B>
class SC_Decoder_HIHO;

template <typename B = int>
class SC_Decoder_HIHO_module : public sc_core::sc_module
{
public:
	tlm_utils::simple_target_socket   <SC_Decoder_HIHO_module> s_in;
	tlm_utils::simple_initiator_socket<SC_Decoder_HIHO_module> s_out;

private:
	SC_Decoder_HIHO<B> &decoder;
	mipp::vector<B> V_K;

public:
	SC_Decoder_HIHO_module(SC_Decoder_HIHO<B> &decoder, const sc_core::sc_module_name name = "SC_Decoder_HIHO_module")
	: sc_module(name), s_in ("s_in"), s_out("s_out"),
	  decoder(decoder),
	  V_K(decoder.get_K() * decoder.get_n_frames())
	{
		s_in.register_b_transport(this, &SC_Decoder_HIHO_module::b_transport);
	}

	const mipp::vector<B>& get_V_K()
	{
		return V_K;
	}

private:
	void b_transport(tlm::tlm_generic_payload& trans, sc_core::sc_time& t)
	{
		if (decoder.get_N() * decoder.get_n_frames() != (int)(trans.get_data_length() / sizeof(B)))
		{
			std::stringstream message;
			message << "'decoder.get_N()' * 'decoder.get_n_frames()' has to be equal to "
			        << "'trans.get_data_length()' / 'sizeof(B)' ('decoder.get_N()' = " << decoder.get_N()
			        << ", 'decoder.get_n_frames()' = " << decoder.get_n_frames()
			        << ", 'trans.get_data_length()' = " << trans.get_data_length()
			        << ", 'sizeof(B)' = " << sizeof(B) << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		const auto Y_N = (B*)trans.get_data_ptr();

		decoder.decode_hiho(Y_N, V_K.data());

		tlm::tlm_generic_payload payload;
		payload.set_data_ptr((unsigned char*)V_K.data());
		payload.set_data_length(V_K.size() * sizeof(B));

		sc_core::sc_time zero_time(sc_core::SC_ZERO_TIME);
		s_out->b_transport(payload, zero_time);
	}
};

template <typename B>
class SC_Decoder_HIHO : public Decoder_HIHO_i<B>
{
public:
	SC_Decoder_HIHO_module<B> *sc_module;

public:
	SC_Decoder_HIHO(const int K, const int N, const int n_frames = 1, const int simd_inter_frame_level = 1,
	                const std::string name = "SC_Decoder_HIHO")
	: Decoder_HIHO_i<B>(K, N, n_frames, simd_inter_frame_level, name), sc_module(nullptr) {}

	virtual ~SC_Decoder_HIHO()
	{
		if (sc_module != nullptr) { delete sc_module; sc_module = nullptr; }
	}

	void create_sc_module()
	{
		if (sc_module != nullptr) { delete sc_module; sc_module = nullptr; }
		this->sc_module = new SC_Decoder_HIHO_module<B>(*this, this->name.c_str());
	}
};

template <typename B = int>
using Decoder_HIHO = SC_Decoder_HIHO<B>;
}
}
#else
#include "SPU_Decoder_HIHO.hpp"
#endif

#endif /* SC_DECODER_HIHO_HPP_ */
