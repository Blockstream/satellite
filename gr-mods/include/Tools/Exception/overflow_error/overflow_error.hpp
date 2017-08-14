#ifndef OVERFLOW_ERROR_HPP_
#define OVERFLOW_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class overflow_error : public exception
{
	static const std::string default_message;

public:
	overflow_error() throw();

	overflow_error(const std::string message) throw();

	overflow_error(const std::string filename,
	               const int line_num,
	               const std::string funcname = "",
	               const std::string message = "") throw();

	virtual ~overflow_error() throw();
};
}
}

#endif /* OVERFLOW_ERROR_HPP_ */
