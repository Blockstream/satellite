#ifndef SPU_DECODER_SISO_HPP_
#define SPU_DECODER_SISO_HPP_

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
template <typename R = float>
class SPU_Decoder_SISO : public Decoder_SISO_i<R>
{
private:
	static starpu_codelet spu_cl_decode_siso;

public:
	SPU_Decoder_SISO(const int K, const int N, const int n_frames, const int simd_inter_frame_level = 1,
	                 const std::string name = "SPU_Decoder_SISO")
	: Decoder_SISO_i<R>(K, N, n_frames, simd_inter_frame_level, name) {}

	virtual ~SPU_Decoder_SISO() {}

	static inline starpu_task* spu_task_decode_siso(SPU_Decoder_SISO<R> *siso, starpu_data_handle_t &in_data,
	                                                                           starpu_data_handle_t &out_data)
	{
		auto task = starpu_task_create();

		task->name        = "dec::decode_siso";
		task->cl          = &SPU_Decoder_SISO<R>::spu_cl_decode_siso;
		task->cl_arg      = (void*)(siso);
		task->cl_arg_size = sizeof(*siso);
		task->handles[0]  = in_data;
		task->handles[1]  = out_data;

		return task;
	}

private:
	static starpu_codelet spu_init_cl_decode_siso()
	{
		starpu_codelet cl;

		cl.type              = STARPU_SEQ;
		cl.cpu_funcs     [0] = SPU_Decoder_SISO<R>::spu_kernel_decode_siso;
		cl.cpu_funcs_name[0] = "dec::decode_siso::cpu";
		cl.nbuffers          = 2;
		cl.modes         [0] = STARPU_R;
		cl.modes         [1] = STARPU_W;

		return cl;
	}

	static void spu_kernel_decode_siso(void *buffers[], void *cl_arg)
	{
		auto decoder = static_cast<SPU_Decoder_SISO<R>*>(cl_arg);

		auto task = starpu_task_get_current();

		auto udata0 = starpu_data_get_user_data(task->handles[0]); assert(udata0);
		auto udata1 = starpu_data_get_user_data(task->handles[1]); assert(udata1);

		auto Y_N1 = static_cast<mipp::vector<R>*>(udata0);
		auto Y_N2 = static_cast<mipp::vector<R>*>(udata1);

		decoder->decode_siso(*Y_N1, *Y_N2);
	}
};

template <typename R>
starpu_codelet SPU_Decoder_SISO<R>::spu_cl_decode_siso = SPU_Decoder_SISO<R>::spu_init_cl_decode_siso();

template <typename R>
using Decoder_SISO = SPU_Decoder_SISO<R>;
}
}
#else
namespace aff3ct
{
namespace module
{
template <typename R>
using Decoder_SISO = Decoder_SISO_i<R>;
}
}
#endif

#endif /* SPU_DECODER_SISO_HPP_ */
