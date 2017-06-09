/*
 * Copyright (c) 2014, 2016, Oracle and/or its affiliates. All rights reserved.
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

#include "mod_mysqlx_resultset.h"
#include "base_constants.h"
#include "mysqlx.h"
#include "shellcore/common.h"
#include "shellcore/shell_core_options.h"
#include "shellcore/obj_date.h"
#include "utils/utils_time.h"
#include "mysqlxtest_utils.h"
#include "utils/utils_help.h"

using namespace std::placeholders;
using namespace shcore;
using namespace mysqlsh::mysqlx;

// -----------------------------------------------------------------------

// Documentation of BaseResult class
REGISTER_HELP(BASERESULT_BRIEF, "Base class for the different types of results returned by the server.");

BaseResult::BaseResult(std::shared_ptr< ::mysqlx::Result> result) :
_result(result), _execution_time(0) {
  add_property("executionTime", "getExecutionTime");
  add_property("warningCount", "getWarningCount");
  add_property("warnings", "getWarnings");
}

// Documentation of getWarnings function
REGISTER_HELP(BASERESULT_GETWARNINGS_BRIEF, "Retrieves the warnings generated by the executed operation.");
REGISTER_HELP(BASERESULT_GETWARNINGS_RETURNS, "@returns A list containing a warning object for each generated warning.");
REGISTER_HELP(BASERESULT_GETWARNINGS_DETAIL, "This is the same value than C API mysql_warning_count, see https://dev.mysql.com/doc/refman/5.7/en/mysql-warning-count.html");
REGISTER_HELP(BASERESULT_GETWARNINGS_DETAIL1, "Each warning object contains a key/value pair describing the information related to a specific warning.");
REGISTER_HELP(BASERESULT_GETWARNINGS_DETAIL2, "This information includes: Level, Code and Message.");

/**
* $(BASERESULT_GETWARNINGS_BRIEF)
*
* $(BASERESULT_GETWARNINGS_RETURNS)
*
* $(BASERESULT_GETWARNINGS_DETAIL)
*
* $(BASERESULT_GETWARNINGS_DETAIL1)
* $(BASERESULT_GETWARNINGS_DETAIL2)
*/
#if DOXYGEN_JS
List BaseResult::getWarnings() {};
#elif DOXYGEN_PY
list BaseResult::get_warnings() {};
#endif

shcore::Value BaseResult::get_member(const std::string &prop) const {
  Value ret_val;

  if (prop == "executionTime")
    return shcore::Value(get_execution_time());

  else if (prop == "warningCount")
    ret_val = Value(get_warning_count());

  else if (prop == "warnings") {
    std::shared_ptr<shcore::Value::Array_type> array(new shcore::Value::Array_type);

    std::vector< ::mysqlx::Result::Warning> warnings = _result->getWarnings();

    if (warnings.size()) {
      for (size_t index = 0; index < warnings.size(); index++) {
        mysqlsh::Row *warning_row = new mysqlsh::Row();

        warning_row->add_item("level", shcore::Value(warnings[index].is_note ? "Note" : "Warning"));
        warning_row->add_item("code", shcore::Value(warnings[index].code));
        warning_row->add_item("message", shcore::Value(warnings[index].text));

        array->push_back(shcore::Value::wrap(warning_row));
      }
    }

    ret_val = shcore::Value(array);
  } else
    ret_val = ShellBaseResult::get_member(prop);

  return ret_val;
}

// Documentation of getExecutionTime function
REGISTER_HELP(BASERESULT_GETEXECUTIONTIME_BRIEF, "Retrieves a string value indicating the execution time of the executed operation.");

/**
* $(BASERESULT_GETEXECUTIONTIME_BRIEF)
*/
#if DOXYGEN_JS
String BaseResult::getExecutionTime() {};
#elif DOXYGEN_PY
str BaseResult::get_execution_time() {};
#endif

std::string BaseResult::get_execution_time() const {
  return MySQL_timer::format_legacy(_execution_time, 2);
}

// Documentation of getWarningCount function
REGISTER_HELP(BASERESULT_GETWARNINGCOUNT_BRIEF, "The number of warnings produced by the last statement execution. See getWarnings() for more details.");
REGISTER_HELP(BASERESULT_GETWARNINGCOUNT_RETURNS, "@returns the number of warnings.");
REGISTER_HELP(BASERESULT_GETWARNINGCOUNT_DETAIL, "This is the same value than C API mysql_warning_count, see https://dev.mysql.com/doc/refman/5.7/en/mysql-warning-count.html");

