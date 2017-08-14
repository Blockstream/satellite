#ifndef SPU_ENCODER_HPP_
#define SPU_ENCODER_HPP_

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
class SPU_Encoder : public Encoder_i<B>
{
private:
	static starpu_codelet spu_cl_encode;

public:
	SPU_Encoder(const int K, const int N, const int n_frames = 1, const std::string name = "SPU_Encoder")
	: Encoder_i<B>(K, N, n_frames, name) {}

	virtual ~SPU_Encoder() {}

	static inline starpu_task* spu_task_encode(SPU_Encoder<B> *encoder, starpu_data_handle_t &in_data,
	                                                                    starpu_data_handle_t &out_data)
	{
		auto task = starpu_task_create();

		task->name        = "enc::encode";
		task->cl          = &SPU_Encoder<B>::spu_cl_encode;
		task->cl_arg      = (void*)(encoder);
		task->cl_arg_size = sizeof(*encoder);
		task->handles[0]  = in_data;
		task->handles[1]  = out_data;

		return task;
	}

private:
	static starpu_codelet spu_init_cl_encode()
	{
		starpu_codelet cl;

		cl.type              = STARPU_SEQ;
		cl.cpu_funcs     [0] = SPU_Encoder<B>::spu_kernel_encode;
		cl.cpu_funcs_name[0] = "enc::encode::cpu";
		cl.nbuffers          = 2;
		cl.modes         [0] = STARPU_R;
		cl.modes         [1] = STARPU_W;

		return cl;
	}

	static void spu_kernel_encode(void *buffers[], void *cl_arg)
	{
		auto encoder = static_cast<SPU_Encoder<B>*>(cl_arg);

		auto task = starpu_task_get_current();

		auto udata0 = starpu_data_get_user_data(task->handles[0]); assert(udata0);
		auto udata1 = starpu_data_get_user_data(task->handles[1]); assert(udata1);

		auto U_K = static_cast<mipp::vector<B>*>(udata0);
		auto X_N = static_cast<mipp::vector<B>*>(udata1);

		encoder->encode(*U_K, *X_N);
	}
};

template <typename B>
starpu_codelet SPU_Encoder<B>::spu_cl_encode = SPU_Encoder<B>::spu_init_cl_encode();

template <typename B>
using Encoder = SPU_Encoder<B>;
}
}
#else
namespace aff3ct
{
namespace module
{
template <typename B = int>
using Encoder = Encoder_i<B>;
}
}
#endif

#endif /* SPU_ENCODER_HPP_ */
