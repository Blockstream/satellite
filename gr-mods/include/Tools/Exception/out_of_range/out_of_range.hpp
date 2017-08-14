#ifndef OUT_OF_RANGE_HPP_
#define OUT_OF_RANGE_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class out_of_range : public exception
{
	static const std::string default_message;

public:
	out_of_range() throw();

	out_of_range(const std::string message) throw();

	out_of_range(const std::string filename,
	             const int line_num,
	             const std::string funcname = "",
	             const std::string message = "") throw();

	virtual ~out_of_range() throw();
};
}
}

#endif /* OUT_OF_RANGE_HPP_ */
