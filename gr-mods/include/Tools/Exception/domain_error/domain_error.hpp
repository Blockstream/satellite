#ifndef DOMAIN_ERROR_HPP_
#define DOMAIN_ERROR_HPP_

#include "../exception.hpp"

namespace aff3ct
{
namespace tools
{
class domain_error : public exception
{
	static const std::string default_message;

public:
	domain_error() throw();

	domain_error(const std::string message) throw();

	domain_error(const std::string filename,
	             const int line_num,
	             const std::string funcname = "",
	             const std::string message = "") throw();

	virtual ~domain_error() throw();
};
}
}

#endif /* DOMAIN_ERROR_HPP_ */
