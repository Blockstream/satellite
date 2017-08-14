#include "Tools/Exception/invalid_argument/invalid_argument.hpp"

using namespace aff3ct::tools;

const std::string invalid_argument::default_message = "Given argument is invalid.";

invalid_argument
::invalid_argument() throw()
: exception()
{
}

invalid_argument
::invalid_argument(const std::string message) throw()
: exception(message.empty() ? default_message : message)
{
}

invalid_argument
::invalid_argument(const std::string filename,
                   const int line_num,
                   const std::string funcname,
                   const std::string message) throw()
: exception(filename, line_num, funcname, message.empty() ? default_message : message)
{
}

invalid_argument
::~invalid_argument() throw()
{
}
