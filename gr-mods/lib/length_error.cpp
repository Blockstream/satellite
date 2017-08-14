#include "Tools/Exception/length_error/length_error.hpp"

using namespace aff3ct::tools;

const std::string length_error::default_message = "Length error.";

length_error
::length_error() throw()
: exception()
{
}

length_error
::length_error(const std::string message) throw()
: exception(message.empty() ? default_message : message)
{
}

length_error
::length_error(const std::string filename,
               const int line_num,
               const std::string funcname,
               const std::string message) throw()
: exception(filename, line_num, funcname, message.empty() ? default_message : message)
{
}

length_error
::~length_error() throw()
{
}