/**
* $(BASERESULT_GETWARNINGCOUNT_BRIEF)
*
* $(BASERESULT_GETWARNINGCOUNT_RETURNS)
*
* $(BASERESULT_GETWARNINGCOUNT_DETAIL)
*
* \sa warnings
*/
#if DOXYGEN_JS
Integer BaseResult::getWarningCount() {};
#elif DOXYGEN_PY
int BaseResult::get_warning_count() {};
#endif

uint64_t BaseResult::get_warning_count() const {
  return uint64_t(_result->getWarnings().size());
}

void BaseResult::buffer() {
  _result->buffer();
}

bool BaseResult::rewind() {
  return _result->rewind();
}

bool BaseResult::tell(size_t &dataset, size_t &record) {
  return _result->tell(dataset, record);
}

bool BaseResult::seek(size_t dataset, size_t record) {
  return _result->seek(dataset, record);
}

void BaseResult::append_json(shcore::JSON_dumper& dumper) const {
  bool create_object = (dumper.deep_level() == 0);

  if (create_object)
    dumper.start_object();

  dumper.append_value("executionTime", get_member("executionTime"));

  if (Shell_core_options::get()->get_bool(SHCORE_SHOW_WARNINGS)) {
    dumper.append_value("warningCount", get_member("warningCount"));
    dumper.append_value("warnings", get_member("warnings"));
  }

  if (create_object)
    dumper.end_object();
}

// -----------------------------------------------------------------------

// Documentation of Result class
REGISTER_HELP(RESULT_BRIEF, "Allows retrieving information about non query operations performed on the database.");
REGISTER_HELP(RESULT_DETAIL, "An instance of this class will be returned on the CRUD operations that change the content of the database:");
REGISTER_HELP(RESULT_DETAIL1, "@li On Table: insert, update and delete");
REGISTER_HELP(RESULT_DETAIL2, "@li On Collection: add, modify and remove");
REGISTER_HELP(RESULT_DETAIL3, "Other functions on the BaseSession class also return an instance of this class:");
REGISTER_HELP(RESULT_DETAIL4, "@li Transaction handling functions");
REGISTER_HELP(RESULT_DETAIL5, "@li Transaction handling functions");

Result::Result(std::shared_ptr< ::mysqlx::Result> result) :
BaseResult(result) {
  add_property("affectedItemCount", "getAffectedItemCount");
  add_property("autoIncrementValue", "getAutoIncrementValue");
  add_property("lastDocumentId", "getLastDocumentId");
  add_property("lastDocumentIds", "getLastDocumentIds");
}

shcore::Value Result::get_member(const std::string &prop) const {
  Value ret_val;

  if (prop == "affectedItemCount")
    ret_val = Value(get_affected_item_count());

  else if (prop == "autoIncrementValue")
    ret_val = Value(get_auto_increment_value());

  else if (prop == "lastDocumentId")
    ret_val = Value(get_last_document_id());

  else if (prop == "lastDocumentIds") {
    shcore::Value::Array_type_ref ret_val(new shcore::Value::Array_type);
    std::vector<std::string> doc_ids = get_last_document_ids();

    for (auto doc_id : doc_ids)
      ret_val->push_back(shcore::Value(doc_id));

    return shcore::Value(ret_val);
  } else
    ret_val = BaseResult::get_member(prop);

  return ret_val;
}

// Documentation of getAffectedItemCount function
REGISTER_HELP(RESULT_GETAFFECTEDITEMCOUNT_BRIEF, "The the number of affected items for the last operation.");
REGISTER_HELP(RESULT_GETAFFECTEDITEMCOUNT_RETURNS, "@returns the number of affected items.");
REGISTER_HELP(RESULT_GETAFFECTEDITEMCOUNT_DETAIL, "This is the value of the C API mysql_affected_rows(), see https://dev.mysql.com/doc/refman/5.7/en/mysql-affected-rows.html");

