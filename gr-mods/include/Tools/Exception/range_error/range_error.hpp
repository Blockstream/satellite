#ifndef RANGE_ERROR_HPP_
#define RANGE_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class range_error : public exception
{
	static const std::string default_message;

public:
	range_error() throw();

	range_error(const std::string message) throw();

	range_error(const std::string filename,
	            const int line_num,
	            const std::string funcname = "",
	            const std::string message = "") throw();

	virtual ~range_error() throw();
};
}
}

#endif /* RANGE_ERROR_HPP_ */
