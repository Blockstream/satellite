#include "Tools/Exception/runtime_error/runtime_error.hpp"

using namespace aff3ct::tools;

const std::string runtime_error::default_message = "Runtile error.";

runtime_error
::runtime_error() throw()
: exception()
{
}

runtime_error
::runtime_error(const std::string message) throw()
: exception(message.empty() ? default_message : message)
{
}

runtime_error
::runtime_error(const std::string filename,
                const int line_num,
                const std::string funcname,
                const std::string message) throw()
: exception(filename, line_num, funcname, message.empty() ? default_message : message)
{
}

runtime_error
::~runtime_error() throw()
{
}
