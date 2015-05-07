/*
 * Copyright (c) 2014, Oracle and/or its affiliates. All rights reserved.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; version 2 of the
 * License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301  USA
 */

#include "shellcore/shell_jscript.h"
#include "shellcore/jscript_context.h"

using namespace shcore;


Shell_javascript::Shell_javascript(Shell_core *shcore)
: Shell_language(shcore)
{
  _js = boost::shared_ptr<JScript_context>(new JScript_context(shcore->registry(), shcore->lang_delegate()));
}


Value Shell_javascript::handle_input(std::string &code, Interactive_input_state &state, bool interactive)
{
  // Undefined to be returned in case of errors
  Value result;

  if (interactive)
    result = _js->execute_interactive(code);
  else
  {
    try
    {
      boost::system::error_code err;

      result = _js->execute(code, err, _owner->get_input_source());

      if (err)
      {
        _owner->print_error(err.message());
      }
    }
    catch (Exception &exc)
    {
      // This exception was already printed in JS
      // and the correct return_value of undefined is set
    }
  }

  _last_handled = code;

  state = Input_ok;

  return result;
}


std::string Shell_javascript::prompt()
{
  return "mysql-js> ";
}


void Shell_javascript::set_global(const std::string &name, const Value &value)
{
  _js->set_global(name, value);
}

