#include <fstream>
#include <sstream>

#include "Tools/Exception/exception.hpp"

#include "Encoder_user.hpp"

using namespace aff3ct::module;
using namespace aff3ct::tools;

template <typename B>
Encoder_user<B>
::Encoder_user(const int K, const int N, const std::string filename, const int n_frames, const std::string name)
: Encoder<B>(K, N, n_frames, name), codewords(), cw_counter(0)
{
	if (filename.empty())
		throw invalid_argument(__FILE__, __LINE__, __func__, "'filename' should not be empty.");

	std::ifstream file(filename.c_str(), std::ios::in);

	if (file.is_open())
	{
		int n_cw = 0, src_size = 0, cw_size = 0;

		file >> n_cw;
		file >> cw_size;
		file >> src_size;

		if (n_cw <= 0 || src_size <= 0 || cw_size <= 0)
		{
			std::stringstream message;
			message << "'n_cw', 'src_size' and 'cw_size' have to be greater than 0 ('n_cw' = " << n_cw
			        << ", 'src_size' = " << src_size << ", 'cw_size' = " << cw_size << ").";
			throw runtime_error(__FILE__, __LINE__, __func__, message.str());
		}

		if (cw_size < src_size)
		{
			std::stringstream message;
			message << "'cw_size' has to be equal or greater than 'src_size' ('cw_size' = " << cw_size
			        << ", 'src_size' = " << src_size << ").";
			throw runtime_error(__FILE__, __LINE__, __func__, message.str());
		}

		this->codewords.resize(n_cw);
		for (auto i = 0; i < n_cw; i++)
			this->codewords[i].resize(cw_size);

		if ((src_size == this->K) && (cw_size == this->N))
		{
			for (auto i = 0; i < n_cw; i++)
				for (auto j = 0; j < cw_size; j++)
				{
					int symbol;
					file >> symbol;
					this->codewords[i][j] = (B)symbol;
				}
		}
		else
		{
			file.close();

			std::stringstream message;
			message << "The number of information bits or the codeword size is wrong "
			        << "(read: {" << src_size << "," << cw_size << "}, "
			        << "expected: {" << this->K << "," << this->N << "}).";
			throw runtime_error(__FILE__, __LINE__, __func__, message.str());
		}

		file.close();
	}
	else
	{
		std::stringstream message;
		message << "Can't open '" + filename + "' file.";
		throw invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}
}

template <typename B>
Encoder_user<B>
::~Encoder_user()
{
}

template <typename B>
void Encoder_user<B>
::_encode(const B *U_K, B *X_N, const int frame_id)
{
	std::copy(this->codewords[this->cw_counter].begin(),
	          this->codewords[this->cw_counter].end  (),
	          X_N);

	this->cw_counter = (this->cw_counter +1) % (int)this->codewords.size();
}

// ==================================================================================== explicit template instantiation 
#include "Tools/types.h"
#ifdef MULTI_PREC
template class aff3ct::module::Encoder_user<B_8>;
template class aff3ct::module::Encoder_user<B_16>;
template class aff3ct::module::Encoder_user<B_32>;
template class aff3ct::module::Encoder_user<B_64>;
#else
template class aff3ct::module::Encoder_user<B>;
#endif
// ==================================================================================== explicit template instantiation