/**
* $(RESULT_GETAFFECTEDITEMCOUNT_BRIEF)
*
* $(RESULT_GETAFFECTEDITEMCOUNT_RETURNS)
*
* $(RESULT_GETAFFECTEDITEMCOUNT_DETAIL)
*/
#if DOXYGEN_JS
Integer Result::getAffectedItemCount() {};
#elif DOXYGEN_PY
int Result::get_affected_item_count() {};
#endif

int64_t Result::get_affected_item_count() const {
  return _result->affectedRows();
}

// Documentation of getAutoIncrementValue function
REGISTER_HELP(RESULT_GETAUTOINCREMENTVALUE_BRIEF, "The last insert id auto generated (from an insert operation)");
REGISTER_HELP(RESULT_GETAUTOINCREMENTVALUE_RETURNS, "@returns the integer representing the last insert id");
REGISTER_HELP(RESULT_GETAUTOINCREMENTVALUE_DETAIL, "For more details, see https://dev.mysql.com/doc/refman/5.7/en/information-functions.html#function_last-insert-id");
REGISTER_HELP(RESULT_GETAUTOINCREMENTVALUE_DETAIL1, "Note that this value will be available only when the result is for a Table.insert operation.");

/**
* $(RESULT_GETAUTOINCREMENTVALUE_BRIEF)
*
* $(RESULT_GETAUTOINCREMENTVALUE_RETURNS)
*
* $(RESULT_GETAUTOINCREMENTVALUE_DETAIL)
*
* $(RESULT_GETAUTOINCREMENTVALUE_DETAIL1)
*/
#if DOXYGEN_JS
Integer Result::getAutoIncrementValue() {};
#elif DOXYGEN_PY
int Result::get_auto_increment_value() {};
#endif

int64_t Result::get_auto_increment_value() const {
  return _result->lastInsertId();
}

// Documentation of getLastDocumentId function
REGISTER_HELP(RESULT_GETLASTDOCUMENTID_BRIEF, "The id of the last document inserted into a collection.");
REGISTER_HELP(RESULT_GETLASTDOCUMENTID_RETURNS, "@returns the string representing the if of the last inserted document.");
REGISTER_HELP(RESULT_GETLASTDOCUMENTID_DETAIL, "Note that this value will be available only when the result is for a Collection.add operation.");

/**
* $(RESULT_GETLASTDOCUMENTID_BRIEF)
*
* $(RESULT_GETLASTDOCUMENTID_RETURNS)
*
* $(RESULT_GETLASTDOCUMENTID_DETAIL)
*/
#if DOXYGEN_JS
String Result::getLastDocumentId() {};
#elif DOXYGEN_PY
str Result::get_last_document_id() {};
#endif

std::string Result::get_last_document_id() const {
  std::string ret_val;
  try {
    ret_val = _result->lastDocumentId();
  }
  CATCH_AND_TRANSLATE_FUNCTION_EXCEPTION(get_function_name("getLastDocumentId"));

  return ret_val;
}

const std::vector<std::string> Result::get_last_document_ids() const {
  std::vector<std::string> ret_val;
  try {
    ret_val = _result->lastDocumentIds();
  }
  CATCH_AND_TRANSLATE_FUNCTION_EXCEPTION(get_function_name("getLastDocumentIds"));
  return ret_val;
}

void Result::append_json(shcore::JSON_dumper& dumper) const {
  dumper.start_object();

  BaseResult::append_json(dumper);

  dumper.append_value("affectedItemCount", get_member("affectedItemCount"));
  dumper.append_value("autoIncrementValue", get_member("autoIncrementValue"));
  dumper.append_value("lastDocumentId", get_member("lastDocumentId"));

  dumper.end_object();
}

// -----------------------------------------------------------------------

// Documentation of DocResult class
REGISTER_HELP(DOCRESULT_BRIEF, "Allows traversing the DbDoc objects returned by a Collection.find operation.");

DocResult::DocResult(std::shared_ptr< ::mysqlx::Result> result) :
BaseResult(result) {
  add_method("fetchOne", std::bind(&DocResult::fetch_one, this, _1), "nothing", shcore::String, NULL);
  add_method("fetchAll", std::bind(&DocResult::fetch_all, this, _1), "nothing", shcore::String, NULL);
}

// Documentation of fetchOne function
REGISTER_HELP(DOCRESULT_FETCHONE_BRIEF, "Retrieves the next DbDoc on the DocResult.");
REGISTER_HELP(DOCRESULT_FETCHONE_RETURNS, "@returns A DbDoc object representing the next Document in the result.");

