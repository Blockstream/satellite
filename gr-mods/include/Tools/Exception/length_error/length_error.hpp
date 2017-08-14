#ifndef LENGTH_ERROR_HPP_
#define LENGTH_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class length_error : public exception
{
	static const std::string default_message;

public:
	length_error() throw();

	length_error(const std::string message) throw();

	length_error(const std::string filename,
	             const int line_num,
	             const std::string funcname = "",
	             const std::string message = "") throw();

	virtual ~length_error() throw();
};
}
}

#endif /* LENGTH_ERROR_HPP_ */
