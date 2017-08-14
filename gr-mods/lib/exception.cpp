#if (defined(__GNUC__) || defined(__clang__) || defined(__llvm__)) && (defined(__linux__) || defined(__linux) || defined(__APPLE__))
#include <execinfo.h>
#include <unistd.h>
#include <cstdlib>
#endif

#include "Tools/Exception/exception.hpp"

#define ENABLE_BACK_TRACE

using namespace aff3ct::tools;

exception
::exception() throw()
{
}

exception
::exception(const std::string message) throw()
: message(message)
{
#if defined(ENABLE_BACK_TRACE)
	this->message += get_back_trace();
#endif
}

exception
::exception(const std::string filename,
            const int line_num,
            const std::string funcname,
            const std::string message) throw()
{
	if (!filename.empty())
		this->message += "In the '" + filename + "' file";
	if (line_num >= 0)
		this->message += " at line " + std::to_string(line_num);
	if (!funcname.empty())
		this->message += " ('" + funcname + "' function)";
	this->message += ": ";
	this->message += "\"" + message + "\"";

#if defined(ENABLE_BACK_TRACE)
	this->message += get_back_trace();
#endif
}

exception
::~exception() throw()
{
}

const char* exception
::what() const throw()
{
	return message.c_str();
}

std::string exception
::get_back_trace()
{
	std::string bt_str;
#if (defined(__GNUC__) || defined(__clang__) || defined(__llvm__)) && (defined(__linux__) || defined(__linux) || defined(__APPLE__))
	const int bt_max_depth = 32;
	void *bt_array[bt_max_depth];

	size_t size = backtrace(bt_array, bt_max_depth);
	char** bt_symbs = backtrace_symbols(bt_array, size);

	bt_str += "\nBacktrace:";
	for (size_t i = 0; i < size; i++)
		bt_str += "\n" + std::string(bt_symbs[i]);
	free(bt_symbs);
#endif

	return bt_str;
}
