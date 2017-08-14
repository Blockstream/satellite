#ifndef RUNTIME_ERROR_HPP_
#define RUNTIME_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class runtime_error : public exception
{
	static const std::string default_message;

public:
	runtime_error() throw();

	runtime_error(const std::string message) throw();

	runtime_error(const std::string filename,
	              const int line_num,
	              const std::string funcname = "",
	              const std::string message = "") throw();

	virtual ~runtime_error() throw();
};
}
}

#endif /* RUNTIME_ERROR_HPP_ */
