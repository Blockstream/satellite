#include "Tools/Exception/unimplemented_error/unimplemented_error.hpp"

using namespace aff3ct::tools;

const std::string unimplemented_error::default_message = "Unimplemented function or method.";

unimplemented_error
::unimplemented_error() throw()
: exception()
{
}

unimplemented_error
::unimplemented_error(const std::string message) throw()
: exception(message.empty() ? default_message : message)
{
}

unimplemented_error
::unimplemented_error(const std::string filename,
                      const int line_num,
                      const std::string funcname,
                      const std::string message) throw()
: exception(filename, line_num, funcname, message.empty() ? default_message : message)
{
}

unimplemented_error
::~unimplemented_error() throw()
{
}
