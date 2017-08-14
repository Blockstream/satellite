#ifndef SC_DECODER_SIHO_HPP_
#define SC_DECODER_SIHO_HPP_

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
template <typename B, typename R>
class SC_Decoder_SIHO;

template <typename B = int, typename R = float>
class SC_Decoder_SIHO_module : public sc_core::sc_module
{
public:
	tlm_utils::simple_target_socket   <SC_Decoder_SIHO_module> s_in;
	tlm_utils::simple_initiator_socket<SC_Decoder_SIHO_module> s_out;

private:
	SC_Decoder_SIHO<B,R> &decoder;
	mipp::vector<B> V_K;

public:
	SC_Decoder_SIHO_module(SC_Decoder_SIHO<B,R> &decoder, const sc_core::sc_module_name name = "SC_Decoder_SIHO_module")
	: sc_module(name), s_in ("s_in"), s_out("s_out"),
	  decoder(decoder),
	  V_K(decoder.get_K() * decoder.get_n_frames())
	{
		s_in.register_b_transport(this, &SC_Decoder_SIHO_module::b_transport);
	}

	const mipp::vector<B>& get_V_K()
	{
		return V_K;
	}

private:
	void b_transport(tlm::tlm_generic_payload& trans, sc_core::sc_time& t)
	{
		if (decoder.get_N() * decoder.get_n_frames() != (int)(trans.get_data_length() / sizeof(R)))
		{
			std::stringstream message;
			message << "'decoder.get_N()' * 'decoder.get_n_frames()' has to be equal to "
			        << "'trans.get_data_length()' / 'sizeof(R)' ('decoder.get_N()' = " << decoder.get_N()
			        << ", 'decoder.get_n_frames()' = " << decoder.get_n_frames()
			        << ", 'trans.get_data_length()' = " << trans.get_data_length()
			        << ", 'sizeof(R)' = " << sizeof(R) << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, message.str());
		}

		const auto Y_N = (R*)trans.get_data_ptr();

		decoder.decode_siho(Y_N, V_K.data());

		tlm::tlm_generic_payload payload;
		payload.set_data_ptr((unsigned char*)V_K.data());
		payload.set_data_length(V_K.size() * sizeof(B));

		sc_core::sc_time zero_time(sc_core::SC_ZERO_TIME);
		s_out->b_transport(payload, zero_time);
	}
};

template <typename B, typename R>
class SC_Decoder_SIHO : public Decoder_SIHO_i<B,R>
{
public:
	SC_Decoder_SIHO_module<B,R> *sc_module;

public:
	SC_Decoder_SIHO(const int K, const int N, const int n_frames = 1, const int simd_inter_frame_level = 1,
	                const std::string name = "SC_Decoder_SIHO")
	: Decoder_SIHO_i<B,R>(K, N, n_frames, simd_inter_frame_level, name), sc_module(nullptr) {}

	virtual ~SC_Decoder_SIHO()
	{
		if (sc_module != nullptr) { delete sc_module; sc_module = nullptr; }
	}

	void create_sc_module()
	{
		if (sc_module != nullptr) { delete sc_module; sc_module = nullptr; }
		this->sc_module = new SC_Decoder_SIHO_module<B,R>(*this, this->name.c_str());
	}
};

template <typename B = int, typename R = float>
using Decoder_SIHO = SC_Decoder_SIHO<B,R>;
}
}
#else
#include "SPU_Decoder_SIHO.hpp"
#endif

#endif /* DECODER_HPP_ */
