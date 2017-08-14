#include <vector>
#include <iostream>

#include "bash_tools.h"

bool aff3ct::tools::enable_bash_tools = true;

// source : http://misc.flogisoft.com/bash/tip_colors_and_formatting

std::vector<std::vector<std::string>> Style_table = {
	// BASIC   BLINK   BOLD    DIM HIDDEN INVERT ITALIC UNDERL
	{    "0",    "5",   "1",   "2",   "8",   "7",   "3",   "4"}, // SET
	{    "0",   "25",  "21",  "22",  "28",  "27",  "23",  "24"}  // CLEAR
	};

std::vector<std::vector<std::string>> Color_table_fg = {
	//DEFAULT  BLACK   BLUE   CYAN    GRAY  GREEN MAGENT  ORANGE     RED  WHITE YELLOW
	{   "256",   "0",  "33",  "39",  "244",   "2",   "5",  "208",    "1",  "256",  "220"}, // NORMAL
	{   "256",   "0",  "21",  "51",  "251",  "10",  "13",  "214",  "196",  "256",  "226"}  // INTENSE
	};

std::vector<std::vector<std::string>> Color_table_bg = {
	//DEFAULT  BLACK   BLUE   CYAN    GRAY  GREEN MAGENT  ORANGE    RED  WHITE YELLOW
	{    "0",    "0",  "33",  "39",  "244",   "2",   "5",  "208",    "1",  "256",  "220"}, // NORMAL
	{    "0",    "0",  "21",  "51",  "251",  "10",  "13",  "214",  "196",  "256",  "226"}  // INTENSE
	};

std::string reset_command = "\e[0m";

std::string style_command_head  = "\e[";
std::string style_command_queue = "m";

std::string fg_color_command_head  = "\e[38;5;";
std::string fg_color_command_queue = "m";
std::string fg_color_reset_command = "\e[39m";

std::string bg_color_command_head  = "\e[48;5;";
std::string bg_color_command_queue = "m";
std::string bg_color_reset_command = "\e[49m";

std::string aff3ct::tools::format(std::string str, Format f)
{
#ifndef ENABLE_COOL_BASH
	return str;
#else

	if (enable_bash_tools)
	{
		constexpr Format style_mask = (((Format)1 << 31) + (((Format)1 << 31) -1)) ^ (((Format)1 << 20) -1);
		str = style(str, (Style)(f & style_mask));

		constexpr Format bg_intensity_mask = (((Format)1 << 20) -1) ^ (((Format)1 << 18) -1);
		constexpr Format bg_color_mask     = (((Format)1 << 18) -1) ^ (((Format)1 << 10) -1);
		str = bg_color(str, (BG::Color)(f & bg_color_mask), (BG::Intensity)(f & bg_intensity_mask));

		constexpr Format fg_intensity_mask = (((Format)1 << 10) -1) ^ (((Format)1 << 8) -1);
		constexpr Format fg_color_mask     = (((Format)1 <<  8) -1);
		str = fg_color(str, (FG::Color)(f & fg_color_mask), (FG::Intensity)(f & fg_intensity_mask));
	}

	return str;

#endif
}

std::string aff3ct::tools::style(std::string str, Style s)
{
#ifndef ENABLE_COOL_BASH
	return str;
#else

	if (enable_bash_tools)
	{
		std::string head, queue;
		for (unsigned i = 0; i < 12; ++i)
		{
			if(s & ((Format)1 << (i+20)))
			{
				head  += style_command_head + Style_table.at(0).at(i+1) + style_command_queue;
				queue += style_command_head + Style_table.at(1).at(i+1) + style_command_queue;
			}
		}
		return head + str + queue;
	}
	else
		return str;

#endif
}

std::string aff3ct::tools::fg_color(std::string str, FG::Color c, FG::Intensity i)
{
#ifndef ENABLE_COOL_BASH
	return str;
#else

	if (enable_bash_tools && c != 0)
	{
		std::string head  = fg_color_command_head + Color_table_fg.at(i >> 8).at(c >> 0) + fg_color_command_queue;
		std::string queue = fg_color_reset_command;
		return head + str + queue;
	}
	else
		return str;

#endif
}

std::string aff3ct::tools::bg_color(std::string str, BG::Color c, BG::Intensity i)
{
#ifndef ENABLE_COOL_BASH
	return str;
#else

	if (enable_bash_tools && c != 0)
	{
		std::string head  = bg_color_command_head + Color_table_bg.at(i >> 18).at(c >> 10) + bg_color_command_queue;
		std::string queue = bg_color_reset_command;
		return head + str + queue;
	}
	else
		return str;

#endif
}

std::string aff3ct::tools::default_style(std::string str)
{
#ifndef ENABLE_COOL_BASH
	return str;
#else
	if (enable_bash_tools)
		return reset_command + str;
	else
		return str;
#endif
}


std::string aff3ct::tools::format_error(std::string str)
{
	return format("(EE) ", FG::Color::RED | FG::Intensity::INTENSE | Style::BOLD) + str;
}

std::string aff3ct::tools::format_critical_error(std::string str)
{
	return format("(EE) ", FG::Color::WHITE | FG::Intensity::NORMAL | BG::Color::RED | BG::Intensity::INTENSE) + str;
}

std::string aff3ct::tools::format_warning(std::string str)
{
	return format("(WW) ", FG::Color::ORANGE | FG::Intensity::NORMAL | Style::BOLD) + str;
}

std::string aff3ct::tools::format_critical_warning(std::string str)
{
	return format("(WW) ", FG::Color::WHITE | FG::Intensity::NORMAL | BG::Color::ORANGE | BG::Intensity::INTENSE) + str;
}

std::string aff3ct::tools::format_info(std::string str)
{
	return format("(II) ", FG::Color::BLUE | FG::Intensity::NORMAL | Style::BOLD) + str;
}

std::string aff3ct::tools::format_critical_info(std::string str)
{
	return format("(II) ", FG::Color::WHITE | FG::Intensity::NORMAL | BG::Color::BLUE | BG::Intensity::INTENSE) + str;
}

std::string aff3ct::tools::format_positive_info(std::string str)
{
	return format("(II) ", FG::Color::GREEN | FG::Intensity::NORMAL) + str;
}


std::string aff3ct::tools::apply_on_each_line(const std::string& str, format_function fptr)
{
	std::string formated;

	size_t pos = 0, old_pos = 0;
	while((pos = str.find('\n', old_pos)) != str.npos)
	{
		formated += fptr(str.substr(old_pos, pos-old_pos)) + "\n";

		old_pos = pos+1;
	}

	formated += fptr(str.substr(old_pos, pos-old_pos));

	return formated;
}

