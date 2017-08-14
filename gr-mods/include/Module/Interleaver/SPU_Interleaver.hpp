#ifndef SPU_INTERLEAVER_HPP_
#define SPU_INTERLEAVER_HPP_

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
template <typename T = int>
class SPU_Interleaver : public Interleaver_i<T>
{
private:
	static starpu_codelet spu_cl_interleave;
	static starpu_codelet spu_cl_deinterleave;

public:
	SPU_Interleaver(const int size, const bool uniform = false, const int n_frames = 1,
	                const std::string name = "SPU_Interleaver")
	: Interleaver_i<T>(size, uniform, n_frames, name) {}

	virtual ~SPU_Interleaver() {}

	static inline starpu_task* spu_task_interleave(SPU_Interleaver<T> *interleaver, starpu_data_handle_t &in_data,
	                                                                                starpu_data_handle_t &out_data)
	{
		auto *task = starpu_task_create();

		task->name        = "itl::interleave";
		task->cl          = &SPU_Interleaver<T>::spu_cl_interleave;
		task->cl_arg      = (void*)(interleaver);
		task->cl_arg_size = sizeof(*interleaver);
		task->handles[0]  = in_data;
		task->handles[1]  = out_data;

		return task;
	}

	static inline starpu_task* spu_task_deinterleave(SPU_Interleaver<T> *interleaver, starpu_data_handle_t &in_data,
	                                                                                  starpu_data_handle_t &out_data)
	{
		auto task = starpu_task_create();

		task->name        = "itl::deinterleave";
		task->cl          = &SPU_Interleaver<T>::spu_cl_deinterleave;
		task->cl_arg      = (void*)(interleaver);
		task->cl_arg_size = sizeof(*interleaver);
		task->handles[0]  = in_data;
		task->handles[1]  = out_data;

		return task;
	}

private:
	static starpu_codelet spu_init_cl_interleave()
	{
		starpu_codelet cl;

		cl.type              = STARPU_SEQ;
		cl.cpu_funcs     [0] = SPU_Interleaver<T>::spu_kernel_interleave;
		cl.cpu_funcs_name[0] = "itl::interleave::cpu";
		cl.nbuffers          = 2;
		cl.modes         [0] = STARPU_R;
		cl.modes         [1] = STARPU_W;

		return cl;
	}

	static starpu_codelet spu_init_cl_deinterleave()
	{
		starpu_codelet cl;

		cl.type              = STARPU_SEQ;
		cl.cpu_funcs     [0] = SPU_Interleaver<T>::spu_kernel_deinterleave;
		cl.cpu_funcs_name[0] = "itl::interleave::cpu";
		cl.nbuffers          = 2;
		cl.modes         [0] = STARPU_R;
		cl.modes         [1] = STARPU_W;

		return cl;
	}

	static void spu_kernel_interleave(void *buffers[], void *cl_arg)
	{
		auto itl = static_cast<SPU_Interleaver<T>*>(cl_arg);

		switch (STARPU_VARIABLE_GET_ELEMSIZE(buffers[0]))
		{
			case 1: _spu_kernel_interleave<int8_t >(buffers, itl); break;
			case 2: _spu_kernel_interleave<int16_t>(buffers, itl); break;
			case 4: _spu_kernel_interleave<int32_t>(buffers, itl); break;
			case 8: _spu_kernel_interleave<int64_t>(buffers, itl); break;
			default:
				std::cerr << "(EE) Unrecognized type of data, exiting." << std::endl;
				std::exit(-1);
				break;
		}
	}

	static void spu_kernel_deinterleave(void *buffers[], void *cl_arg)
	{
		auto itl = static_cast<SPU_Interleaver<T>*>(cl_arg);

		switch (STARPU_VARIABLE_GET_ELEMSIZE(buffers[0]))
		{
			case 1: _spu_kernel_deinterleave<int8_t >(buffers, itl); break;
			case 2: _spu_kernel_deinterleave<int16_t>(buffers, itl); break;
			case 4: _spu_kernel_deinterleave<int32_t>(buffers, itl); break;
			case 8: _spu_kernel_deinterleave<int64_t>(buffers, itl); break;
			default:
				std::cerr << "(EE) Unrecognized type of data, exiting." << std::endl;
				std::exit(-1);
				break;
		}
	}

	template <typename D>
	static void _spu_kernel_interleave(void *buffers[],
	                                   SPU_Interleaver<T>* interleaver)
	{
		auto task = starpu_task_get_current();

		auto udata0 = starpu_data_get_user_data(task->handles[0]); assert(udata0);
		auto udata1 = starpu_data_get_user_data(task->handles[1]); assert(udata1);

		auto natural_vec     = static_cast<mipp::vector<D>*>(udata0);
		auto interleaved_vec = static_cast<mipp::vector<D>*>(udata1);

		interleaver->interleave(*natural_vec, *interleaved_vec);
	}

	template <typename D>
	static void _spu_kernel_deinterleave(void *buffers[],
	                                     SPU_Interleaver<T>* interleaver)
	{
		auto task = starpu_task_get_current();

		auto udata0 = starpu_data_get_user_data(task->handles[0]); assert(udata0);
		auto udata1 = starpu_data_get_user_data(task->handles[1]); assert(udata1);

		auto interleaved_vec = static_cast<mipp::vector<D>*>(udata0);
		auto natural_vec     = static_cast<mipp::vector<D>*>(udata1);

		interleaver->deinterleave(*interleaved_vec, *natural_vec);
	}
};

template <typename T>
starpu_codelet SPU_Interleaver<T>::spu_cl_interleave = SPU_Interleaver<T>::spu_init_cl_interleave();

template <typename T>
starpu_codelet SPU_Interleaver<T>::spu_cl_deinterleave = SPU_Interleaver<T>::spu_init_cl_deinterleave();

template <typename T>
using Interleaver = SPU_Interleaver<T>;
}
}
#else
namespace aff3ct
{
namespace module
{
template <typename T = int>
using Interleaver = Interleaver_i<T>;
}
}
#endif

#endif /* SPU_INTERLEAVER_HPP_ */