/**
* $(DOCRESULT_FETCHONE_BRIEF)
*
* $(DOCRESULT_FETCHONE_RETURNS)
*/
#if DOXYGEN_JS
Document DocResult::fetchOne() {};
#elif DOXYGEN_PY
Document DocResult::fetch_one() {};
#endif
shcore::Value DocResult::fetch_one(const shcore::Argument_list &args) const {
  Value ret_val = Value::Null();

  args.ensure_count(0, get_function_name("fetchOne").c_str());

  try {
    if (_result->columnMetadata() && _result->columnMetadata()->size()) {
      std::shared_ptr< ::mysqlx::Row> r(_result->next());
      if (r.get())
        ret_val = Value::parse(r->stringField(0));
    }
  }
  CATCH_AND_TRANSLATE_FUNCTION_EXCEPTION(get_function_name("fetchOne"));

  return ret_val;
}

// Documentation of fetchAll function
REGISTER_HELP(DOCRESULT_FETCHALL_BRIEF, "Returns a list of DbDoc objects which contains an element for every unread document.");
REGISTER_HELP(DOCRESULT_FETCHALL_RETURNS, "@returns A List of DbDoc objects.");
REGISTER_HELP(DOCRESULT_FETCHALL_DETAIL, "If this function is called right after executing a query, it will return a DbDoc for every document on the resultset.");
REGISTER_HELP(DOCRESULT_FETCHALL_DETAIL1, "If fetchOne is called before this function, when this function is called it will return a DbDoc for each of the remaining documents on the resultset.");

/**
* $(DOCRESULT_FETCHALL_BRIEF)
*
* $(DOCRESULT_FETCHALL_RETURNS)
*
* $(DOCRESULT_FETCHALL_DETAIL)
*
* $(DOCRESULT_FETCHALL_DETAIL1)
*/
#if DOXYGEN_JS
List DocResult::fetchAll() {};
#elif DOXYGEN_PY
list DocResult::fetch_all() {};
#endif
shcore::Value DocResult::fetch_all(const shcore::Argument_list &args) const {
  Value::Array_type_ref array(new Value::Array_type());

  args.ensure_count(0, get_function_name("fetchAll").c_str());

  // Gets the next document
  Value record = fetch_one(args);
  while (record) {
    array->push_back(record);
    record = fetch_one(args);
  }

  return Value(array);
}

shcore::Value DocResult::get_metadata() const {
  if (!_metadata) {
    shcore::Value data_type = mysqlsh::Constant::get_constant("mysqlx", "Type", "JSON", shcore::Argument_list());

    // the plugin may not send these if they are equal to table/name respectively
    // We need to reconstruct them
    std::string orig_table = _result->columnMetadata()->at(0).original_table;
    std::string orig_name = _result->columnMetadata()->at(0).original_name;

    if (orig_table.empty())
      orig_table = _result->columnMetadata()->at(0).table;

    if (orig_name.empty())
      orig_name = _result->columnMetadata()->at(0).name;

    std::shared_ptr<mysqlsh::Column> metadata(new mysqlsh::Column(
      _result->columnMetadata()->at(0).schema,
      orig_table,
      _result->columnMetadata()->at(0).table,
      orig_name,
      _result->columnMetadata()->at(0).name,
      data_type,
      _result->columnMetadata()->at(0).length,
      false, // IS NUMERIC
      _result->columnMetadata()->at(0).fractional_digits,
      false, // IS SIGNED
      mysqlsh::charset::collation_name_from_collation_id(
          _result->columnMetadata()->at(0).collation),
      mysqlsh::charset::charset_name_from_collation_id(
          _result->columnMetadata()->at(0).collation),       true)); // IS PADDED

    _metadata = shcore::Value(std::static_pointer_cast<Object_bridge>(metadata));
  }

  return _metadata;
}

void DocResult::append_json(shcore::JSON_dumper& dumper) const {
  dumper.start_object();

  dumper.append_value("documents", fetch_all(shcore::Argument_list()));

  BaseResult::append_json(dumper);

  dumper.end_object();
}

// -----------------------------------------------------------------------

// Documentation of RowResult class
REGISTER_HELP(ROWRESULT_BRIEF, "Allows traversing the Row objects returned by a Table.select operation.");

