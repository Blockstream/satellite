#ifndef CANNOT_ALLOCATE_HPP_
#define CANNOT_ALLOCATE_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class cannot_allocate : public exception
{
	static const std::string default_message;

public:
	cannot_allocate() throw();

	cannot_allocate(const std::string message) throw();

	cannot_allocate(const std::string filename,
	                const int line_num,
	                const std::string funcname = "",
	                const std::string message = "") throw();

	virtual ~cannot_allocate() throw();
};
}
}

#endif /* CANNOT_ALLOCATE_HPP_ */
