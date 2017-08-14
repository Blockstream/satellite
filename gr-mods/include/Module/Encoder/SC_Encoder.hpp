#ifndef SC_ENCODER_HPP_
#define SC_ENCODER_HPP_

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
class SC_Encoder;

template <typename B = int>
class SC_Encoder_module : public sc_core::sc_module
{
public:
	tlm_utils::simple_target_socket   <SC_Encoder_module> s_in;
	tlm_utils::simple_initiator_socket<SC_Encoder_module> s_out;

private:
	SC_Encoder<B> &encoder;
	mipp::vector<B> X_N;

public:
	SC_Encoder_module(SC_Encoder<B> &encoder, const sc_core::sc_module_name name = "SC_Encoder_module")
	: sc_module(name), s_in("s_in"), s_out("s_out"),
	  encoder(encoder),
	  X_N(encoder.get_N() * encoder.get_n_frames())
	{
		s_in.register_b_transport(this, &SC_Encoder_module::b_transport);
	}

	const mipp::vector<B>& get_X_N()
	{
		return X_N;
	}

private:
	void b_transport(tlm::tlm_generic_payload& trans, sc_core::sc_time& t)
	{
		if (encoder.get_K() * encoder.get_n_frames() != (int)(trans.get_data_length() / sizeof(B)))
		{
			std::stringstream message;
			message << "'encoder.get_K()' * 'encoder.get_n_frames()' has to be equal to "
			        << "'trans.get_data_length()' / 'sizeof(B)' ('encoder.get_K()' = " << encoder.get_K()
			        << ", 'encoder.get_n_frames()' = " << encoder.get_n_frames()
			        << ", 'trans.get_data_length()' = " << trans.get_data_length()
			        << ", 'sizeof(B)' = " << sizeof(B) << ").";
			throw tools::length_error(__FILE__, __LINE__, __func__, "aff3ct::module::Encoder: TLM input data size is invalid.");
		}

		const auto U_K = (B*)trans.get_data_ptr();

		encoder.encode(U_K, X_N.data());

		tlm::tlm_generic_payload payload;
		payload.set_data_ptr((unsigned char*)X_N.data());
		payload.set_data_length(X_N.size() * sizeof(B));

		sc_core::sc_time zero_time(sc_core::SC_ZERO_TIME);
		s_out->b_transport(payload, zero_time);
	}
};

template <typename B>
class SC_Encoder : public Encoder_i<B>
{
public:
	SC_Encoder_module<B> *sc_module;

public:
	SC_Encoder(const int K, const int N, const int n_frames = 1, const std::string name = "SC_Encoder")
	: Encoder_i<B>(K, N, n_frames, name), sc_module(nullptr) {}

	virtual ~SC_Encoder()
	{
		if (sc_module != nullptr) { delete sc_module; sc_module = nullptr; }
	}

	void create_sc_module()
	{
		if (sc_module != nullptr) { delete sc_module; sc_module = nullptr; }
		this->sc_module = new SC_Encoder_module<B>(*this, this->name.c_str());
	}
};

template <typename B = int>
using Encoder = SC_Encoder<B>;
}
}
#else
#include "SPU_Encoder.hpp"
#endif

#endif /* SC_ENCODER_HPP_ */
