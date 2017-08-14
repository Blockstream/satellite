#include "Tools/Exception/exception.hpp"

#include "Module/Encoder/NO/Encoder_NO.hpp"
#include "Module/Encoder/AZCW/Encoder_AZCW.hpp"
#include "Module/Encoder/Coset/Encoder_coset.hpp"
#include "Module/Encoder/User/Encoder_user.hpp"

#include "Encoder.hpp"

using namespace aff3ct;
using namespace aff3ct::factory;

const std::string aff3ct::factory::Encoder::name   = "Encoder";
const std::string aff3ct::factory::Encoder::prefix = "enc";

template <typename B>
module::Encoder<B>* Encoder
::build(const parameters &params)
{
	     if (params.type == "NO"   ) return new module::Encoder_NO   <B>(params.K,                           params.n_frames);
	else if (params.type == "AZCW" ) return new module::Encoder_AZCW <B>(params.K, params.N_cw,              params.n_frames);
	else if (params.type == "COSET") return new module::Encoder_coset<B>(params.K, params.N_cw, params.seed, params.n_frames);
	else if (params.type == "USER" ) return new module::Encoder_user <B>(params.K, params.N_cw, params.path, params.n_frames);

	throw tools::cannot_allocate(__FILE__, __LINE__, __func__);
}

void Encoder
::build_args(arg_map &req_args, arg_map &opt_args, const std::string p)
{
	req_args[{p+"-info-bits", "K"}] =
		{"positive_int",
		 "useful number of bit transmitted (information bits)."};

	req_args[{p+"-cw-size", "N"}] =
		{"positive_int",
		 "the codeword size."};

	opt_args[{p+"-fra", "F"}] =
		{"positive_int",
		 "set the number of inter frame level to process."};

	opt_args[{p+"-type"}] =
		{"string",
		 "select the type of encoder you want to use.",
		 "NO, AZCW, COSET, USER"};

	opt_args[{p+"-path"}] =
		{"string",
		 "path to a file containing one or a set of pre-computed codewords, to use with \"--enc-type USER\"."};

	opt_args[{p+"-seed", "S"}] =
		{"positive_int",
		 "seed used to initialize the pseudo random generators."};
}

void Encoder
::store_args(const arg_val_map &vals, parameters &params, const std::string p)
{
	if(exist(vals, {p+"-info-bits", "K"})) params.K          = std::stoi(vals.at({p+"-info-bits", "K"}));
	if(exist(vals, {p+"-cw-size",   "N"})) params.N_cw       = std::stoi(vals.at({p+"-cw-size",   "N"}));
	if(exist(vals, {p+"-fra",       "F"})) params.n_frames   = std::stoi(vals.at({p+"-fra",       "F"}));
	if(exist(vals, {p+"-seed",      "S"})) params.seed       = std::stoi(vals.at({p+"-seed",      "S"}));
	if(exist(vals, {p+"-type"          })) params.type       =           vals.at({p+"-type"          });
	if(exist(vals, {p+"-path"          })) params.path       =           vals.at({p+"-path"          });
	if(exist(vals, {p+"-no-sys"        })) params.systematic = false;

	params.R = (float)params.K / (float)params.N_cw;
}

void Encoder
::make_header(params_list& head_enc, const parameters& params, const bool full)
{
	head_enc.push_back(std::make_pair("Type", params.type));
	if (full) head_enc.push_back(std::make_pair("Info. bits (K)", std::to_string(params.K)));
	if (full) head_enc.push_back(std::make_pair("Codeword size (N)", std::to_string(params.N_cw)));
	if (full) head_enc.push_back(std::make_pair("Code rate (R)", std::to_string(params.R)));
	if (full) head_enc.push_back(std::make_pair("Inter frame level", std::to_string(params.n_frames)));
	head_enc.push_back(std::make_pair("Systematic", ((params.systematic) ? "yes" : "no")));
	if (params.type == "USER")
		head_enc.push_back(std::make_pair("Path", params.path));
	if (params.type == "COSET" && full)
		head_enc.push_back(std::make_pair("Seed", std::to_string(params.seed)));

}

// ==================================================================================== explicit template instantiation
#include "Tools/types.h"
#ifdef MULTI_PREC
template aff3ct::module::Encoder<B_8 >* aff3ct::factory::Encoder::build<B_8 >(const aff3ct::factory::Encoder::parameters&);
template aff3ct::module::Encoder<B_16>* aff3ct::factory::Encoder::build<B_16>(const aff3ct::factory::Encoder::parameters&);
template aff3ct::module::Encoder<B_32>* aff3ct::factory::Encoder::build<B_32>(const aff3ct::factory::Encoder::parameters&);
template aff3ct::module::Encoder<B_64>* aff3ct::factory::Encoder::build<B_64>(const aff3ct::factory::Encoder::parameters&);
#else
template aff3ct::module::Encoder<B>* aff3ct::factory::Encoder::build<B>(const aff3ct::factory::Encoder::parameters&);
#endif
// ==================================================================================== explicit template instantiation
