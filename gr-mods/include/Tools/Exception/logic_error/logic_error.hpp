#ifndef LOGIC_ERROR_HPP_
#define LOGIC_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class logic_error : public exception
{
	static const std::string default_message;

public:
	logic_error() throw();

	logic_error(const std::string message) throw();

	logic_error(const std::string filename,
	            const int line_num,
	            const std::string funcname = "",
	            const std::string message = "") throw();

	virtual ~logic_error() throw();
};
}
}

#endif /* LOGIC_ERROR_HPP_ */