RowResult::RowResult(std::shared_ptr< ::mysqlx::Result> result) :
BaseResult(result) {
  add_property("columnCount", "getColumnCount");
  add_property("columns", "getColumns");
  add_property("columnNames", "getColumnNames");

  add_method("fetchOne", std::bind(&RowResult::fetch_one, this, _1), "nothing", shcore::String, NULL);
  add_method("fetchAll", std::bind(&RowResult::fetch_all, this, _1), "nothing", shcore::String, NULL);
}

shcore::Value RowResult::get_member(const std::string &prop) const {
  Value ret_val;
  if (prop == "columnCount")
    ret_val = shcore::Value(get_column_count());
  else if (prop == "columnNames") {
    std::shared_ptr<shcore::Value::Array_type> array(new shcore::Value::Array_type);

    if (_result->columnMetadata()) {
      size_t num_fields = _result->columnMetadata()->size();

      for (size_t i = 0; i < num_fields; i++)
        array->push_back(shcore::Value(_result->columnMetadata()->at(i).name));
    }

    ret_val = shcore::Value(array);
  } else if (prop == "columns")
    ret_val = shcore::Value(get_columns());
  else
    ret_val = BaseResult::get_member(prop);

  return ret_val;
}

// Documentation of getColumnCount function
REGISTER_HELP(ROWRESULT_GETCOLUMNCOUNT_BRIEF, "Retrieves the number of columns on the current result.");
REGISTER_HELP(ROWRESULT_GETCOLUMNCOUNT_RETURNS, "@returns the number of columns on the current result.");

/**
* $(ROWRESULT_GETCOLUMNCOUNT_BRIEF)
*
* $(ROWRESULT_GETCOLUMNCOUNT_RETURNS)
*/
#if DOXYGEN_JS
Integer RowResult::getColumnCount() {};
#elif DOXYGEN_PY
int RowResult::get_column_count() {};
#endif
int64_t RowResult::get_column_count() const {
  size_t count = 0;
  if (_result->columnMetadata())
    count = _result->columnMetadata()->size();

  return uint64_t(count);
}

// Documentation of getColumnNames function
REGISTER_HELP(ROWRESULT_GETCOLUMNNAMES_BRIEF, "Gets the columns on the current result.");
REGISTER_HELP(ROWRESULT_GETCOLUMNNAMES_RETURNS, "@returns A list with the names of the columns returned on the active result.");

/**
* $(ROWRESULT_GETCOLUMNNAMES_BRIEF)
*
* $(ROWRESULT_GETCOLUMNNAMES_RETURNS)
*/
#if DOXYGEN_JS
List RowResult::getColumnNames() {};
#elif DOXYGEN_PY
list RowResult::get_column_names() {};
#endif
std::vector<std::string> RowResult::get_column_names() const {
  std::vector<std::string> ret_val;

  if (_result->columnMetadata()) {
    size_t num_fields = _result->columnMetadata()->size();

    for (size_t i = 0; i < num_fields; i++)
      ret_val.push_back(_result->columnMetadata()->at(i).name);
  }

  return ret_val;
}

// Documentation of getColumns function
REGISTER_HELP(ROWRESULT_GETCOLUMNS_BRIEF, "Gets the column metadata for the columns on the active result.");
REGISTER_HELP(ROWRESULT_GETCOLUMNS_RETURNS, "@returns a list of Column objects containing information about the columns included on the active result.");

