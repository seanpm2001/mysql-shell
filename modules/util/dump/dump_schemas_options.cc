/*
 * Copyright (c) 2020, Oracle and/or its affiliates. All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License, version 2.0,
 * as published by the Free Software Foundation.
 *
 * This program is also distributed with certain software (including
 * but not limited to OpenSSL) that is licensed under separate terms, as
 * designated in a particular file or component or in included license
 * documentation.  The authors of MySQL hereby grant you an additional
 * permission to link the program and your derivative works with the
 * separately licensed software that they have included with MySQL.
 * This program is distributed in the hope that it will be useful,  but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
 * the GNU General Public License, version 2.0, for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include "modules/util/dump/dump_schemas_options.h"

#include <utility>

#include "mysqlshdk/libs/utils/utils_general.h"

namespace mysqlsh {
namespace dump {

Dump_schemas_options::Dump_schemas_options(
    const std::vector<std::string> &schemas, const std::string &output_url)
    : Ddl_dumper_options(output_url),
      m_schemas(schemas.begin(), schemas.end()) {}

Dump_schemas_options::Dump_schemas_options(const std::string &output_url)
    : Ddl_dumper_options(output_url) {}

void Dump_schemas_options::unpack_options(shcore::Option_unpacker *unpacker) {
  Ddl_dumper_options::unpack_options(unpacker);

  std::vector<std::string> tables;
  std::vector<std::string> compatibility_options;
  bool mds = false;

  unpacker->optional("excludeTables", &tables)
      .optional("events", &m_dump_events)
      .optional("routines", &m_dump_routines)
      .optional("ocimds", &mds)
      .optional("compatibility", &compatibility_options);

  std::string schema;
  std::string table;

  for (const auto &t : tables) {
    try {
      shcore::split_schema_and_table(t, &schema, &table);
    } catch (const std::runtime_error &e) {
      throw std::invalid_argument("Failed to parse table to be excluded '" + t +
                                  "': " + e.what());
    }

    if (schema.empty()) {
      throw std::invalid_argument(
          "The table to be excluded must be in the following form: "
          "schema.table, with optional backtick quotes, wrong value: '" +
          t + "'.");
    }

    m_excluded_tables[schema].emplace(std::move(table));
  }

  if (mds) {
    set_mds_compatibility(mysqlshdk::utils::Version(MYSH_VERSION));
  }

  for (const auto &option : compatibility_options) {
    m_compatibility_options |= to_compatibility_option(option);
  }
}

void Dump_schemas_options::validate_options() const {
  Ddl_dumper_options::validate_options();

  if (m_schemas.empty()) {
    throw std::invalid_argument(
        "The 'schemas' parameter cannot be an empty list.");
  }
}

}  // namespace dump
}  // namespace mysqlsh
