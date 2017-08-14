#ifndef EXCEPTION_HPP_
#define EXCEPTION_HPP_

#include <exception>
#include <string>

namespace aff3ct
{
namespace tools
{
class exception : public std::exception
{
private:
	std::string message;

public:
	exception() throw();

	exception(const std::string message) throw();

	exception(const std::string filename,
	          const int line_num,
	          const std::string funcname,
	          const std::string message) throw();

	virtual ~exception() throw();

	virtual const char* what() const throw();

private:
	static std::string get_back_trace();
};
}
}

// include specific exceptions
#include "cannot_allocate/cannot_allocate.hpp"
#include "domain_error/domain_error.hpp"
#include "invalid_argument/invalid_argument.hpp"
#include "length_error/length_error.hpp"
#include "logic_error/logic_error.hpp"
#include "out_of_range/out_of_range.hpp"
#include "overflow_error/overflow_error.hpp"
#include "range_error/range_error.hpp"
#include "runtime_error/runtime_error.hpp"
#include "underflow_error/underflow_error.hpp"
#include "unimplemented_error/unimplemented_error.hpp"

#endif /* EXCEPTION_HPP_ */
