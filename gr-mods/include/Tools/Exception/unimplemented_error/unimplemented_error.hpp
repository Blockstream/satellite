#ifndef UNIMPLEMENTED_ERROR_HPP_
#define UNIMPLEMENTED_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class unimplemented_error : public exception
{
	static const std::string default_message;

public:
	unimplemented_error() throw();

	unimplemented_error(const std::string message) throw();

	unimplemented_error(const std::string filename,
	                    const int line_num,
	                    const std::string funcname = "",
	                    const std::string message = "") throw();

	virtual ~unimplemented_error() throw();
};
}
}

#endif /* UNIMPLEMENTED_ERROR_HPP_ */
