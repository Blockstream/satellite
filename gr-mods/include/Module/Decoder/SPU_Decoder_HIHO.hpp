#ifndef SPU_DECODER_HIHO_HPP_
#define SPU_DECODER_HIHO_HPP_

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
template <typename B = int>
class SPU_Decoder_HIHO : public Decoder_HIHO_i<B>
{
private:
	static starpu_codelet spu_cl_decode_hiho;

public:
	SPU_Decoder_HIHO(const int K, const int N, const int n_frames = 1, const int simd_inter_frame_level = 1,
	                 const std::string name = "SPU_Decoder_HIHO")
	: Decoder_HIHO_i<B>(K, N, n_frames, simd_inter_frame_level, name) {}

	virtual ~SPU_Decoder_HIHO() {}

	static inline starpu_task* spu_task_decode_hiho(SPU_Decoder_HIHO<B> *decoder, starpu_data_handle_t &in_data,
	                                                                              starpu_data_handle_t &out_data)
	{
		auto task = starpu_task_create();

		task->name        = "dec::decode_hiho";
		task->cl          = &SPU_Decoder_HIHO<B>::spu_cl_decode_hiho;
		task->cl_arg      = (void*)(decoder);
		task->cl_arg_size = sizeof(*decoder);
		task->handles[0]  = in_data;
		task->handles[1]  = out_data;

		return task;
	}

private:
	static starpu_codelet spu_init_cl_decode_hiho()
	{
		starpu_codelet cl;

		cl.type              = STARPU_SEQ;
		cl.cpu_funcs     [0] = SPU_Decoder_HIHO<B>::spu_kernel_decode_hiho;
		cl.cpu_funcs_name[0] = "dec::decode_hiho::cpu";
		cl.nbuffers          = 2;
		cl.modes         [0] = STARPU_R;
		cl.modes         [1] = STARPU_W;

		return cl;
	}

	static void spu_kernel_decode_hiho(void *buffers[], void *cl_arg)
	{
		auto decoder = static_cast<SPU_Decoder_HIHO<B>*>(cl_arg);

		auto task = starpu_task_get_current();

		auto udata0 = starpu_data_get_user_data(task->handles[0]); assert(udata0);
		auto udata1 = starpu_data_get_user_data(task->handles[1]); assert(udata1);

		auto Y_N = static_cast<mipp::vector<B>*>(udata0);
		auto V_K = static_cast<mipp::vector<B>*>(udata1);

		decoder->decode_hiho(*Y_N, *V_K);
	}
};

template <typename B>
starpu_codelet SPU_Decoder_HIHO<B>::spu_cl_decode_hiho = SPU_Decoder_HIHO<B>::spu_init_cl_decode_hiho();

template <typename B>
using Decoder_HIHO = SPU_Decoder_HIHO<B>;
}
}
#else
namespace aff3ct
{
namespace module
{
template <typename B = int>
using Decoder_HIHO = Decoder_HIHO_i<B>;
}
}
#endif

#endif /* SPU_DECODER_HIHO_HPP_ */
