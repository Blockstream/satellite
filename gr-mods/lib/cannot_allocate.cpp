#include "cannot_allocate.hpp"

using namespace aff3ct::tools;

const std::string cannot_allocate::default_message = "Cannot allocate the object.";

cannot_allocate
::cannot_allocate() throw()
: exception()
{
}

cannot_allocate
::cannot_allocate(const std::string message) throw()
: exception(message.empty() ? default_message : message)
{
}

cannot_allocate
::cannot_allocate(const std::string filename,
                  const int line_num,
                  const std::string funcname,
                  const std::string message) throw()
: exception(filename, line_num, funcname, message.empty() ? default_message : message)
{
}

cannot_allocate
::~cannot_allocate() throw()
{
}
