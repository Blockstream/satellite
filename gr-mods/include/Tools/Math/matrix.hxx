#include <sstream>

#include "Tools/Exception/exception.hpp"

#include "matrix.h"

namespace aff3ct
{
namespace tools
{
template <typename T, class AT>
inline void rgemm(const int M, const int N, const int K,
                  const std::vector<T,AT> &A,
                  const std::vector<T,AT> &tB,
                        std::vector<T,AT> &tC)
{
	if (A.size() != unsigned(M * K))
	{
		std::stringstream message;
		message << "'A.size()' has to be equal to 'M' * 'K' ('A.size()' = " << A.size()  << ", 'M' = " << M
		        << ", 'K' = " << K << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (tB.size() != unsigned(K * N))
	{
		std::stringstream message;
		message << "'tB.size()' has to be equal to 'K' * 'N' ('tB.size()' = " << tB.size() << ", 'K' = " << K
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (tC.size() != unsigned(M * N))
	{
		std::stringstream message;
		message << "'tC.size()' has to be equal to 'M' * 'N' ('tC.size()' = " << tC.size() << ", 'M' = " << M
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	rgemm(M, N, K, A.data(), tB.data(), tC.data());
}

template <typename T>
inline void rgemm(const int M, const int N, const int K,
                  const T *A,
                  const T *tB,
                        T *tC)
{
	for (auto i = 0; i < M; i++)
		for (auto j = 0; j < N; j++)
		{
			T sum_r = 0;
			for (auto k = 0; k < K; k++)
				sum_r += A[i * K + k] * tB[j * K + k];

			tC[j * M + i] = sum_r;
		}
}

template <typename T, class AT>
inline void cgemm(const int M, const int N, const int K, 
                  const std::vector<T,AT> &A,
                  const std::vector<T,AT> &tB,
                        std::vector<T,AT> &tC)
{
	if (A.size() != unsigned(M * K * 2))
	{
		std::stringstream message;
		message << "'A.size()' has to be equal to 'M' * 'K' * 2 ('A.size()' = " << A.size() << ", 'M' = " << M
		        << ", 'K' = " << K << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (tB.size() != unsigned(K * N * 2))
	{
		std::stringstream message;
		message << "'tB.size()' has to be equal to 'K' * 'N' * 2 ('tB.size()' = " << tB.size() << ", 'K' = " << K
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (tC.size() != unsigned(M * N * 2))
	{
		std::stringstream message;
		message << "'tC.size()' has to be equal to 'M' * 'N' * 2 ('tC.size()' = " << tC.size() << ", 'M' = " << M
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	cgemm(M, N, K, A.data(), tB.data(), tC.data());
}

template <typename T>
inline void cgemm(const int M, const int N, const int K,
                  const T *A,
                  const T *tB,
                        T *tC)
{
	const T*  A_real =  A;
	const T*  A_imag =  A + ((M * K) >> 1);
	const T* tB_real = tB;
	const T* tB_imag = tB + ((N * K) >> 1);
	      T* tC_real = tC;
	      T* tC_imag = tC + ((M * N) >> 1);

	for (auto i = 0; i < M; i++) 
	{
		for (auto j = 0; j < N; j++) 
		{
			T sum_r = 0, sum_i = 0;
			for (auto k = 0; k < K; k++) 
			{
				sum_r += A_real[i * K + k] * tB_real[j * K + k] - A_imag[i * K + k] * tB_imag[j * K + k];
				sum_i += A_imag[i * K + k] * tB_real[j * K + k] + A_real[i * K + k] * tB_imag[j * K + k];
			}

			tC_real[j * M + i] = sum_r;
			tC_imag[j * M + i] = sum_i;
		}
	}
}

template <typename T, class AT>
inline void cgemm_r(const int M, const int N, const int K, 
                    const std::vector<T,AT> &A,
                    const std::vector<T,AT> &tB,
                          std::vector<T,AT> &tC)
{
	if (A.size() != unsigned(M * K * 2))
	{
		std::stringstream message;
		message << "'A.size()' has to be equal to 'M' * 'K' * 2 ('A.size()' = " << A.size() << ", 'M' = " << M
		        << ", 'K' = " << K << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (tB.size() != unsigned(K * N * 2))
	{
		std::stringstream message;
		message << "'tB.size()' has to be equal to 'K' * 'N' * 2 ('tB.size()' = " << tB.size() << ", 'K' = " << K
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (tC.size() != unsigned(M * N * 1))
	{
		std::stringstream message;
		message << "'tC.size()' has to be equal to 'M' * 'N' * 1 ('tC.size()' = " << tC.size() << ", 'M' = " << M
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	cgemm_r(M, N, K, A.data(), tB.data(), tC.data());
}

template <typename T>
inline void cgemm_r(const int M, const int N, const int K,
                    const T *A,
                    const T *tB,
                          T *tC)
{
	const T*  A_real =  A;
	const T*  A_imag =  A + ((M * K) >> 1);
	const T* tB_real = tB;
	const T* tB_imag = tB + ((N * K) >> 1);
	      T* tC_real = tC;

	for (auto i = 0; i < M; i++) 
	{
		for (auto j = 0; j < N; j++) 
		{
			T sum_r = 0;
			for (auto k = 0; k < K; k++) 
				sum_r += A_real[i * K + k] * tB_real[j * K + k] - A_imag[i * K + k] * tB_imag[j * K + k];

			tC_real[j * M + i] = sum_r;
		}
	}
}

template <typename T, class AT>
inline void real_transpose(const int M, const int N,
                           const std::vector<T,AT> &A,
                                 std::vector<T,AT> &B)
{
	if (A.size() != unsigned(M * N))
	{
		std::stringstream message;
		message << "'A.size()' has to be equal to 'M' * 'N' ('A.size()' = " << A.size() << ", 'M' = " << M
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (B.size() != unsigned(N * M))
	{
		std::stringstream message;
		message << "'B.size()' has to be equal to 'N' * 'M' ('B.size()' = " << B.size() << ", 'N' = " << N
		        << ", 'M' = " << M << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	real_transpose(M, N, A.data(), B.data());
}

template <typename T>
inline void real_transpose(const int M, const int N,
                           const T *A,
                                 T *B)
{
	for (auto i = 0; i < M; i++)
		for (auto j = 0; j < N; j++)
			B[j*M+i] =  A[i*N+j];
}

template <typename T, class AT>
inline void complex_transpose(const int M, const int N,
                              const std::vector<T,AT> &A,
                                    std::vector<T,AT> &B)
{
	if (A.size() != unsigned(M * N * 2))
	{
		std::stringstream message;
		message << "'A.size()' has to be equal to 'M' * 'N' * 2 ('A.size()' = " << A.size() << ", 'M' = " << M
		        << ", 'N' = " << N << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	if (B.size() != unsigned(N * M * 2))
	{
		std::stringstream message;
		message << "'B.size()' has to be equal to 'N' * 'M' * 2 ('B.size()' = " << B.size() << ", 'N' = " << N
		        << ", 'M' = " << M << ").";
		throw length_error(__FILE__, __LINE__, __func__, message.str());
	}

	complex_transpose(M, N, A.data(), B.data());
}

template <typename T>
inline void complex_transpose(const int M, const int N,
                              const T *A,
                                    T *B)
{
	const T* A_real = A;
	const T* A_imag = A + M * N;
	      T* B_real = B;
	      T* B_imag = B + M * N;

	for (auto i = 0; i < M; i++)
	{
		for (auto j = 0; j < N; j++)
		{
			B_real[j*M+i] =  A_real[i*N+j];
			B_imag[j*M+i] = -A_imag[i*N+j];
		}
	}
}
}
}
