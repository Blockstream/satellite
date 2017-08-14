#ifndef INVALID_ARGUMENT_HPP_
#define INVALID_ARGUMENT_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class invalid_argument : public exception
{
	static const std::string default_message;

public:
	invalid_argument() throw();

	invalid_argument(const std::string message) throw();

	invalid_argument(const std::string filename,
	                 const int line_num,
	                 const std::string funcname = "",
	                 const std::string message = "") throw();

	virtual ~invalid_argument() throw();
};
}
}

#endif /* INVALID_ARGUMENT_HPP_ */