/**
* $(ROWRESULT_GETCOLUMNS_BRIEF)
*
* $(ROWRESULT_GETCOLUMNS_RETURNS)
*/
#if DOXYGEN_JS
List RowResult::getColumns() {};
#elif DOXYGEN_PY
list RowResult::get_columns() {};
#endif
shcore::Value::Array_type_ref RowResult::get_columns() const {
  if (!_columns) {
    _columns.reset(new shcore::Value::Array_type);

    size_t num_fields = _result->columnMetadata()->size();
    for (size_t i = 0; i < num_fields; i++) {
      ::mysqlx::FieldType type = _result->columnMetadata()->at(i).type;
      bool is_numeric = type == ::mysqlx::SINT ||
        type == ::mysqlx::UINT ||
        type == ::mysqlx::DOUBLE ||
        type == ::mysqlx::FLOAT ||
        type == ::mysqlx::DECIMAL;

      std::string type_name;
      bool is_signed = false;
      bool is_padded = true;
      switch (_result->columnMetadata()->at(i).type) {
        case ::mysqlx::SINT:
          is_signed = true;
        case ::mysqlx::UINT:
          switch (_result->columnMetadata()->at(i).length) {
            case 3:
            case 4:
              type_name = "TINYINT";
              break;
            case 5:
            case 6:
              type_name = "SMALLINT";
              break;
            case 8:
            case 9:
              type_name = "MEDIUMINT";
              break;
            case 10:
            case 11:
              type_name = "INT";
              break;
            case 20:
              type_name = "BIGINT";
              break;
          }
          break;
        case ::mysqlx::BIT:
          type_name = "BIT";
          break;
        case ::mysqlx::DOUBLE:
          type_name = "DOUBLE";
          is_signed = !(_result->columnMetadata()->at(i).flags & 0x001);
          break;
        case ::mysqlx::FLOAT:
          type_name = "FLOAT";
          is_signed = !(_result->columnMetadata()->at(i).flags & 0x001);
          break;
        case ::mysqlx::DECIMAL:
          type_name = "DECIMAL";
          is_signed = !(_result->columnMetadata()->at(i).flags & 0x001);
          break;
        case ::mysqlx::BYTES:
          is_padded = is_signed = _result->columnMetadata()->at(i).flags & 0x001;

          switch (_result->columnMetadata()->at(i).content_type & 0x0003) {
            case 1:
              type_name = "GEOMETRY";
              break;
            case 2:
              type_name = "JSON";
              break;
            case 3:
              type_name = "XML";
              break;
            default:
              if (mysqlsh::charset::charset_name_from_collation_id(
                      _result->columnMetadata()->at(i).collation) == "binary")
                type_name = "BYTES";
              else
                type_name = "STRING";
              break;
          }
          break;
        case ::mysqlx::TIME:
          type_name = "TIME";
          break;
        case ::mysqlx::DATETIME:
          if (_result->columnMetadata()->at(i).flags & 0x001)
            type_name = "TIMESTAMP";
          else if (_result->columnMetadata()->at(i).length == 10)
            type_name = "DATE";
          else
            type_name = "DATETIME";
          break;
        case ::mysqlx::SET:
          type_name = "SET";
          break;
        case ::mysqlx::ENUM:
          type_name = "ENUM";
          break;
      }

      shcore::Value data_type = mysqlsh::Constant::get_constant("mysqlx", "Type", type_name, shcore::Argument_list());

      // the plugin may not send these if they are equal to table/name respectively
      // We need to reconstruct them
      std::string orig_table = _result->columnMetadata()->at(i).original_table;
      std::string orig_name = _result->columnMetadata()->at(i).original_name;

      if (orig_table.empty())
        orig_table = _result->columnMetadata()->at(i).table;

      if (orig_name.empty())
        orig_name = _result->columnMetadata()->at(i).name;

      std::shared_ptr<mysqlsh::Column> column(new mysqlsh::Column(
        _result->columnMetadata()->at(i).schema,
        orig_table,
        _result->columnMetadata()->at(i).table,
        orig_name,
        _result->columnMetadata()->at(i).name,
        data_type,
        _result->columnMetadata()->at(i).length,
        is_numeric,
        _result->columnMetadata()->at(i).fractional_digits,
        is_signed,
        mysqlsh::charset::collation_name_from_collation_id(
          _result->columnMetadata()->at(i).collation),
        mysqlsh::charset::charset_name_from_collation_id(
          _result->columnMetadata()->at(i).collation),         is_padded));

      _columns->push_back(shcore::Value(std::static_pointer_cast<Object_bridge>(column)));
    }
  }

  return _columns;
}

// Documentation of fetchOne function
REGISTER_HELP(ROWRESULT_FETCHONE_BRIEF, "Retrieves the next Row on the RowResult.");
REGISTER_HELP(ROWRESULT_FETCHONE_RETURNS, "@returns A Row object representing the next record on the result.");

