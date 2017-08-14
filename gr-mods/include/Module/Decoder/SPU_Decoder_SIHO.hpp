#ifndef SPU_DECODER_SIHO_HPP_
#define SPU_DECODER_SIHO_HPP_

#ifdef STARPU
#include <vector>
#include <string>
#include <cassert>
#include <mipp/mipp.h>
#include <starpu.h>

namespace aff3ct
{
namespace module
{
template <typename B = int, typename R = float>
class SPU_Decoder_SIHO : public Decoder_SIHO_i<B,R>
{
private:
	static starpu_codelet spu_cl_decode_siho;

public:
	SPU_Decoder_SIHO(const int K, const int N, const int n_frames = 1, const int simd_inter_frame_level = 1,
	                 const std::string name = "SPU_Decoder_SIHO")
	: Decoder_SIHO_i<B,R>(K, N, n_frames, simd_inter_frame_level, name) {}

	virtual ~SPU_Decoder_SIHO() {}

	static inline starpu_task* spu_task_decode_siho(SPU_Decoder_SIHO<B,R> *decoder, starpu_data_handle_t &in_data,
	                                                                                starpu_data_handle_t &out_data)
	{
		auto task = starpu_task_create();

		task->name        = "dec::decode_siho";
		task->cl          = &SPU_Decoder_SIHO<B,R>::spu_cl_decode_siho;
		task->cl_arg      = (void*)(decoder);
		task->cl_arg_size = sizeof(*decoder);
		task->handles[0]  = in_data;
		task->handles[1]  = out_data;

		return task;
	}

private:
	static starpu_codelet spu_init_cl_decode_siho()
	{
		starpu_codelet cl;

		cl.type              = STARPU_SEQ;
		cl.cpu_funcs     [0] = SPU_Decoder_SIHO<B,R>::spu_kernel_decode_siho;
		cl.cpu_funcs_name[0] = "dec::decode_siho::cpu";
		cl.nbuffers          = 2;
		cl.modes         [0] = STARPU_R;
		cl.modes         [1] = STARPU_W;

		return cl;
	}

	static void spu_kernel_decode_siho(void *buffers[], void *cl_arg)
	{
		auto decoder = static_cast<SPU_Decoder_SIHO<B,R>*>(cl_arg);

		auto task = starpu_task_get_current();

		auto udata0 = starpu_data_get_user_data(task->handles[0]); assert(udata0);
		auto udata1 = starpu_data_get_user_data(task->handles[1]); assert(udata1);

		auto Y_N = static_cast<mipp::vector<R>*>(udata0);
		auto V_K = static_cast<mipp::vector<B>*>(udata1);

		decoder->decode_siho(*Y_N, *V_K);
	}
};

template <typename B, typename R>
starpu_codelet SPU_Decoder_SIHO<B,R>::spu_cl_decode_siho = SPU_Decoder_SIHO<B,R>::spu_init_cl_decode_siho();

template <typename B, typename R>
using Decoder_SIHO = SPU_Decoder_SIHO<B,R>;
}
}
#else
namespace aff3ct
{
namespace module
{
template <typename B = int, typename R = float>
using Decoder_SIHO = Decoder_SIHO_i<B,R>;
}
}
#endif

#endif /* DECODER_HPP_ */
