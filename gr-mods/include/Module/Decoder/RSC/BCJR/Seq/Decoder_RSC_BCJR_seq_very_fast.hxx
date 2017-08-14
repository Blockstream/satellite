#include <sstream>

#include "Tools/Exception/exception.hpp"

#include "Decoder_RSC_BCJR_seq_very_fast.hpp"

namespace aff3ct
{
namespace module
{
template <typename B, typename R, typename RD, tools::proto_max<R> MAX1, tools::proto_max<RD> MAX2>
Decoder_RSC_BCJR_seq_very_fast<B,R,RD,MAX1,MAX2>
::Decoder_RSC_BCJR_seq_very_fast(const int &K,
                                 const std::vector<std::vector<int>> &trellis,
                                 const bool buffered_encoding,
                                 const int n_frames,
                                 const std::string name)
: Decoder_RSC_BCJR_seq<B,R>(K, trellis, buffered_encoding, n_frames, name)
{
	if (this->K % mipp::nElReg<R>())
	{
		std::stringstream message;
		message << "'K' has to be divisible by 'mipp::nElReg<R>()' ('K' = " << this->K
		        << ", 'mipp::nElReg<R>()' = " << mipp::nElReg<R>() << ").";
		throw tools::invalid_argument(__FILE__, __LINE__, __func__, message.str());
	}
}

template <typename B, typename R, typename RD, tools::proto_max<R> MAX1, tools::proto_max<RD> MAX2>
Decoder_RSC_BCJR_seq_very_fast<B,R,RD,MAX1,MAX2>
::~Decoder_RSC_BCJR_seq_very_fast()
{
}

template <typename B, typename R, typename RD, tools::proto_max<R> MAX1, tools::proto_max<RD> MAX2>
void Decoder_RSC_BCJR_seq_very_fast<B,R,RD,MAX1,MAX2>
::compute_gamma(const R *sys, const R *par)
{
	// compute gamma values (auto-vectorized loop)
	for (auto i = 0; i < this->K +3; i++)
	{
		// there is a big loss of precision here in fixed point
		this->gamma[0][i] = RSC_BCJR_seq_div_or_not<R>::apply(sys[i] + par[i]);
		// there is a big loss of precision here in fixed point
		this->gamma[1][i] = RSC_BCJR_seq_div_or_not<R>::apply(sys[i] - par[i]);
	}
}

template <typename B, typename R, typename RD, tools::proto_max<R> MAX1, tools::proto_max<RD> MAX2>
void Decoder_RSC_BCJR_seq_very_fast<B,R,RD,MAX1,MAX2>
::compute_alpha()
{
	// compute alpha values [trellis forward traversal ->]
	for (auto i = 1; i < this->K +3; i++)
	{
		const auto g0 = this->gamma[0][i -1];
		const auto g1 = this->gamma[1][i -1];

		this->alpha[0][i] = MAX1(this->alpha[0][i -1] + g0, this->alpha[1][i -1] - g0);
		this->alpha[1][i] = MAX1(this->alpha[3][i -1] + g1, this->alpha[2][i -1] - g1);
		this->alpha[2][i] = MAX1(this->alpha[4][i -1] + g1, this->alpha[5][i -1] - g1);
		this->alpha[3][i] = MAX1(this->alpha[7][i -1] + g0, this->alpha[6][i -1] - g0);
		this->alpha[4][i] = MAX1(this->alpha[1][i -1] + g0, this->alpha[0][i -1] - g0);
		this->alpha[5][i] = MAX1(this->alpha[2][i -1] + g1, this->alpha[3][i -1] - g1);
		this->alpha[6][i] = MAX1(this->alpha[5][i -1] + g1, this->alpha[4][i -1] - g1);
		this->alpha[7][i] = MAX1(this->alpha[6][i -1] + g0, this->alpha[7][i -1] - g0);

		RSC_BCJR_seq_normalize<R>::apply(this->alpha, i);
	}
}

// template <typename B, typename R, typename RD, tools::proto_max<R> MAX1, tools::proto_max<RD> MAX2>
// void Decoder_RSC_BCJR_seq_very_fast<B,R,RD,MAX1,MAX2>
// ::compute_beta_ext(const R *sys, R *ext)
// {
// 	constexpr int idx_b1[8] = {0, 4, 5, 1, 2, 6, 7, 3};
// 	constexpr int idx_b2[8] = {4, 0, 1, 5, 6, 2, 3, 7};
// 	constexpr int idx_g2[8] = {0, 0, 1, 1, 1, 1, 0, 0};

// 	// compute the first beta values [trellis backward traversal <-]
// 	R beta_prev[8];
// 	for (auto j = 0; j < 8; j++)
// 		beta_prev[j] = this->alpha[j][0];
// 	for (auto i = this->K +2; i > this->K; i--)
// 	{
// 		R beta_cur[8];
// 		for (auto j = 0; j < 8; j++)
// 			beta_cur[j] = MAX1(beta_prev[idx_b1[j]] + this->gamma[idx_g2[j]][i],
// 			                   beta_prev[idx_b2[j]] - this->gamma[idx_g2[j]][i]);

// 		RSC_BCJR_seq_normalize<R>::apply(beta_cur, i);
	
// 		for (auto j = 0; j < 8; j++)
// 			beta_prev[j] = beta_cur[j];
// 	}

// 	constexpr int block = mipp::nElReg<R>();
// 	R beta_tmp[8][block];
// 	for (auto k = 0; k < 8; k++)
// 		beta_tmp[k][block -1] = beta_prev[k];

// 	// compute the beta values [trellis backward traversal <-] + compute extrinsic values
// 	for (auto i = this->K -1; i >= 0; i -= block)
// 	{
// 		// compute the beta values
// 		for (auto k = 0; k < 8; k++)
// 			beta_tmp[k][0] = MAX1(beta_tmp[idx_b1[k]][block -1] + this->gamma[idx_g2[k]][i+1],
// 			                      beta_tmp[idx_b2[k]][block -1] - this->gamma[idx_g2[k]][i+1]);
// 		RSC_BCJR_seq_normalize<R>::apply(beta_tmp, 0);

// 		for (auto j = 1; j < block; j++)
// 		{
// 			for (auto k = 0; k < 8; k++)
// 				beta_tmp[k][j] = MAX1(beta_tmp[idx_b1[k]][j-1] + this->gamma[idx_g2[k]][(i-j)+1],
// 				                      beta_tmp[idx_b2[k]][j-1] - this->gamma[idx_g2[k]][(i-j)+1]);

// 			RSC_BCJR_seq_normalize<R>::apply(beta_tmp, j);
// 		}

// 		// (auto-vectorized loop)
// 		RD tmp_post[2][8][block];
// 		for (auto j = 0; j < block; j++)
// 		{
// 			for (auto k = 0; k < 8; k++)
// 				tmp_post[0][k][j] = (RD)this->alpha[       k ][i-j] + 
// 				                    (RD)beta_tmp   [idx_b1[k]][  j] + 
// 				                    (RD)this->gamma[idx_g2[k]][i-j];

// 			for (auto k = 0; k < 8; k++)
// 				tmp_post[1][k][j] = (RD)this->alpha[       k ][i-j] + 
// 				                    (RD)beta_tmp   [idx_b2[k]][  j] - 
// 				                    (RD)this->gamma[idx_g2[k]][i-j];
// 		}

// 		// (auto-vectorized loop)
// 		for (auto j = 0; j < block; j++)
// 		{
// 			auto max0 = tmp_post[0][0][j];
// 			for (auto k = 1; k < 8; k++) // (auto-unrolled loop)
// 				max0 = MAX2(max0, tmp_post[0][k][j]);

// 			auto max1 = tmp_post[1][0][j];
// 			for (auto k = 1; k < 8; k++) // (auto-unrolled loop)
// 				max1 = MAX2(max1, tmp_post[1][k][j]);

// 			ext[i-j] = RSC_BCJR_seq_post<R,RD>::compute(max0 - max1) - sys[i-j];
// 		}
// 	}
// }

template <typename B, typename R, typename RD, tools::proto_max<R> MAX1, tools::proto_max<RD> MAX2>
void Decoder_RSC_BCJR_seq_very_fast<B,R,RD,MAX1,MAX2>
::compute_beta_ext(const R *sys, R *ext)
{
	// compute the first beta values [trellis backward traversal <-]
	R beta_prev[8];
	for (auto j = 0; j < 8; j++)
		beta_prev[j] = this->alpha[j][0];
	for (auto i = this->K +2; i > this->K; i--)
	{
		const auto g0 = this->gamma[0][i];
		const auto g1 = this->gamma[1][i];

		R beta_cur[8];
		beta_cur[0] = MAX1(beta_prev[0] + g0, beta_prev[4] - g0);
		beta_cur[1] = MAX1(beta_prev[4] + g0, beta_prev[0] - g0);
		beta_cur[2] = MAX1(beta_prev[5] + g1, beta_prev[1] - g1);
		beta_cur[3] = MAX1(beta_prev[1] + g1, beta_prev[5] - g1);
		beta_cur[4] = MAX1(beta_prev[2] + g1, beta_prev[6] - g1);
		beta_cur[5] = MAX1(beta_prev[6] + g1, beta_prev[2] - g1);
		beta_cur[6] = MAX1(beta_prev[7] + g0, beta_prev[3] - g0);
		beta_cur[7] = MAX1(beta_prev[3] + g0, beta_prev[7] - g0);

		RSC_BCJR_seq_normalize<R>::apply(beta_cur, i);
	
		std::copy(beta_cur +0, beta_cur +8 -1, beta_prev);
	}

	constexpr int block = mipp::nElReg<R>();
	R beta_tmp[8][block];
	for (auto k = 0; k < 8; k++)
		beta_tmp[k][block -1] = beta_prev[k];

	// compute the beta values [trellis backward traversal <-] + compute extrinsic values
	for (auto i = this->K -1; i >= 0; i -= block)
	{
		const auto g0 = this->gamma[0][i+1];
		const auto g1 = this->gamma[1][i+1];

		// compute the beta values
		beta_tmp[0][0] = MAX1(beta_tmp[0][block -1] + g0, beta_tmp[4][block -1] - g0);
		beta_tmp[1][0] = MAX1(beta_tmp[4][block -1] + g0, beta_tmp[0][block -1] - g0);
		beta_tmp[2][0] = MAX1(beta_tmp[5][block -1] + g1, beta_tmp[1][block -1] - g1);
		beta_tmp[3][0] = MAX1(beta_tmp[1][block -1] + g1, beta_tmp[5][block -1] - g1);
		beta_tmp[4][0] = MAX1(beta_tmp[2][block -1] + g1, beta_tmp[6][block -1] - g1);
		beta_tmp[5][0] = MAX1(beta_tmp[6][block -1] + g1, beta_tmp[2][block -1] - g1);
		beta_tmp[6][0] = MAX1(beta_tmp[7][block -1] + g0, beta_tmp[3][block -1] - g0);
		beta_tmp[7][0] = MAX1(beta_tmp[3][block -1] + g0, beta_tmp[7][block -1] - g0);
		RSC_BCJR_seq_normalize<R>::apply(beta_tmp, 0);

		for (auto j = 1; j < block; j++)
		{
			const auto g0 = this->gamma[0][(i-j)+1];
			const auto g1 = this->gamma[1][(i-j)+1];

			// compute the beta values
			beta_tmp[0][j] = MAX1(beta_tmp[0][j-1] + g0, beta_tmp[4][j-1] - g0);
			beta_tmp[1][j] = MAX1(beta_tmp[4][j-1] + g0, beta_tmp[0][j-1] - g0);
			beta_tmp[2][j] = MAX1(beta_tmp[5][j-1] + g1, beta_tmp[1][j-1] - g1);
			beta_tmp[3][j] = MAX1(beta_tmp[1][j-1] + g1, beta_tmp[5][j-1] - g1);
			beta_tmp[4][j] = MAX1(beta_tmp[2][j-1] + g1, beta_tmp[6][j-1] - g1);
			beta_tmp[5][j] = MAX1(beta_tmp[6][j-1] + g1, beta_tmp[2][j-1] - g1);
			beta_tmp[6][j] = MAX1(beta_tmp[7][j-1] + g0, beta_tmp[3][j-1] - g0);
			beta_tmp[7][j] = MAX1(beta_tmp[3][j-1] + g0, beta_tmp[7][j-1] - g0);
			RSC_BCJR_seq_normalize<R>::apply(beta_tmp, j);
		}

		// (auto-vectorized loop)
		RD tmp_post[2][8][block];
		for (auto j = 0; j < block; j++)
		{
			const auto g0 = this->gamma[0][i-j];
			const auto g1 = this->gamma[1][i-j];

			tmp_post[0][0][j] = (RD)this->alpha[0][i-j] + (RD)beta_tmp[0][j] + (RD)g0;
			tmp_post[0][1][j] = (RD)this->alpha[1][i-j] + (RD)beta_tmp[4][j] + (RD)g0;
			tmp_post[0][2][j] = (RD)this->alpha[2][i-j] + (RD)beta_tmp[5][j] + (RD)g1;
			tmp_post[0][3][j] = (RD)this->alpha[3][i-j] + (RD)beta_tmp[1][j] + (RD)g1;
			tmp_post[0][4][j] = (RD)this->alpha[4][i-j] + (RD)beta_tmp[2][j] + (RD)g1;
			tmp_post[0][5][j] = (RD)this->alpha[5][i-j] + (RD)beta_tmp[6][j] + (RD)g1;
			tmp_post[0][6][j] = (RD)this->alpha[6][i-j] + (RD)beta_tmp[7][j] + (RD)g0;
			tmp_post[0][7][j] = (RD)this->alpha[7][i-j] + (RD)beta_tmp[3][j] + (RD)g0;

			tmp_post[1][0][j] = (RD)this->alpha[0][i-j] + (RD)beta_tmp[4][j] - (RD)g0;
			tmp_post[1][1][j] = (RD)this->alpha[1][i-j] + (RD)beta_tmp[0][j] - (RD)g0;
			tmp_post[1][2][j] = (RD)this->alpha[2][i-j] + (RD)beta_tmp[1][j] - (RD)g1;
			tmp_post[1][3][j] = (RD)this->alpha[3][i-j] + (RD)beta_tmp[5][j] - (RD)g1;
			tmp_post[1][4][j] = (RD)this->alpha[4][i-j] + (RD)beta_tmp[6][j] - (RD)g1;
			tmp_post[1][5][j] = (RD)this->alpha[5][i-j] + (RD)beta_tmp[2][j] - (RD)g1;
			tmp_post[1][6][j] = (RD)this->alpha[6][i-j] + (RD)beta_tmp[3][j] - (RD)g0;
			tmp_post[1][7][j] = (RD)this->alpha[7][i-j] + (RD)beta_tmp[7][j] - (RD)g0;
		}

		// (auto-vectorized loop)
		for (auto j = 0; j < block; j++)
		{
			auto max0 = tmp_post[0][0][j];
			for (auto k = 1; k < 8; k++) // (auto-unrolled loop)
				max0 = MAX2(max0, tmp_post[0][k][j]);

			auto max1 = tmp_post[1][0][j];
			for (auto k = 1; k < 8; k++) // (auto-unrolled loop)
				max1 = MAX2(max1, tmp_post[1][k][j]);

			ext[i-j] = RSC_BCJR_seq_post<R,RD>::compute(max0 - max1) - sys[i-j];
		}
	}
}

template <typename B, typename R, typename RD, tools::proto_max<R> MAX1, tools::proto_max<RD> MAX2>
void Decoder_RSC_BCJR_seq_very_fast<B,R,RD,MAX1,MAX2>
::_decode_siso(const R *sys, const R *par, R *ext, const int frame_id)
{
	this->compute_gamma   (sys, par);
	this->compute_alpha   (        );
	this->compute_beta_ext(sys, ext);
}
}
}
