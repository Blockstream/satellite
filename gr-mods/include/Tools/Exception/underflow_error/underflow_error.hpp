#ifndef UNDERFLOW_ERROR_HPP_
#define UNDERFLOW_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class underflow_error : public exception
{
	static const std::string default_message;

public:
	underflow_error() throw();

	underflow_error(const std::string message) throw();

	underflow_error(const std::string filename,
	                const int line_num,
	                const std::string funcname = "",
	                const std::string message = "") throw();

	virtual ~underflow_error() throw();
};
}
}

#endif /* UNDERFLOW_ERROR_HPP_ */