/**
* $(ROWRESULT_FETCHONE_BRIEF)
*
* $(ROWRESULT_FETCHONE_RETURNS)
*/
#if DOXYGEN_JS
Row RowResult::fetchOne() {};
#elif DOXYGEN_PY
Row RowResult::fetch_one() {};
#endif
shcore::Value RowResult::fetch_one(const shcore::Argument_list &args) const {
  shcore::Value ret_val;
  args.ensure_count(0, get_function_name("fetchOne").c_str());

  try {
    std::shared_ptr<std::vector< ::mysqlx::ColumnMetadata> > metadata = _result->columnMetadata();
    std::string display_value;

    if (metadata->size() > 0) {
      std::shared_ptr< ::mysqlx::Row>row = _result->next();
      if (row) {
        mysqlsh::Row *value_row = new mysqlsh::Row();

        for (int index = 0; index < int(metadata->size()); index++) {
          Value field_value;

          if (row->isNullField(index))
            field_value = Value::Null();
          else {
            switch (metadata->at(index).type) {
              case ::mysqlx::SINT:
                field_value = Value(row->sInt64Field(index));
                break;
              case ::mysqlx::UINT:
                //Check if the ZEROFILL flag is set, if so then create proper display value
                if (metadata->at(index).flags & 0x0001) {
                  display_value = std::to_string(row->uInt64Field(index));
                  int count = metadata->at(index).length - display_value.length();
                  if (count > 0)
                    display_value.insert(0, count, '0');
                }
                field_value = Value(row->uInt64Field(index));
                break;
              case ::mysqlx::DOUBLE:
                field_value = Value(row->doubleField(index));
                break;
              case ::mysqlx::FLOAT:
                field_value = Value(row->floatField(index));
                break;
              case ::mysqlx::BYTES:
                field_value = Value(row->stringField(index));
                break;
              case ::mysqlx::DECIMAL:
                field_value = Value(row->decimalField(index));
                break;
              case ::mysqlx::TIME:
                field_value = Value(row->timeField(index).to_string());
                break;
              case ::mysqlx::DATETIME:
              {
                ::mysqlx::DateTime date = row->dateTimeField(index);
                std::shared_ptr<shcore::Date> shell_date(new shcore::Date(
                  date.year(), date.month(), date.day(), date.hour(),
                  date.minutes(), date.seconds() + ((double)date.useconds() / 1000000)));

                field_value = Value(std::static_pointer_cast<Object_bridge>(shell_date));
                break;
              }
              case ::mysqlx::ENUM:
                field_value = Value(row->enumField(index));
                break;
              case ::mysqlx::BIT:
                field_value = Value(row->bitField(index));
                break;
                //TODO: Fix the handling of SET
              case ::mysqlx::SET:
                //field_value = Value(row->setField(int(index)));
                break;
            }
          }
          if (display_value.empty())
            display_value = field_value.descr();
          value_row->add_item(metadata->at(index).name, field_value, display_value);
        }

        ret_val = shcore::Value::wrap(value_row);
      }
    }
  }
  CATCH_AND_TRANSLATE_FUNCTION_EXCEPTION(get_function_name("fetchOne"));

  return ret_val;
}

// Documentation of fetchAll function
REGISTER_HELP(ROWRESULT_FETCHALL_BRIEF, "Returns a list of DbDoc objects which contains an element for every unread document.");
REGISTER_HELP(ROWRESULT_FETCHALL_RETURNS, "@returns A List of DbDoc objects.");

/**
* $(ROWRESULT_FETCHALL_BRIEF)
*
* $(ROWRESULT_FETCHALL_RETURNS)
*/
#if DOXYGEN_JS
List RowResult::fetchAll() {};
#elif DOXYGEN_PY
list RowResult::fetch_all() {};
#endif
shcore::Value RowResult::fetch_all(const shcore::Argument_list &args) const {
  Value::Array_type_ref array(new Value::Array_type());

  args.ensure_count(0, get_function_name("fetchAll").c_str());

  // Gets the next row
  Value record = fetch_one(args);
  while (record) {
    array->push_back(record);
    record = fetch_one(args);
  }

  return Value(array);
}

void RowResult::append_json(shcore::JSON_dumper& dumper) const {
  bool create_object = (dumper.deep_level() == 0);

  if (create_object)
    dumper.start_object();

  BaseResult::append_json(dumper);

  dumper.append_value("rows", fetch_all(shcore::Argument_list()));

  if (create_object)
    dumper.end_object();
}

