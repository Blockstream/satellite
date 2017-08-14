#include <algorithm>
#include <iostream>
#include <utility>
#include <vector>
#include <map>

#include "Factory.hpp"

bool aff3ct::factory::exist(const arg_val_map &vals, const std::vector<std::string> &tags)
{
	return (vals.find(tags) != vals.end());
}

void aff3ct::factory::Header::print_parameters(std::string grp_name, params_list params, int max_n_chars,
                                               std::ostream& stream)
{
	stream << "# * " << tools::style(tools::style(grp_name, tools::Style::BOLD), tools::Style::UNDERLINED) << " ";
	for (auto i = 0; i < 46 - (int)grp_name.length(); i++) std::cout << "-";
	stream << std::endl;

	for (auto i = 0; i < (int)params.size(); i++)
	{
		stream << "#    ** " << tools::style(params[i].first, tools::Style::BOLD);
		for (auto j = 0; j < max_n_chars - (int)params[i].first.length(); j++) stream << " ";
		stream << " = " << params[i].second << std::endl;
	}
}

void aff3ct::factory::Header::compute_max_n_chars(const params_list& params, int& max_n_chars)
{
	for (unsigned i = 0; i < params.size(); i++)
		max_n_chars = std::max(max_n_chars, (int)params[i].first.length());
}