// Documentation of SqlResult class
REGISTER_HELP(SQLRESULT_BRIEF, "Allows browsing through the result information after performing an operation on the database done through NodeSession.sql");

SqlResult::SqlResult(std::shared_ptr< ::mysqlx::Result> result) :
RowResult(result) {
  add_method("hasData", std::bind(&SqlResult::has_data, this, _1), "nothing", shcore::String, NULL);
  add_method("nextDataSet", std::bind(&SqlResult::next_data_set, this, _1), "nothing", shcore::String, NULL);
  add_property("autoIncrementValue", "getAutoIncrementValue");
  add_property("affectedRowCount", "getAffectedRowCount");
}

// Documentation of hasData function
REGISTER_HELP(SQLRESULT_HASDATA_BRIEF, "Returns true if the last statement execution has a result set.");

/**
* $(SQLRESULT_HASDATA_BRIEF)
*
*/
#if DOXYGEN_JS
Bool SqlResult::hasData() {}
#elif DOXYGEN_PY
bool SqlResult::has_data() {}
#endif
shcore::Value SqlResult::has_data(const shcore::Argument_list &args) const {
  args.ensure_count(0, get_function_name("hasData").c_str());

  return Value(_result->has_data());
}

// Documentation of getAutoIncrementValue function
REGISTER_HELP(SQLRESULT_GETAUTOINCREMENTVALUE_BRIEF, "Returns the identifier for the last record inserted.");
REGISTER_HELP(SQLRESULT_GETAUTOINCREMENTVALUE_DETAIL, "Note that this value will only be set if the executed statement inserted a record in the database and an ID was automatically generated.");

/**
* $(SQLRESULT_GETAUTOINCREMENTVALUE_BRIEF)
*
* $(SQLRESULT_GETAUTOINCREMENTVALUE_DETAIL)
*/
#if DOXYGEN_JS
Integer SqlResult::getAutoIncrementValue() {};
#elif DOXYGEN_PY
int SqlResult::get_auto_increment_value() {};
#endif
int64_t SqlResult::get_auto_increment_value() const {
  return _result->lastInsertId();
}

// Documentation of getAffectedRowCount function
REGISTER_HELP(SQLRESULT_GETAFFECTEDROWCOUNT_BRIEF, "Returns the number of rows affected by the executed query.");

/**
* $(SQLRESULT_GETAFFECTEDROWCOUNT_BRIEF)
*/
#if DOXYGEN_JS
Integer SqlResult::getAffectedRowCount() {};
#elif DOXYGEN_PY
int SqlResult::get_affected_row_count() {};
#endif
int64_t SqlResult::get_affected_row_count() const {
  return _result->affectedRows();
}

shcore::Value SqlResult::get_member(const std::string &prop) const {
  Value ret_val;
  if (prop == "autoIncrementValue")
    ret_val = Value(get_auto_increment_value());
  else if (prop == "affectedRowCount")
    ret_val = Value(get_affected_row_count());
  else
    ret_val = RowResult::get_member(prop);

  return ret_val;
}

// Documentation of nextDataSet function
REGISTER_HELP(SQLRESULT_NEXTDATASET_BRIEF, "Prepares the SqlResult to start reading data from the next Result (if many results were returned).");
REGISTER_HELP(SQLRESULT_NEXTDATASET_RETURNS, "@returns A boolean value indicating whether there is another result or not.");

/**
* $(SQLRESULT_NEXTDATASET_BRIEF)
*
* $(SQLRESULT_NEXTDATASET_RETURNS)
*/
#if DOXYGEN_JS
Bool SqlResult::nextDataSet() {};
#elif DOXYGEN_PY
bool SqlResult::next_data_set() {};
#endif
shcore::Value SqlResult::next_data_set(const shcore::Argument_list &args) {
  args.ensure_count(0, get_function_name("nextDataSet").c_str());

  return shcore::Value(_result->nextDataSet());
}

void SqlResult::append_json(shcore::JSON_dumper& dumper) const {
  dumper.start_object();

  RowResult::append_json(dumper);

  dumper.append_value("hasData", has_data(shcore::Argument_list()));
  dumper.append_value("affectedRowCount", get_member("affectedRowCount"));
  dumper.append_value("autoIncrementValue", get_member("autoIncrementValue"));

  dumper.end_object();
}
