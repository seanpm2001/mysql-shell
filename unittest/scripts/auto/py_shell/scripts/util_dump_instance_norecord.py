#@<> INCLUDE dump_utils.inc

#@<> entry point

# imports
import json
import os
import os.path
import random
import re
import shutil
import stat

# constants
world_x_schema = "world_x_cities"
world_x_table = "cities"

# schema name can consist of 51 reserved characters max, server supports up to
# 64 chars but when it creates the directory for schema, it encodes non-letters
# ASCII using five bytes, meaning the directory name is going to be 255
# characters long (max on most # platforms)
# schema name consists of 49 reserved characters + UTF-8 character
test_schema = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ó"
test_table_primary = "first"
test_table_unique = "second"
# mysql_data_home + schema + table name + path separators cannot exceed 512
# characters
# table name consists of 48 reserved characters + UTF-8 character
test_table_non_unique = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ą"
test_table_no_index = "fóurth"
test_table_trigger = "sample_trigger"
test_schema_procedure = "sample_procedure"
test_schema_function = "sample_function"
test_schema_event = "sample_event"
test_view = "sample_view"
test_role = "sample_role"
test_user_no_pwd = get_test_user_account("sample_user_no_pwd")
test_privileges = [ "FILE" ]
if __version_num >= 80000:
    test_privileges.append("RESOURCE_GROUP_ADMIN")
test_all_allowed_privileges = "allowed_privileges"
test_disallowed_privileges = "disallowed_privileges"

allowed_authentication_plugins = [
    "caching_sha2_password",
    "mysql_native_password",
    "sha256_password"
]

all_authentication_plugins = [
    "auth_socket",
    "authentication_ldap_sasl",
    "authentication_ldap_simple",
    "authentication_pam",
    "authentication_windows",
    "caching_sha2_password",
    "mysql_native_password",
    "mysql_no_login",
    "sha256_password"
]

disallowed_authentication_plugins = set(all_authentication_plugins) - set(allowed_authentication_plugins)

allowed_privileges = [
    # each account has USAGE
    "USAGE",
    # global static privileges
    "ALTER",
    "ALTER ROUTINE",
    "CREATE",
    "CREATE ROLE",
    "CREATE ROUTINE",
    "CREATE TEMPORARY TABLES",
    "CREATE USER",
    "CREATE VIEW",
    "DELETE",
    "DROP",
    "DROP ROLE",
    "EVENT",
    "EXECUTE",
    "INDEX",
    "INSERT",
    "LOCK TABLES",
    "PROCESS",
    "REFERENCES",
    "REPLICATION CLIENT",
    "REPLICATION SLAVE",
    "SELECT",
    "SHOW DATABASES",
    "SHOW VIEW",
    "TRIGGER",
    "UPDATE",
    # global dynamic privileges
    "APPLICATION_PASSWORD_ADMIN",
    "AUDIT_ADMIN",
    "BACKUP_ADMIN",
    "CONNECTION_ADMIN",
    "FLUSH_OPTIMIZER_COSTS",
    "FLUSH_STATUS",
    "FLUSH_TABLES",
    "FLUSH_USER_RESOURCES",
    "REPLICATION_APPLIER",
    "ROLE_ADMIN",
    "XA_RECOVER_ADMIN",
]

all_privileges = [
    # static privileges
    "ALTER",
    "ALTER ROUTINE",
    "CREATE",
    "CREATE ROLE",
    "CREATE ROUTINE",
    "CREATE TABLESPACE",
    "CREATE TEMPORARY TABLES",
    "CREATE USER",
    "CREATE VIEW",
    "DELETE",
    "DROP",
    "DROP ROLE",
    "EVENT",
    "EXECUTE",
    "FILE",
    "GRANT OPTION",
    "INDEX",
    "INSERT",
    "LOCK TABLES",
    "PROCESS",
    "PROXY",
    "REFERENCES",
    "RELOAD",
    "REPLICATION CLIENT",
    "REPLICATION SLAVE",
    "SELECT",
    "SHOW DATABASES",
    "SHOW VIEW",
    "SHUTDOWN",
    "SUPER",
    "TRIGGER",
    "UPDATE",
    "USAGE",
    # dynamic privileges
    "APPLICATION_PASSWORD_ADMIN",
    "AUDIT_ADMIN",
    "BACKUP_ADMIN",
    "BINLOG_ADMIN",
    "BINLOG_ENCRYPTION_ADMIN",
    "CLONE_ADMIN",
    "CONNECTION_ADMIN",
    "ENCRYPTION_KEY_ADMIN",
    "FIREWALL_ADMIN",
    "FIREWALL_USER",
    "FLUSH_OPTIMIZER_COSTS",
    "FLUSH_STATUS",
    "FLUSH_TABLES",
    "FLUSH_USER_RESOURCES",
    "GROUP_REPLICATION_ADMIN",
    "INNODB_REDO_LOG_ARCHIVE",
    "NDB_STORED_USER",
    "PERSIST_RO_VARIABLES_ADMIN",
    "REPLICATION_APPLIER",
    "REPLICATION_SLAVE_ADMIN",
    "RESOURCE_GROUP_ADMIN",
    "RESOURCE_GROUP_USER",
    "ROLE_ADMIN",
    "SESSION_VARIABLES_ADMIN",
    "SET_USER_ID",
    "SHOW_ROUTINE",
    "SYSTEM_USER",
    "SYSTEM_VARIABLES_ADMIN",
    "TABLE_ENCRYPTION_ADMIN",
    "VERSION_TOKEN_ADMIN",
    "XA_RECOVER_ADMIN",
]

# GRANT OPTION is implicitly allowed
disallowed_privileges = set(all_privileges) - set(allowed_privileges) - {'GRANT OPTION'}

verification_schema = "wl13807_ver"

types_schema = "xtest"

incompatible_schema = "mysqlaas"
incompatible_table_wrong_engine = "wrong_engine"
incompatible_table_encryption = "has_encryption"
incompatible_table_data_directory = "has_data_dir"
incompatible_table_index_directory = "has_index_dir"
incompatible_tablespace = "sample_tablespace"
incompatible_table_tablespace = "use_tablespace"
incompatible_view = "has_definer"

incompatible_table_directory = os.path.join(__tmp_dir, "incompatible")
table_data_directory = os.path.join(incompatible_table_directory, "data")
table_index_directory = os.path.join(incompatible_table_directory, "index")

shutil.rmtree(incompatible_table_directory, True)
os.makedirs(incompatible_table_directory)
os.mkdir(table_data_directory)
os.mkdir(table_index_directory)

if __os_type == "windows":
    # on windows server would have to be installed in the root folder to
    # handle long schema/table names
    if __version_num >= 80000:
        test_schema = "@ó"
        test_table_non_unique = "@ą"
    else:
        # when using latin1 encoding, UTF-8 characters sent by shell are converted by server
        # to latin1 representation, then upper case characters are converted to lower case,
        # which leads to invalid UTF-8 sequences when names are transfered back to shell
        # use ASCII in this case
        test_schema = "@o"
        test_table_non_unique = "@a"
        test_table_no_index = "fourth"

all_schemas = [world_x_schema, types_schema, test_schema, verification_schema, incompatible_schema]
exclude_all_but_types_schema = all_schemas[:]
exclude_all_but_types_schema.remove(types_schema)

uri = __sandbox_uri1
xuri = __sandbox_uri1.replace("mysql://", "mysqlx://") + "0"

test_output_relative = "dump_output"
test_output_absolute = os.path.abspath(test_output_relative)

# helpers
if __os_type != "windows":
    def filename_for_file(filename):
        return filename
else:
    def filename_for_file(filename):
        return filename.replace("\\", "/")

if __os_type != "windows":
    def absolute_path_for_output(path):
        return path
else:
    def absolute_path_for_output(path):
        long_path_prefix = r"\\?" "\\"
        return long_path_prefix + path

def setup_session(u = uri):
    shell.connect(u)
    session.run_sql("SET NAMES 'utf8mb4';")
    if __user + ":" in u:
        session.run_sql("SET GLOBAL local_infile = true;")

def drop_all_schemas(exclude=[]):
    for schema in session.run_sql("SELECT SCHEMA_NAME FROM information_schema.schemata;").fetch_all():
        if schema[0] not in ["information_schema", "mysql", "performance_schema", "sys"] + exclude:
            session.run_sql("DROP SCHEMA IF EXISTS !;", [ schema[0] ])

def create_all_schemas():
    for schema in all_schemas:
        session.run_sql("CREATE SCHEMA IF NOT EXISTS !;", [ schema ])

def create_authentication_plugin_user(name):
    full_name = get_test_user_account(name)
    session.run_sql("DROP USER IF EXISTS " + full_name)
    ensure_plugin_enabled(name, session)
    session.run_sql("CREATE USER IF NOT EXISTS {0} IDENTIFIED WITH ? BY 'pwd'".format(full_name), [name])

def create_users():
    # test user which has some disallowed privileges
    session.run_sql(f"DROP USER IF EXISTS {test_user_account};")
    session.run_sql(f"CREATE USER IF NOT EXISTS {test_user_account} IDENTIFIED BY ?;", [test_user_pwd])
    session.run_sql(f"GRANT {','.join(test_privileges)} ON *.* TO {test_user_account};")
    # test user without password
    session.run_sql(f"DROP USER IF EXISTS {test_user_no_pwd};")
    session.run_sql(f"CREATE USER IF NOT EXISTS {test_user_no_pwd};")
    # accounts which use allowed authentication plugins
    global allowed_authentication_plugins
    allowed = []
    for plugin in allowed_authentication_plugins:
        try:
            create_authentication_plugin_user(plugin)
            allowed.append(plugin)
        except Exception as e:
            pass
    allowed_authentication_plugins = allowed
    # accounts which use disallowed authentication plugins
    global disallowed_authentication_plugins
    disallowed = []
    for plugin in disallowed_authentication_plugins:
        try:
            create_authentication_plugin_user(plugin)
            disallowed.append(plugin)
        except Exception as e:
            pass
    disallowed_authentication_plugins = disallowed
    # user which has all allowed privileges
    global allowed_privileges
    account_name = get_test_user_account(test_all_allowed_privileges)
    session.run_sql("DROP USER IF EXISTS " + account_name)
    session.run_sql("CREATE USER IF NOT EXISTS " + account_name + " IDENTIFIED BY 'pwd'")
    for privilege in allowed_privileges:
        try:
            session.run_sql("GRANT {0} ON *.* TO {1}".format(privilege, account_name))
        except Exception as e:
            # ignore exceptions on non-exisiting privileges
            pass
    # user which has only disallowed privileges
    global disallowed_privileges
    disallowed = []
    account_name = get_test_user_account(test_disallowed_privileges)
    session.run_sql("DROP USER IF EXISTS " + account_name)
    session.run_sql("CREATE USER IF NOT EXISTS " + account_name + " IDENTIFIED BY 'pwd'")
    for privilege in disallowed_privileges:
        try:
            session.run_sql("GRANT {0} ON *.* TO {1}".format(privilege, account_name))
            disallowed.append(privilege)
        except Exception as e:
            # ignore exceptions on non-existing privileges
            pass
    disallowed_privileges = disallowed

def recreate_verification_schema():
    session.run_sql("DROP SCHEMA IF EXISTS !;", [ verification_schema ])
    session.run_sql("CREATE SCHEMA !;", [ verification_schema ])

def EXPECT_SUCCESS(schemas, outputUrl, options = {}):
    WIPE_STDOUT()
    shutil.rmtree(test_output_absolute, True)
    EXPECT_FALSE(os.path.isdir(test_output_absolute))
    if schemas and not "includeSchemas" in options and not "excludeSchemas" in options:
        options["includeSchemas"] = schemas
    util.dump_instance(outputUrl, options)
    included = options.get("includeSchemas", [])
    if not "dryRun" in options and len(included) > 0:
        EXPECT_STDOUT_CONTAINS(f"Schemas dumped: {len(included)}")

def EXPECT_FAIL(error, msg, outputUrl, options = {}, expect_dir_created = False):
    shutil.rmtree(test_output_absolute, True)
    is_re = is_re_instance(msg)
    full_msg = "{0}: Util.dump_instance: {1}".format(re.escape(error) if is_re else error, msg.pattern if is_re else msg)
    if is_re:
        full_msg = re.compile("^" + full_msg)
    EXPECT_THROWS(lambda: util.dump_instance(outputUrl, options), full_msg)
    EXPECT_EQ(expect_dir_created, os.path.isdir(test_output_absolute), "Output directory should" + ("" if expect_dir_created else " NOT") + " be created.")

def TEST_BOOL_OPTION(option):
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Bool, but is Null".format(option), test_output_relative, { option: None })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' Bool expected, but value is String".format(option), test_output_relative, { option: "dummy" })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Bool, but is Array".format(option), test_output_relative, { option: [] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Bool, but is Map".format(option), test_output_relative, { option: {} })

def TEST_STRING_OPTION(option):
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type String, but is Null".format(option), test_output_relative, { option: None })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type String, but is Integer".format(option), test_output_relative, { option: 5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type String, but is Integer".format(option), test_output_relative, { option: -5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type String, but is Array".format(option), test_output_relative, { option: [] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type String, but is Map".format(option), test_output_relative, { option: {} })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type String, but is Bool".format(option), test_output_relative, { option: False })

def TEST_UINT_OPTION(option):
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type UInteger, but is Null".format(option), test_output_relative, { option: None })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' UInteger expected, but Integer value is out of range".format(option), test_output_relative, { option: -5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' UInteger expected, but value is String".format(option), test_output_relative, { option: "dummy" })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type UInteger, but is Array".format(option), test_output_relative, { option: [] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type UInteger, but is Map".format(option), test_output_relative, { option: {} })

def TEST_ARRAY_OF_STRINGS_OPTION(option):
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Array, but is Integer".format(option), test_output_relative, { option: 5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Array, but is Integer".format(option), test_output_relative, { option: -5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Array, but is String".format(option), test_output_relative, { option: "dummy" })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Array, but is Map".format(option), test_output_relative, { option: {} })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Array, but is Bool".format(option), test_output_relative, { option: False })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Null".format(option), test_output_relative, { option: [ None ] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Integer".format(option), test_output_relative, { option: [ 5 ] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Integer".format(option), test_output_relative, { option: [ -5 ] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Map".format(option), test_output_relative, { option: [ {} ] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Bool".format(option), test_output_relative, { option: [ False ] })

def TEST_MAP_OF_STRINGS_OPTION(option):
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Integer".format(option), test_output_relative, { option: 5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Integer".format(option), test_output_relative, { option: -5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is String".format(option), test_output_relative, { option: "dummy" })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Array".format(option), test_output_relative, { option: [] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Bool".format(option), test_output_relative, { option: False })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Null".format(option), test_output_relative, { option: { "key": None } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Integer".format(option), test_output_relative, { option: { "key": 5 } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Integer".format(option), test_output_relative, { option: { "key": -5 } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Map".format(option), test_output_relative, { option: { "key": {} } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Bool".format(option), test_output_relative, { option: { "key": False } })

def TEST_MAP_OF_ARRAY_OF_STRINGS_OPTION(option):
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Integer".format(option), test_output_relative, { option: 5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Integer".format(option), test_output_relative, { option: -5 })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is String".format(option), test_output_relative, { option: "dummy" })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Array".format(option), test_output_relative, { option: [] })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' is expected to be of type Map, but is Bool".format(option), test_output_relative, { option: False })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' Array expected, but value is Integer".format(option), test_output_relative, { option: { "key": 5 } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' Array expected, but value is Integer".format(option), test_output_relative, { option: { "key": -5 } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' Array expected, but value is Map".format(option), test_output_relative, { option: { "key": {} } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' Array expected, but value is Bool".format(option), test_output_relative, { option: { "key": False } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Integer".format(option), test_output_relative, { option: { "key": [ 5 ] } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Integer".format(option), test_output_relative, { option: { "key": [ -5 ] } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Map".format(option), test_output_relative, { option: { "key": [ {} ] } })
    EXPECT_FAIL("TypeError", "Argument #2: Option '{0}' String expected, but value is Bool".format(option), test_output_relative, { option: { "key": [ False ] } })

def get_load_columns(options):
    decode = options["decodeColumns"] if "decodeColumns" in options else {}
    columns = []
    variables = []
    for c in options["columns"]:
        if c in decode:
            var = "@var{0}".format(len(variables))
            variables.append("{0} = {1}({2})".format(c, decode[c], var))
            columns.append(var)
        else:
            columns.append(c)
    statement = "(" + ",".join(columns) + ")"
    if variables:
        statement += " SET " + ",".join(variables)
    return statement

def get_all_columns(schema, table):
    columns = []
    for column in session.run_sql("SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION;", [schema, table]).fetch_all():
        columns.append(column[0])
    return columns

def compute_crc(schema, table, columns):
    session.run_sql("SET @crc = '';")
    session.run_sql("SELECT @crc := MD5(CONCAT_WS('#',@crc,{0})) FROM !.! ORDER BY {0};".format(("!," * len(columns))[:-1]), columns + [schema, table] + columns)
    return session.run_sql("SELECT @crc;").fetch_one()[0]

def TEST_LOAD(schema, table, where = "", partitions = [], recreate_schema = True):
    print("---> testing: `{0}`.`{1}`".format(schema, table))
    # load data
    if recreate_schema:
        recreate_verification_schema()
    EXPECT_NO_THROWS(lambda: util.load_dump(test_output_absolute, { "showProgress": False, "loadUsers": False, "includeSchemas": [ quote_identifier(schema) ], "includeTables" : [ quote_identifier(schema, table) ], "schema": verification_schema, "resetProgress": True }), "loading should not throw")
    # compute CRC
    EXPECT_EQ(md5_table(session, schema, table, where, partitions), md5_table(session, verification_schema, table))

def TEST_DUMP_AND_LOAD(schemas, options = {}):
    EXPECT_SUCCESS(schemas, test_output_absolute, options)
    where = options.get("where", {})
    partitions = options.get("partitions", {})
    recreate_verification_schema()
    for schema in schemas:
        for row in session.run_sql("SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = ? and table_type = 'BASE TABLE'", [schema]).fetch_all():
            table = row[0]
            quoted = quote_identifier(schema, table)
            TEST_LOAD(schema, table, where.get(quoted, ""), partitions.get(quoted, []), False)

#@<> WL13807-FR1.2 - an exception must be thrown if there is no global session
# WL13807-TSFR_1_17
EXPECT_FAIL("RuntimeError", "An open session is required to perform this operation.", test_output_relative)

#@<> deploy sandbox
testutil.deploy_raw_sandbox(__mysql_sandbox_port1, "root", {
    "loose_innodb_directories": filename_for_file(table_data_directory),
    "early-plugin-load": "keyring_file." + ("dll" if __os_type == "windows" else "so"),
    "keyring_file_data": filename_for_file(os.path.join(incompatible_table_directory, "keyring")),
    "log-bin": "binlog",
    "server-id": str(random.randint(1, 4294967295)),
    "enforce_gtid_consistency": "ON",
    "gtid_mode": "ON",
})

#@<> wait for server
testutil.wait_sandbox_alive(uri)
shell.connect(uri)

#@<> WL13807-FR1.2 - an exception must be thrown if there is no open global session
# WL13807-TSFR_1_16
session.close()
EXPECT_FAIL("RuntimeError", "An open session is required to perform this operation.", test_output_relative)

#@<> Setup
setup_session()

drop_all_schemas()
create_all_schemas()

create_users()

session.run_sql("CREATE TABLE !.! (`ID` int(11) NOT NULL AUTO_INCREMENT, `Name` char(64) NOT NULL DEFAULT '', `CountryCode` char(3) NOT NULL DEFAULT '', `District` char(64) NOT NULL DEFAULT '', `Info` json DEFAULT NULL, PRIMARY KEY (`ID`)) ENGINE=InnoDB AUTO_INCREMENT=4080 DEFAULT CHARSET=utf8mb4;", [ world_x_schema, world_x_table ])
util.import_table(os.path.join(__import_data_path, "world_x_cities.dump"), { "schema": world_x_schema, "table": world_x_table, "characterSet": "utf8mb4", "showProgress": False })

rc = testutil.call_mysqlsh([uri, "--sql", "--file", os.path.join(__data_path, "sql", "fieldtypes_all.sql")])
EXPECT_EQ(0, rc)

# table with primary key, unique key, generated columns
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY, `data` INT NOT NULL UNIQUE, `vdata` INT GENERATED ALWAYS AS (data + 1) VIRTUAL, `sdata` INT GENERATED ALWAYS AS (data + 2) STORED) ENGINE=InnoDB;", [ test_schema, test_table_primary ])
# table with unique key
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT NOT NULL UNIQUE, `data` INT) ENGINE=InnoDB;", [ test_schema, test_table_unique ])
# table with non-unique key
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT, `data` INT, KEY (`id`)) ENGINE=InnoDB;", [ test_schema, test_table_non_unique ])
# table without key
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT, `data` INT, `tdata` INT) ENGINE=InnoDB;", [ test_schema, test_table_no_index ])

session.run_sql("CREATE TRIGGER !.! BEFORE UPDATE ON ! FOR EACH ROW BEGIN SET NEW.tdata = NEW.data + 3; END;", [ test_schema, test_table_trigger, test_table_no_index ])

session.run_sql("""
CREATE PROCEDURE !.!()
BEGIN
  DECLARE i INT DEFAULT 1;

  WHILE i < 10000 DO
    INSERT INTO !.! (`data`) VALUES (i);
    SET i = i + 1;
  END WHILE;
END""", [ test_schema, test_schema_procedure, test_schema, test_table_primary ])

session.run_sql("CREATE FUNCTION !.!(a INT) RETURNS CHAR(12) DETERMINISTIC RETURN CONVERT(a, CHAR);", [ test_schema, test_schema_function ])

session.run_sql("CREATE VIEW !.! AS SELECT !.!(`tdata`) FROM !.!;", [ test_schema, test_view, test_schema, test_schema_function, test_schema, test_table_no_index ])

session.run_sql("CREATE EVENT !.! ON SCHEDULE EVERY 1 HOUR STARTS CURRENT_TIMESTAMP + INTERVAL 1 WEEK DO DELETE FROM !.!;", [ test_schema, test_schema_event, test_schema, test_table_no_index ])

# BUG#31820571 - events which contain string `;;` cause dump to freeze
session.run_sql("CREATE DEFINER=`root`@`localhost` EVENT !.! ON SCHEDULE AT '2020-08-28 10:53:50' ON COMPLETION PRESERVE ENABLE COMMENT '/* ;; */' DO begin end;", [ test_schema, "bug31820571" ])

session.run_sql("""INSERT INTO !.! (`data`)
SELECT (tth * 10000 + th * 1000 + h * 100 + t * 10 + u + 1) x FROM
    (SELECT 0 tth UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) E,
    (SELECT 0 th UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) D,
    (SELECT 0 h UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) C,
    (SELECT 0 t UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) B,
    (SELECT 0 u UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) A
ORDER BY x;""", [ test_schema, test_table_primary ])

session.run_sql("INSERT INTO !.! (`id`, `data`) SELECT `id`, `data` FROM !.!;", [ test_schema, test_table_unique, test_schema, test_table_primary ])
session.run_sql("INSERT INTO !.! (`id`, `data`) SELECT `id`, `data` FROM !.!;", [ test_schema, test_table_non_unique, test_schema, test_table_primary ])
# duplicate row, NULL row
session.run_sql("INSERT INTO !.! (`id`, `data`) VALUES (1, 1), (NULL, NULL);", [ test_schema, test_table_non_unique ])
session.run_sql("INSERT INTO !.! (`id`, `data`) SELECT `id`, `data` FROM !.!;", [ test_schema, test_table_no_index, test_schema, test_table_primary ])
# duplicate row, NULL row
session.run_sql("INSERT INTO !.! (`id`, `data`) VALUES (1, 1), (NULL, NULL);", [ test_schema, test_table_no_index ])

for table in [test_table_primary, test_table_unique, test_table_non_unique, test_table_no_index]:
    session.run_sql("ANALYZE TABLE !.!;", [ test_schema, table ])

#@<> schema with MySQLaaS incompatibilities
session.run_sql("ALTER DATABASE ! CHARACTER SET latin1;", [ incompatible_schema ])
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT, `data` INT) ENGINE=MyISAM DEFAULT CHARSET=latin1 ROW_FORMAT=FIXED;", [ incompatible_schema, incompatible_table_wrong_engine ])
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT, `data` INT) ENGINE=InnoDB ENCRYPTION = 'Y' DEFAULT CHARSET=latin1;", [ incompatible_schema, incompatible_table_encryption ])
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT, `data` INT) ENGINE=InnoDB DATA DIRECTORY = '{0}' DEFAULT CHARSET=latin1;".format(filename_for_file(table_data_directory)), [ incompatible_schema, incompatible_table_data_directory ])
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT, `data` INT) ENGINE=MyISAM INDEX DIRECTORY = '{0}' DEFAULT CHARSET=latin1;".format(filename_for_file(table_index_directory)), [ incompatible_schema, incompatible_table_index_directory ])
session.run_sql("CREATE TABLESPACE ! ADD DATAFILE 't_s_1.ibd' ENGINE=INNODB;", [ incompatible_tablespace ])
session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT, `data` INT) TABLESPACE ! DEFAULT CHARSET=latin1;", [ incompatible_schema, incompatible_table_tablespace, incompatible_tablespace ])
session.run_sql("CREATE VIEW !.! AS SELECT `data` FROM !.!;", [ incompatible_schema, incompatible_view, incompatible_schema, incompatible_table_wrong_engine ])

#@<> count types tables
types_schema_tables = []
types_schema_views = []

for table in session.run_sql("SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.tables WHERE TABLE_SCHEMA = ?", [types_schema]).fetch_all():
    if table[1] == "BASE TABLE":
        types_schema_tables.append(table[0])
    else:
        types_schema_views.append(table[0])

#@<> Create roles {VER(>=8.0.0)}
session.run_sql("DROP ROLE IF EXISTS ?;", [ test_role ])
session.run_sql("CREATE ROLE ?;", [ test_role ])

#@<> Analyze the table {VER(>=8.0.0)}
session.run_sql("ANALYZE TABLE !.! UPDATE HISTOGRAM ON `id`;", [ test_schema, test_table_no_index ])

#@<> WL13807-TSFR_1_3 - first parameter
EXPECT_FAIL("TypeError", "Argument #1 is expected to be a string", None)
EXPECT_FAIL("TypeError", "Argument #1 is expected to be a string", 1)
EXPECT_FAIL("TypeError", "Argument #1 is expected to be a string", [])
EXPECT_FAIL("TypeError", "Argument #1 is expected to be a string", {})
EXPECT_FAIL("TypeError", "Argument #1 is expected to be a string", False)

#@<> WL13807-TSFR_3_1 - second parameter
EXPECT_FAIL("TypeError", "Argument #2 is expected to be a map", test_output_relative, 1)
EXPECT_FAIL("TypeError", "Argument #2 is expected to be a map", test_output_relative, "string")
EXPECT_FAIL("TypeError", "Argument #2 is expected to be a map", test_output_relative, [])

#@<> WL13807-FR1.1 - The `outputUrl` parameter must be a string value which specifies the output directory, where the dump data is going to be stored.
EXPECT_SUCCESS([types_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR1.1.1 - If the dump is going to be stored on the local filesystem, the `outputUrl` parameter may be optionally prefixed with `file://` scheme.
EXPECT_SUCCESS([types_schema], "file://" + test_output_absolute, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR1.1.2 - If the dump is going to be stored on the local filesystem and the `outputUrl` parameter holds a relative path, its absolute value is computed as relative to the current working directory.
EXPECT_SUCCESS([types_schema], test_output_relative, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR1.1.2 - relative with .
EXPECT_SUCCESS([types_schema], "./" + test_output_relative, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR1.1.2 - relative with ..
EXPECT_SUCCESS([types_schema], "dummy/../" + test_output_relative, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR1.1.1 + WL13807-FR1.1.2
EXPECT_SUCCESS([types_schema], "file://" + test_output_relative, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR1.1.3 - If the output directory does not exist, it must be created if its parent directory exists. If it is not possible or parent directory does not exist, an exception must be thrown.
# parent directory does not exist
shutil.rmtree(test_output_absolute, True)
EXPECT_FALSE(os.path.isdir(test_output_absolute))
# WL14841-TSFR_4_1
EXPECT_FAIL("RuntimeError", "Could not create directory ", os.path.join(test_output_absolute, "dummy"), { "showProgress": False })
EXPECT_FALSE(os.path.isdir(test_output_absolute))

# unable to create directory, file with the same name exists
shutil.rmtree(test_output_absolute, True)
EXPECT_FALSE(os.path.isdir(test_output_absolute))
open(test_output_relative, 'a').close()
EXPECT_FAIL("RuntimeError", "Could not create directory ", test_output_absolute, { "showProgress": False })
EXPECT_FALSE(os.path.isdir(test_output_absolute))
os.remove(test_output_relative)

#@<> WL13807-FR1.1.4 - If a local directory is used and the output directory must be created, `rwxr-x---` permissions should be used on the created directory. The owner of the directory is the user running the Shell. {__os_type != "windows"}
EXPECT_SUCCESS([types_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
# get the umask value
umask = os.umask(0o777)
os.umask(umask)
# use the umask value to compute the expected access rights
EXPECT_EQ(0o750 & ~umask, stat.S_IMODE(os.stat(test_output_absolute).st_mode))
EXPECT_EQ(os.getuid(), os.stat(test_output_absolute).st_uid)

#@<> WL13807-FR1.1.5 - If the output directory exists and is not empty, an exception must be thrown.
# dump into empty directory
shutil.rmtree(test_output_absolute, True)
EXPECT_FALSE(os.path.isdir(test_output_absolute))
os.mkdir(test_output_absolute)
testutil.call_mysqlsh([uri, "--", "util", "dump-instance", test_output_absolute, "--exclude-schemas=" + ','.join(exclude_all_but_types_schema), "--ddl-only", "--show-progress=false"])
EXPECT_STDOUT_CONTAINS("Schemas dumped: 1")

#@<> dump once again to the same directory, should fail
EXPECT_THROWS(lambda: util.dump_instance(test_output_relative, { "showProgress": False }), "ValueError: Util.dump_instance: Cannot proceed with the dump, the specified directory '{0}' already exists at the target location {1} and is not empty.".format(test_output_relative, absolute_path_for_output(test_output_absolute)))

# WL13807-FR3 - Both new functions must accept the following options specified in WL#13804, FR5:
# * The `maxRate` option specified in WL#13804, FR5.1.
# * The `showProgress` option specified in WL#13804, FR5.2.
# * The `compression` option specified in WL#13804, FR5.3, with the modification of FR5.3.2, the default value must be`"zstd"`.
# * The `osBucketName` option specified in WL#13804, FR5.4.
# * The `osNamespace` option specified in WL#13804, FR5.5.
# * The `ociConfigFile` option specified in WL#13804, FR5.6.
# * The `ociProfile` option specified in WL#13804, FR5.7.
# * The `defaultCharacterSet` option specified in WL#13804, FR5.8.

#@<> WL13807-FR4.12 - The `options` dictionary may contain a `chunking` key with a Boolean value, which specifies whether to split the dump data into multiple files.
# WL13807-TSFR_3_52
TEST_BOOL_OPTION("chunking")

EXPECT_SUCCESS([test_schema], test_output_absolute, { "chunking": False, "showProgress": False })
EXPECT_FALSE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_primary) + "@"))
EXPECT_FALSE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_unique) + "@"))

#@<> WL13807-FR4.12.3 - If the `chunking` option is not given, a default value of `true` must be used instead.
WIPE_SHELL_LOG()
EXPECT_SUCCESS([test_schema], test_output_absolute, { "showProgress": False })

# WL13807-FR4.12.1 - If the `chunking` option is set to `true` and the index column cannot be selected automatically as described in FR3.1, the data must to written to a single dump file. A warning should be displayed to the user.
# WL13807-FR3.1 - For each table dumped, its index column (name of the column used to order the data and perform the chunking) must be selected automatically as the first column used in the primary key, or if there is no primary key, as the first column used in the first unique index. If the table to be dumped does not contain a primary key and does not contain an unique index, the index column will not be defined.
# WL13807-TSFR_3_521_1
# BUG#34195250 - if index column cannot be selected, table is dumped to multiple files by a single thread
EXPECT_SHELL_LOG_CONTAINS(f"Could not select columns to be used as an index for table `{test_schema}`.`{test_table_non_unique}`. Data will be dumped to multiple files by a single thread.")
EXPECT_SHELL_LOG_CONTAINS(f"Could not select columns to be used as an index for table `{test_schema}`.`{test_table_no_index}`. Data will be dumped to multiple files by a single thread.")

EXPECT_TRUE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_non_unique) + "@"))
EXPECT_TRUE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_no_index) + "@"))

# WL13807-FR4.12.2 - If the `chunking` option is set to `true` and the index column can be selected automatically as described in FR3.1, the data must to written to multiple dump files. The data is partitioned into chunks using values from the index column.
# WL13807-TSFR_3_522_1
EXPECT_TRUE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_primary) + "@"))
# WL13807-TSFR_3_522_3
EXPECT_TRUE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_unique) + "@"))
number_of_dump_files = count_files_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_primary) + "@")

#@<> WL13807-FR4.13 - The `options` dictionary may contain a `bytesPerChunk` key with a string value, which specifies the average estimated number of bytes to be written per each data dump file.
TEST_STRING_OPTION("bytesPerChunk")

EXPECT_SUCCESS([test_schema], test_output_absolute, { "bytesPerChunk": "128k", "showProgress": False })

# WL13807-FR4.13.1 - If the `bytesPerChunk` option is given, it must implicitly set the `chunking` option to `true`.
# WL13807-TSFR_3_531_1
EXPECT_TRUE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_primary) + "@"))
EXPECT_TRUE(has_file_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_unique) + "@"))

# WL13807-FR4.13.4 - If the `bytesPerChunk` option is not given and the `chunking` option is set to `true`, a default value of `256M` must be used instead.
# this dump used smaller chunk size, number of files should be greater
EXPECT_TRUE(count_files_with_basename(test_output_absolute, encode_table_basename(test_schema, test_table_primary) + "@") > number_of_dump_files)

#@<> WL13807-FR4.13.2 - The value of the `bytesPerChunk` option must use the same format as specified in WL#12193.
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "xyz"', test_output_absolute, { "bytesPerChunk": "xyz" })
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "1xyz"', test_output_absolute, { "bytesPerChunk": "1xyz" })
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "2Mhz"', test_output_absolute, { "bytesPerChunk": "2Mhz" })
# WL13807-TSFR_3_532_3
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "0.1k"', test_output_absolute, { "bytesPerChunk": "0.1k" })
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "0,3M"', test_output_absolute, { "bytesPerChunk": "0,3M" })
EXPECT_FAIL("ValueError", 'Argument #2: Input number "-1G" cannot be negative', test_output_absolute, { "bytesPerChunk": "-1G" })
EXPECT_FAIL("ValueError", "Argument #2: The option 'bytesPerChunk' cannot be set to an empty string.", test_output_absolute, { "bytesPerChunk": "" })
# WL13807-TSFR_3_532_2
EXPECT_FAIL("ValueError", "Argument #2: The option 'bytesPerChunk' cannot be used if the 'chunking' option is set to false.", test_output_absolute, { "bytesPerChunk": "128k", "chunking": False })

#@<> WL13807-TSFR_3_532_1
EXPECT_SUCCESS([types_schema], test_output_absolute, { "bytesPerChunk": "1000k", "ddlOnly": True, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "bytesPerChunk": "1M", "ddlOnly": True, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "bytesPerChunk": "1G", "ddlOnly": True, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "bytesPerChunk": "128000", "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR4.13.3 - If the value of the `bytesPerChunk` option is smaller than `128k`, an exception must be thrown.
# WL13807-TSFR_3_533_1
EXPECT_FAIL("ValueError", "Argument #2: The value of 'bytesPerChunk' option must be greater than or equal to 128k.", test_output_relative, { "bytesPerChunk": "127k" })
EXPECT_FAIL("ValueError", "Argument #2: The value of 'bytesPerChunk' option must be greater than or equal to 128k.", test_output_relative, { "bytesPerChunk": "127999" })
EXPECT_FAIL("ValueError", "Argument #2: The value of 'bytesPerChunk' option must be greater than or equal to 128k.", test_output_relative, { "bytesPerChunk": "1" })
EXPECT_FAIL("ValueError", "Argument #2: The value of 'bytesPerChunk' option must be greater than or equal to 128k.", test_output_relative, { "bytesPerChunk": "0" })
EXPECT_FAIL("ValueError", 'Argument #2: Input number "-1" cannot be negative', test_output_relative, { "bytesPerChunk": "-1" })

#@<> WL13807-FR4.14 - The `options` dictionary may contain a `threads` key with an unsigned integer value, which specifies the number of threads to be used to perform the dump.
# WL13807-TSFR_3_54
TEST_UINT_OPTION("threads")

# WL13807-TSFR_3_54_1
EXPECT_SUCCESS([types_schema], test_output_absolute, { "threads": 2, "ddlOnly": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS("Running data dump using 2 threads.")

#@<> WL13807-FR4.14.1 - If the value of the `threads` option is set to `0`, an exception must be thrown.
# WL13807-TSFR_3_54
EXPECT_FAIL("ValueError", "Argument #2: The value of 'threads' option must be greater than 0.", test_output_relative, { "threads": 0 })

#@<> WL13807-FR4.14.2 - If the `threads` option is not given, a default value of `4` must be used instead.
# WL13807-TSFR_3_542
EXPECT_SUCCESS([types_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS("Running data dump using 4 threads.")

#@<> WL13807: WL13804-FR5.1 - The `options` dictionary may contain a `maxRate` key with a string value, which specifies the limit of data read throughput in bytes per second per thread.
TEST_STRING_OPTION("maxRate")

# WL13807-TSFR_3_551_1
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1", "ddlOnly": True, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1000k", "ddlOnly": True, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1000K", "ddlOnly": True, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1M", "ddlOnly": True, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1G", "ddlOnly": True, "showProgress": False })

#@<> WL13807: WL13804-FR5.1.1 - The value of the `maxRate` option must use the same format as specified in WL#12193.
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "xyz"', test_output_absolute, { "maxRate": "xyz" })
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "1xyz"', test_output_absolute, { "maxRate": "1xyz" })
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "2Mhz"', test_output_absolute, { "maxRate": "2Mhz" })
# WL13807-TSFR_3_552
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "hello world!"', test_output_absolute, { "maxRate": "hello world!" })
EXPECT_FAIL("ValueError", 'Argument #2: Input number "-1" cannot be negative', test_output_absolute, { "maxRate": "-1" })
EXPECT_FAIL("ValueError", 'Argument #2: Input number "-1234567890123456" cannot be negative', test_output_absolute, { "maxRate": "-1234567890123456" })
EXPECT_FAIL("ValueError", 'Argument #2: Input number "-2K" cannot be negative', test_output_absolute, { "maxRate": "-2K" })
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "3m"', test_output_absolute, { "maxRate": "3m" })
EXPECT_FAIL("ValueError", 'Argument #2: Wrong input number "4g"', test_output_absolute, { "maxRate": "4g" })

EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1000000", "ddlOnly": True, "showProgress": False })

#@<> WL13807: WL13804-FR5.1.1 - kilo.
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1000k", "ddlOnly": True, "showProgress": False })

#@<> WL13807: WL13804-FR5.1.1 - giga.
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "1G", "ddlOnly": True, "showProgress": False })

#@<> WL13807: WL13804-FR5.1.2 - If the `maxRate` option is set to `"0"` or to an empty string, the read throughput must not be limited.
# WL13807-TSFR_3_552
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "0", "ddlOnly": True, "showProgress": False })

#@<> WL13807: WL13804-FR5.1.2 - empty string.
# WL13807-TSFR_3_552
EXPECT_SUCCESS([types_schema], test_output_absolute, { "maxRate": "", "ddlOnly": True, "showProgress": False })

#@<> WL13807: WL13804-FR5.1.2 - missing.
# WL13807-TSFR_3_552
EXPECT_SUCCESS([types_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

#@<> WL13807: WL13804-FR5.2 - The `options` dictionary may contain a `showProgress` key with a Boolean value, which specifies whether to display the progress of dump process.
TEST_BOOL_OPTION("showProgress")

EXPECT_SUCCESS([types_schema], test_output_absolute, { "showProgress": True, "ddlOnly": True })

#@<> WL13807: WL13804-FR5.2.1 - The information about the progress must include:
# * The estimated total number of rows to be dumped.
# * The number of rows dumped so far.
# * The current progress as a percentage.
# * The current throughput in rows per second.
# * The current throughput in bytes written per second.
shutil.rmtree(test_output_absolute, True)
EXPECT_FALSE(os.path.isdir(test_output_absolute))
rc = testutil.call_mysqlsh([uri, "--", "util", "dump-instance", test_output_relative, "--showProgress", "true"])
EXPECT_EQ(0, rc)
EXPECT_TRUE(os.path.isdir(test_output_absolute))
EXPECT_STDOUT_MATCHES(re.compile(r'\d+% \(\d+\.?\d*[TGMK]? rows / ~\d+\.?\d*[TGMK]? rows\), \d+\.?\d*[TGMK]? rows?/s, \d+\.?\d* [TGMK]?B/s', re.MULTILINE))

#@<> Bug #31829337 - IMPROVE USABILITY OF DUMP OPERATIONS IN CLI: LIST PARAMETERS NOT SUPPORTED
shutil.rmtree(test_output_absolute, True)
EXPECT_FALSE(os.path.isdir(test_output_absolute))
WIPE_SHELL_LOG()
rc = testutil.call_mysqlsh([uri, "--", "util", "dump-instance", test_output_relative, "--showProgress", "true", "--excludeTables=xtest.t_decimal1,xtest.t_decimal3", "--chunking=false"])
EXPECT_EQ(0, rc)
EXPECT_TRUE(os.path.isdir(test_output_absolute))
EXPECT_SHELL_LOG_NOT_CONTAINS("Data dump for table `xtest`.`t_decimal1` will be written to 1 file")
EXPECT_SHELL_LOG_CONTAINS("Data dump for table `xtest`.`t_decimal2` will be written to 1 file")
EXPECT_SHELL_LOG_NOT_CONTAINS("Data dump for table `xtest`.`t_decimal3` will be written to 1 file")
EXPECT_STDOUT_MATCHES(re.compile(r'\d+% \(\d+\.?\d*[TGMK]? rows / ~\d+\.?\d*[TGMK]? rows\), \d+\.?\d*[TGMK]? rows?/s, \d+\.?\d* [TGMK]?B/s', re.MULTILINE))

#@<> WL13807: WL13804-FR5.2.2 - If the `showProgress` option is not given, a default value of `true` must be used instead if shell is used interactively. Otherwise, it is set to `false`.
shutil.rmtree(test_output_absolute, True)
EXPECT_FALSE(os.path.isdir(test_output_absolute))
rc = testutil.call_mysqlsh([uri, "--", "util", "dump-instance", test_output_relative])
EXPECT_EQ(0, rc)
EXPECT_TRUE(os.path.isdir(test_output_absolute))
EXPECT_STDOUT_NOT_CONTAINS("rows/s")

#@<> WL13807: WL13804-FR5.3 - The `options` dictionary may contain a `compression` key with a string value, which specifies the compression type used when writing the data dump files.
# WL13807-TSFR_3_57
# WL13807-TSFR_3_571_1
TEST_STRING_OPTION("compression")

# WL13807-TSFR_3_571_2
EXPECT_SUCCESS([types_schema], test_output_absolute, { "compression": "none", "chunking": False, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(types_schema, types_schema_tables[0]) + ".tsv")))

#@<> WL13807: WL13804-FR5.3.1 - The allowed values for the `compression` option are:
# * `"none"` - no compression is used,
# * `"gzip"` - gzip compression is used.
# * `"zstd"` - zstd compression is used.
# WL13807-TSFR_3_571_3
EXPECT_SUCCESS([types_schema], test_output_absolute, { "compression": "gzip", "chunking": False, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(types_schema, types_schema_tables[0]) + ".tsv.gz")))

EXPECT_FAIL("ValueError", "Argument #2: The option 'compression' cannot be set to an empty string.", test_output_relative, { "compression": "" })
EXPECT_FAIL("ValueError", "Argument #2: Unknown compression type: dummy", test_output_relative, { "compression": "dummy" })

EXPECT_SUCCESS([types_schema], test_output_absolute, { "compression": "zstd", "chunking": False, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(types_schema, types_schema_tables[0]) + ".tsv.zst")))

#@<> WL13807: WL13804-FR5.3.2 - If the `compression` option is not given, a default value of `"none"` must be used instead.
# WL13807-FR3 - Both new functions must accept the following options specified in WL#13804, FR5:
# * The `compression` option specified in WL#13804, FR5.3, with the modification of FR5.3.2, the default value must be`"zstd"`.
# WL13807-TSFR_3_572_1
EXPECT_SUCCESS([types_schema], test_output_absolute, { "chunking": False, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(types_schema, types_schema_tables[0]) + ".tsv.zst")))

#@<> WL13807: WL13804-FR5.4 - The `options` dictionary may contain a `osBucketName` key with a string value, which specifies the OCI bucket name where the data dump files are going to be stored.
# WL13807-TSFR_3_58
TEST_STRING_OPTION("osBucketName")

#@<> WL13807: WL13804-FR5.5 - The `options` dictionary may contain a `osNamespace` key with a string value, which specifies the OCI namespace (tenancy name) where the OCI bucket is located.
# WL13807-TSFR_3_59
TEST_STRING_OPTION("osNamespace")

#@<> WL13807: WL13804-FR5.5.2 - If the value of `osNamespace` option is a non-empty string and the value of `osBucketName` option is an empty string, an exception must be thrown.
# WL13807-TSFR_3_592_1
EXPECT_FAIL("ValueError", "Argument #2: The option 'osNamespace' cannot be used when the value of 'osBucketName' option is not set.", test_output_relative, { "osNamespace": "namespace" })

#@<> WL13807: WL13804-FR5.6 - The `options` dictionary may contain a `ociConfigFile` key with a string value, which specifies the path to the OCI configuration file.
# WL13807-TSFR_3_510_1
TEST_STRING_OPTION("ociConfigFile")

#@<> WL13807: WL13804-FR5.6.2 - If the value of `ociConfigFile` option is a non-empty string and the value of `osBucketName` option is an empty string, an exception must be thrown.
# WL13807-TSFR_3_5102
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociConfigFile' cannot be used when the value of 'osBucketName' option is not set.", test_output_relative, { "ociConfigFile": "config" })

#@<> WL13807: WL13804-FR5.7 - The `options` dictionary may contain a `ociProfile` key with a string value, which specifies the name of the OCI profile to use.
TEST_STRING_OPTION("ociProfile")

#@<> WL13807: WL13804-FR5.7.2 - If the value of `ociProfile` option is a non-empty string and the value of `osBucketName` option is an empty string, an exception must be thrown.
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociProfile' cannot be used when the value of 'osBucketName' option is not set", test_output_relative, { "ociProfile": "profile" })

#@<> WL14154: WL14154-TSFR1_2 - Validate that the option ociParManifest only take boolean values as valid values.
TEST_BOOL_OPTION("ociParManifest")

#@<> WL14154: WL14154-TSFR1_3 - Validate that the option ociParManifest is valid only when doing a dump to OCI.
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociParManifest' cannot be used when the value of 'osBucketName' option is not set.", test_output_relative, { "ociParManifest": True })
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociParManifest' cannot be used when the value of 'osBucketName' option is not set.", test_output_relative, { "ociParManifest": False })

#@<> WL14154: WL14154-TSFR2_12 - Doing a dump to file system with ociParManifest set to True and ociParExpireTime set to a valid value. Validate that dump fails because ociParManifest is not valid if osBucketName is not specified.
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociParManifest' cannot be used when the value of 'osBucketName' option is not set.", test_output_relative, { "ociParManifest": True, "ociParExpireTime": "2021-01-01" })

#@<> WL14154: WL14154-TSFR2_2 - Validate that the option ociParExpireTime only take string values
TEST_STRING_OPTION("ociParExpireTime")

#@<> WL14154: WL14154-TSFR2_6 - Doing a dump to OCI ociParManifest not set or set to False and ociParExpireTime set to a valid value. Validate that the dump fail because ociParExpireTime it's valid only when ociParManifest is set to True.
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociParExpireTime' cannot be used when the value of 'ociParManifest' option is not True.", test_output_relative, { "ociParExpireTime": "2021-01-01" })
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociParExpireTime' cannot be used when the value of 'ociParManifest' option is not True.", test_output_relative, { "osBucketName": "bucket", "ociParExpireTime": "2021-01-01" })
EXPECT_FAIL("ValueError", "Argument #2: The option 'ociParExpireTime' cannot be used when the value of 'ociParManifest' option is not True.", test_output_relative, { "osBucketName": "bucket", "ociParManifest": False, "ociParExpireTime": "2021-01-01" })

#@<> WL13807: WL13804-FR5.8 - The `options` dictionary may contain a `defaultCharacterSet` key with a string value, which specifies the character set to be used during the dump. The session variables `character_set_client`, `character_set_connection`, and `character_set_results` must be set to this value for each opened connection.
# WL13807-TSFR4_43
TEST_STRING_OPTION("defaultCharacterSet")

#@<> WL13807-TSFR4_40
EXPECT_SUCCESS([test_schema], test_output_absolute, { "defaultCharacterSet": "utf8mb4", "ddlOnly": True, "showProgress": False })
# name should be correctly encoded using UTF-8
EXPECT_FILE_CONTAINS("CREATE TABLE IF NOT EXISTS `{0}`".format(test_table_non_unique), os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_non_unique) + ".sql"))

#@<> WL13807: WL13804-FR5.8.1 - If the value of the `defaultCharacterSet` option is not a character set supported by the MySQL server, an exception must be thrown.
# WL13807-TSFR4_41
# WL14841-TSFR_4_1
EXPECT_FAIL("MySQL Error (1115)", "Unknown character set: ''", test_output_relative, { "defaultCharacterSet": "" })
EXPECT_FAIL("MySQL Error (1115)", "Unknown character set: 'dummy'", test_output_relative, { "defaultCharacterSet": "dummy" })

#@<> WL13807: WL13804-FR5.8.2 - If the `defaultCharacterSet` option is not given, a default value of `"utf8mb4"` must be used instead.
# WL13807-TSFR4_39
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
# name should be correctly encoded using UTF-8
EXPECT_FILE_CONTAINS("CREATE TABLE IF NOT EXISTS `{0}`".format(test_table_non_unique), os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_non_unique) + ".sql"))

#@<> WL15311_TSFR_5_1
help_text = """
      - fieldsTerminatedBy: string (default: "\\t") - This option has the same
        meaning as the corresponding clause for SELECT ... INTO OUTFILE.
      - fieldsEnclosedBy: char (default: '') - This option has the same meaning
        as the corresponding clause for SELECT ... INTO OUTFILE.
      - fieldsEscapedBy: char (default: '\\') - This option has the same meaning
        as the corresponding clause for SELECT ... INTO OUTFILE.
      - fieldsOptionallyEnclosed: bool (default: false) - Set to true if the
        input values are not necessarily enclosed within quotation marks
        specified by fieldsEnclosedBy option. Set to false if all fields are
        quoted by character specified by fieldsEnclosedBy option.
      - linesTerminatedBy: string (default: "\\n") - This option has the same
        meaning as the corresponding clause for SELECT ... INTO OUTFILE. See
        Section 13.2.10.1, "SELECT ... INTO Statement".
      - dialect: enum (default: "default") - Setup fields and lines options
        that matches specific data file format. Can be used as base dialect and
        customized with fieldsTerminatedBy, fieldsEnclosedBy, fieldsEscapedBy,
        fieldsOptionallyEnclosed and linesTerminatedBy options. Must be one of
        the following values: default, csv, tsv or csv-unix.
"""
EXPECT_TRUE(help_text in util.help("dump_instance"))

#@<> WL15311 - option types
TEST_STRING_OPTION("fieldsTerminatedBy")
TEST_STRING_OPTION("fieldsEnclosedBy")
TEST_STRING_OPTION("fieldsEscapedBy")
TEST_BOOL_OPTION("fieldsOptionallyEnclosed")
TEST_STRING_OPTION("linesTerminatedBy")
TEST_STRING_OPTION("dialect")

#@<> WL15311_TSFR_5_1_1, WL15311_TSFR_5_2_1 - various predefined dialects and their extensions
for dialect, ext in { "default": "tsv", "csv": "csv", "tsv": "tsv", "csv-unix": "csv" }.items():
    TEST_DUMP_AND_LOAD([types_schema], { "dialect": dialect })
    EXPECT_TRUE(count_files_with_extension(test_output_relative, f".{ext}.zst") > 0)

#@<> WL15311 - The JSON dialect must not be supported.
EXPECT_FAIL("ValueError", "Argument #2: The 'json' dialect is not supported.", test_output_relative, { "dialect": "json" })

#@<> WL15311_TSFR_5_3_1 - custom dialect
TEST_DUMP_AND_LOAD([types_schema], { "fieldsTerminatedBy": "a", "fieldsEnclosedBy": "b", "fieldsEscapedBy": "c", "linesTerminatedBy": "d", "fieldsOptionallyEnclosed": True })
EXPECT_TRUE(count_files_with_extension(test_output_relative, ".txt.zst") > 0)

#@<> WL15311_TSFR_5_2, WL15311_TSFR_5_3, WL15311_TSFR_5_4, WL15311_TSFR_5_5, WL15311_TSFR_5_6 - more custom dialects
custom_dialect_schema = "wl15311_tsfr_5"
custom_dialect_table = "x"

session.run_sql("CREATE SCHEMA !;", [ custom_dialect_schema ])
session.run_sql("CREATE TABLE !.! (id int primary key AUTO_INCREMENT, p text, q text);", [ custom_dialect_schema, custom_dialect_table ])
session.run_sql("INSERT INTO !.! VALUES (1, 'aaaaaa', 'bbbbb'), (2, 'aabbaaaa', 'bbaabbb'), (3, 'aabbaababaaa', 'bbaabbababbabab');", [ custom_dialect_schema, custom_dialect_table ])

for i in range(10):
    session.run_sql("INSERT INTO !.! (p, q) SELECT p, q FROM !.!;", [ custom_dialect_schema, custom_dialect_table, custom_dialect_schema, custom_dialect_table ])

session.run_sql("ANALYZE TABLE !.!;", [ custom_dialect_schema, custom_dialect_table ])

all_schemas.append(custom_dialect_schema)

TEST_DUMP_AND_LOAD([ custom_dialect_schema ])
TEST_DUMP_AND_LOAD([ custom_dialect_schema ], { "fieldsTerminatedBy": "a" })
TEST_DUMP_AND_LOAD([ custom_dialect_schema ], { "linesTerminatedBy": "a" })
TEST_DUMP_AND_LOAD([ custom_dialect_schema ], { "fieldsEnclosedBy": '"', "fieldsOptionallyEnclosed": False , "linesTerminatedBy": "a"})
TEST_DUMP_AND_LOAD([ custom_dialect_schema ], { "fieldsEnclosedBy": '"', "fieldsOptionallyEnclosed": False , "linesTerminatedBy": "ab"})

all_schemas.pop()
session.run_sql("DROP SCHEMA !;", [ custom_dialect_schema ])

#@<> WL15311 - fixed-row format is not supported yet
EXPECT_FAIL("ValueError", "Argument #2: The fieldsTerminatedBy and fieldsEnclosedBy are both empty, resulting in a fixed-row format. This is currently not supported.", test_output_absolute, { "fieldsTerminatedBy": "", "fieldsEnclosedBy": "" })

#@<> WL14387-TSFR_1_1_1 - s3BucketName - string option
TEST_STRING_OPTION("s3BucketName")

#@<> WL14387-TSFR_1_2_1 - s3BucketName and osBucketName cannot be used at the same time
EXPECT_FAIL("ValueError", "Argument #2: The option 's3BucketName' cannot be used when the value of 'osBucketName' option is set", test_output_relative, { "s3BucketName": "one", "osBucketName": "two" })

#@<> WL14387-TSFR_1_1_3 - s3BucketName set to an empty string dumps to a local directory
EXPECT_SUCCESS([types_schema], test_output_absolute, { "s3BucketName": "", "showProgress": False })

#@<> s3CredentialsFile - string option
TEST_STRING_OPTION("s3CredentialsFile")

#@<> WL14387-TSFR_3_1_1_1 - s3CredentialsFile cannot be used without s3BucketName
EXPECT_FAIL("ValueError", "Argument #2: The option 's3CredentialsFile' cannot be used when the value of 's3BucketName' option is not set", test_output_relative, { "s3CredentialsFile": "file" })

#@<> s3BucketName and s3CredentialsFile both set to an empty string dumps to a local directory
EXPECT_SUCCESS([types_schema], test_output_absolute, { "s3BucketName": "", "s3CredentialsFile": "", "showProgress": False })

#@<> s3ConfigFile - string option
TEST_STRING_OPTION("s3ConfigFile")

#@<> WL14387-TSFR_4_1_1_1 - s3ConfigFile cannot be used without s3BucketName
EXPECT_FAIL("ValueError", "Argument #2: The option 's3ConfigFile' cannot be used when the value of 's3BucketName' option is not set", test_output_relative, { "s3ConfigFile": "file" })

#@<> s3BucketName and s3ConfigFile both set to an empty string dumps to a local directory
EXPECT_SUCCESS([types_schema], test_output_absolute, { "s3BucketName": "", "s3ConfigFile": "", "showProgress": False })

#@<> WL14387-TSFR_2_1_1 - s3Profile - string option
TEST_STRING_OPTION("s3Profile")

#@<> WL14387-TSFR_2_1_1_2 - s3Profile cannot be used without s3BucketName
EXPECT_FAIL("ValueError", "Argument #2: The option 's3Profile' cannot be used when the value of 's3BucketName' option is not set", test_output_relative, { "s3Profile": "profile" })

#@<> WL14387-TSFR_2_1_2_1 - s3BucketName and s3Profile both set to an empty string dumps to a local directory
EXPECT_SUCCESS([types_schema], test_output_absolute, { "s3BucketName": "", "s3Profile": "", "showProgress": False })

#@<> s3Region - string option
TEST_STRING_OPTION("s3Region")

#@<> s3Region cannot be used without s3BucketName
EXPECT_FAIL("ValueError", "Argument #2: The option 's3Region' cannot be used when the value of 's3BucketName' option is not set", test_output_relative, { "s3Region": "region" })

#@<> s3BucketName and s3Region both set to an empty string dumps to a local directory
EXPECT_SUCCESS([types_schema], test_output_absolute, { "s3BucketName": "", "s3Region": "", "showProgress": False })

#@<> s3EndpointOverride - string option
TEST_STRING_OPTION("s3EndpointOverride")

#@<> WL14387-TSFR_6_1_1 - s3EndpointOverride cannot be used without s3BucketName
EXPECT_FAIL("ValueError", "Argument #2: The option 's3EndpointOverride' cannot be used when the value of 's3BucketName' option is not set", test_output_relative, { "s3EndpointOverride": "http://example.org" })

#@<> s3BucketName and s3EndpointOverride both set to an empty string dumps to a local directory
EXPECT_SUCCESS([types_schema], test_output_absolute, { "s3BucketName": "", "s3EndpointOverride": "", "showProgress": False })

#@<> s3EndpointOverride is missing a scheme
EXPECT_FAIL("ValueError", "Argument #2: The value of the option 's3EndpointOverride' is missing a scheme, expected: http:// or https://.", test_output_absolute, { "s3BucketName": "bucket", "s3EndpointOverride": "endpoint", "showProgress": False })

#@<> s3EndpointOverride is using wrong scheme
EXPECT_FAIL("ValueError", "Argument #2: The value of the option 's3EndpointOverride' uses an invalid scheme 'FTp://', expected: http:// or https://.", test_output_absolute, { "s3BucketName": "bucket", "s3EndpointOverride": "FTp://endpoint", "showProgress": False })

#@<> WL13807-TSFR_3_2 - options param being a dictionary that contains an unknown key
for param in { "dummy", "indexColumn" }:
    EXPECT_FAIL("ValueError", f"Argument #2: Invalid options: {param}", test_output_relative, { param: "fails" })

# WL13807-FR4 - Both new functions must accept a set of additional options:

#@<> WL13807-FR4.1 - The `options` dictionary may contain a `consistent` key with a Boolean value, which specifies whether the data from the tables should be dumped consistently.
TEST_BOOL_OPTION("consistent")

EXPECT_SUCCESS([types_schema], test_output_absolute, { "consistent": False, "showProgress": False })

#@<> BUG#34556560 - skipConsistencyChecks options
TEST_BOOL_OPTION("skipConsistencyChecks")

#@<> WL13807-FR4.3 - The `options` dictionary may contain a `events` key with a Boolean value, which specifies whether to include events in the DDL file of each schema.
TEST_BOOL_OPTION("events")

EXPECT_SUCCESS([test_schema], test_output_absolute, { "events": False, "ddlOnly": True, "showProgress": False })
EXPECT_FILE_CONTAINS("CREATE DATABASE /*!32312 IF NOT EXISTS*/ `{0}`".format(test_schema), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
EXPECT_FILE_NOT_CONTAINS("CREATE DEFINER=`{0}`@`{1}` EVENT IF NOT EXISTS `{2}`".format(__user, __host, test_schema_event), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))

EXPECT_STDOUT_MATCHES(re.compile(r'1 out of \d+ schemas will be dumped and within them 4 tables, 1 view, 2 routines, 1 trigger\.'))

#@<> WL13807-FR4.3.1 - If the `events` option is not given, a default value of `true` must be used instead.
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_FILE_CONTAINS("CREATE DEFINER=`{0}`@`{1}` EVENT IF NOT EXISTS `{2}`".format(__user, __host, test_schema_event), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
EXPECT_FILE_CONTAINS("CREATE DEFINER=`root`@`localhost` EVENT IF NOT EXISTS `bug31820571`", os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))

#@<> BUG#33396153 - dumpInstance() + events
EXPECT_SUCCESS([test_schema], test_output_absolute, { "excludeEvents": [ f"`{test_schema}`.`{test_schema_event}`" ], "dryRun": True, "showProgress": False })
EXPECT_STDOUT_MATCHES(re.compile(r'1 out of \d+ schemas will be dumped and within them 4 tables, 1 view, 1 out of 2 events, 2 routines, 1 trigger\.'))

#@<> WL13807-FR4.4 - The `options` dictionary may contain a `routines` key with a Boolean value, which specifies whether to include functions and stored procedures in the DDL file of each schema. User-defined functions must not be included.
TEST_BOOL_OPTION("routines")

EXPECT_SUCCESS([test_schema], test_output_absolute, { "routines": False, "ddlOnly": True, "showProgress": False })
EXPECT_FILE_CONTAINS("CREATE DATABASE /*!32312 IF NOT EXISTS*/ `{0}`".format(test_schema), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
EXPECT_FILE_NOT_CONTAINS("CREATE DEFINER=`{0}`@`{1}` PROCEDURE `{2}`".format(__user, __host, test_schema_procedure), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
EXPECT_FILE_NOT_CONTAINS("CREATE DEFINER=`{0}`@`{1}` FUNCTION `{2}`".format(__user, __host, test_schema_function), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))

EXPECT_STDOUT_MATCHES(re.compile(r'1 out of \d+ schemas will be dumped and within them 4 tables, 1 view, 2 events, 1 trigger\.'))

#@<> WL13807-FR4.4.1 - If the `routines` option is not given, a default value of `true` must be used instead.
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_FILE_CONTAINS("CREATE DEFINER=`{0}`@`{1}` PROCEDURE `{2}`".format(__user, __host, test_schema_procedure), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
EXPECT_FILE_CONTAINS("CREATE DEFINER=`{0}`@`{1}` FUNCTION `{2}`".format(__user, __host, test_schema_function), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))

#@<> BUG#33396153 - dumpInstance() + routines
EXPECT_SUCCESS([test_schema], test_output_absolute, { "excludeRoutines": [ f"`{test_schema}`.`{test_schema_procedure}`" ], "dryRun": True, "showProgress": False })
EXPECT_STDOUT_MATCHES(re.compile(r'1 out of \d+ schemas will be dumped and within them 4 tables, 1 view, 2 events, 1 out of 2 routines, 1 trigger\.'))

#@<> WL13807-FR4.5 - The `options` dictionary may contain a `triggers` key with a Boolean value, which specifies whether to include triggers in the DDL file of each table.
# WL13807-TSFR4_15
TEST_BOOL_OPTION("triggers")

# WL13807-TSFR4_14
# WL13807-TSFR10_5
EXPECT_SUCCESS([test_schema], test_output_absolute, { "triggers": False, "ddlOnly": True, "showProgress": False })
EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_no_index) + ".triggers.sql")))

EXPECT_STDOUT_MATCHES(re.compile(r'1 out of \d+ schemas will be dumped and within them 4 tables, 1 view, 2 events, 2 routines\.'))

#@<> WL13807-FR4.5.1 - If the `triggers` option is not given, a default value of `true` must be used instead.
# WL13807-TSFR4_13
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_no_index) + ".triggers.sql")))

#@<> BUG#33396153 - dumpInstance() + triggers
EXPECT_SUCCESS([test_schema], test_output_absolute, { "excludeTriggers": [ f"`{test_schema}`.`{test_table_no_index}`" ], "dryRun": True, "showProgress": False })
EXPECT_STDOUT_MATCHES(re.compile(r'1 out of \d+ schemas will be dumped and within them 4 tables, 1 view, 2 events, 2 routines, 0 out of 1 trigger\.'))

#@<> WL13807-FR4.6 - The `options` dictionary may contain a `tzUtc` key with a Boolean value, which specifies whether to set the time zone to UTC and include a `SET TIME_ZONE='+00:00'` statement in the DDL files and to execute this statement before the data dump is started. This allows dumping TIMESTAMP data when a server has data in different time zones or data is being moved between servers with different time zones.
# WL13807-TSFR4_18
TEST_BOOL_OPTION("tzUtc")

# WL13807-TSFR4_17
EXPECT_SUCCESS([test_schema], test_output_absolute, { "tzUtc": False, "ddlOnly": True, "showProgress": False })
with open(os.path.join(test_output_absolute, "@.json"), encoding="utf-8") as json_file:
    EXPECT_FALSE(json.load(json_file)["tzUtc"])

#@<> WL13807-FR4.6.1 - If the `tzUtc` option is not given, a default value of `true` must be used instead.
# WL13807-TSFR4_16
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
with open(os.path.join(test_output_absolute, "@.json"), encoding="utf-8") as json_file:
    EXPECT_TRUE(json.load(json_file)["tzUtc"])

#@<> WL13807-FR4.7 - The `options` dictionary may contain a `ddlOnly` key with a Boolean value, which specifies whether the data dump should be skipped.
# WL13807-TSFR4_21
TEST_BOOL_OPTION("ddlOnly")

# WL13807-FR4.7.1 - If the `ddlOnly` option is set to `true`, only the DDL files must be written.
# WL13807-TSFR4_20
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_EQ(0, count_files_with_extension(test_output_absolute, ".zst"))
EXPECT_NE(0, count_files_with_extension(test_output_absolute, ".sql"))

#@<> WL13807-FR4.7.2 - If the `ddlOnly` option is not given, a default value of `false` must be used instead.
# WL13807-TSFR4_19
EXPECT_SUCCESS([test_schema], test_output_absolute, { "showProgress": False })
EXPECT_NE(0, count_files_with_extension(test_output_absolute, ".zst"))
EXPECT_NE(0, count_files_with_extension(test_output_absolute, ".sql"))

#@<> WL13807-FR4.8 - The `options` dictionary may contain a `dataOnly` key with a Boolean value, which specifies whether the DDL files should be written.
# WL13807-TSFR4_24
TEST_BOOL_OPTION("dataOnly")

# WL13807-FR4.8.1 - If the `dataOnly` option is set to `true`, only the data dump files must be written.
# WL13807-TSFR4_23
EXPECT_SUCCESS([test_schema], test_output_absolute, { "dataOnly": True, "showProgress": False })
EXPECT_NE(0, count_files_with_extension(test_output_absolute, ".zst"))
# WL13807-TSFR9_2
# WL13807-TSFR10_2
# WL13807-TSFR11_2
EXPECT_EQ(0, count_files_with_extension(test_output_absolute, ".sql"))

#@<> WL13807-FR4.8.2 - If both `ddlOnly` and `dataOnly` options are set to `true`, an exception must be raised.
# WL13807-TSFR4_25
EXPECT_FAIL("ValueError", "Argument #2: The 'ddlOnly' and 'dataOnly' options cannot be both set to true.", test_output_relative, { "ddlOnly": True, "dataOnly": True })

#@<> WL13807-FR4.8.3 - If the `dataOnly` option is not given, a default value of `false` must be used instead.
# WL13807-TSFR4_22
EXPECT_SUCCESS([test_schema], test_output_absolute, { "showProgress": False })
EXPECT_NE(0, count_files_with_extension(test_output_absolute, ".zst"))
EXPECT_NE(0, count_files_with_extension(test_output_absolute, ".sql"))

#@<> WL13807-FR4.9 - The `options` dictionary may contain a `dryRun` key with a Boolean value, which specifies whether a dry run should be performed.
# WL13807-TSFR4_28
TEST_BOOL_OPTION("dryRun")

# WL13807-FR4.9.1 - If the `dryRun` option is set to `true`, Shell must print information about what would be performed/dumped, including the compatibility notes for `ocimds` if available, but do not dump anything.
# WL13807-TSFR4_27
shutil.rmtree(test_output_absolute, True)
EXPECT_FALSE(os.path.isdir(test_output_absolute))
# BUG#32695301 - lock one of the tables, dry run should not attempt to execute FLUSH TABLES WITH READ LOCK and dump should succeed
session.run_sql("LOCK TABLES !.! WRITE", [ test_schema, test_table_unique ])
testutil.call_mysqlsh([uri, "--", "util", "dump-instance", test_output_absolute, "--dry-run", "--show-progress=false"])
EXPECT_FALSE(os.path.isdir(test_output_absolute))
EXPECT_STDOUT_NOT_CONTAINS("Schemas dumped: ")
EXPECT_STDOUT_CONTAINS("dryRun enabled, no locks will be acquired and no files will be created.")
# BUG#32695301 - unlock the tables
session.run_sql("UNLOCK TABLES")

#@<> WL13807-FR4.9.2 - If the `dryRun` option is not given, a default value of `false` must be used instead.
# WL13807-TSFR4_26
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR4.10 - The `options` dictionary may contain a `users` key with a Boolean value, which specifies whether to include users, roles and grants in the DDL file.
# WL13807-TSFR4_31
TEST_BOOL_OPTION("users")

# WL13807-TSFR4_30
# WL13807-TSFR12_2
EXPECT_SUCCESS([test_schema], test_output_absolute, { "users": False, "ddlOnly": True, "showProgress": False })
EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, "@.users.sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, "@.sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, "@.post.sql")))

#@<> WL13807-FR4.10.1 - If the `users` option is not given, a default value of `true` must be used in case of `util.dumpInstance()` and false in case of `util.dumpSchemas()`.
# WL13807-TSFR4_29
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, "@.users.sql")))

#@<> test invalid values of the `includeUsers` option
TEST_ARRAY_OF_STRINGS_OPTION("includeUsers")

#@<> test invalid values of the `excludeUsers` option
TEST_ARRAY_OF_STRINGS_OPTION("excludeUsers")

#@<> the `includeUsers` and `excludeUsers` options cannot be used when `users` is false
EXPECT_FAIL("ValueError", "Argument #2: The 'includeUsers' option cannot be used if the 'users' option is set to false.", test_output_relative, { "users": False, "includeUsers": ["third"] })
EXPECT_FAIL("ValueError", "Argument #2: The 'excludeUsers' option cannot be used if the 'users' option is set to false.", test_output_relative, { "users": False, "excludeUsers": ["third"] })

#@<> test invalid user names
EXPECT_FAIL("ValueError", "Argument #2: User name must not be empty.", test_output_relative, { "includeUsers": [""] })
EXPECT_FAIL("ValueError", "Argument #2: User name must not be empty.", test_output_relative, { "excludeUsers": [""] })

EXPECT_FAIL("ValueError", "Argument #2: User name must not be empty.", test_output_relative, { "includeUsers": ["@"] })
EXPECT_FAIL("ValueError", "Argument #2: User name must not be empty.", test_output_relative, { "excludeUsers": ["@"] })

EXPECT_FAIL("ValueError", "Argument #2: Invalid user name: @", test_output_relative, { "includeUsers": ["@@"] })
EXPECT_FAIL("ValueError", "Argument #2: Invalid user name: @", test_output_relative, { "excludeUsers": ["@@"] })

EXPECT_FAIL("ValueError", "Argument #2: Malformed hostname. Cannot use \"'\" or '\"' characters on the hostname without quotes", test_output_relative, { "includeUsers": ["foo@''nope"] })
EXPECT_FAIL("ValueError", "Argument #2: Malformed hostname. Cannot use \"'\" or '\"' characters on the hostname without quotes", test_output_relative, { "excludeUsers": ["foo@''nope"] })

#@<> create an invalid test user with a ' character, which would be dumped wrong
session.run_sql("CREATE USER IF NOT EXISTS 'foo''bar'@'localhost' IDENTIFIED BY 'pwd';")

# WL14841-TSFR_1_1
EXPECT_FAIL("Error: Shell Error (52036)", "While 'Gathering information': Account 'foo\\'bar'@'localhost' contains the ' character, which is not supported", test_output_absolute, {}, True)

# ok if we exclude it
EXPECT_SUCCESS([test_schema], test_output_absolute, {"excludeUsers":["foo'bar@localhost"]})

session.run_sql("DROP USER 'foo''bar'@'localhost'")

#@<> create some test users
session.run_sql("CREATE USER IF NOT EXISTS 'first'@'localhost' IDENTIFIED BY 'pwd';")
session.run_sql("CREATE USER IF NOT EXISTS 'first'@'10.11.12.13' IDENTIFIED BY 'pwd';")
session.run_sql("CREATE USER IF NOT EXISTS 'firstfirst'@'localhost' IDENTIFIED BY 'pwd';")
session.run_sql("CREATE USER IF NOT EXISTS 'second'@'localhost' IDENTIFIED BY 'pwd';")
session.run_sql("CREATE USER IF NOT EXISTS 'second'@'10.11.12.14' IDENTIFIED BY 'pwd';")

# helper function
def EXPECT_INCLUDE_EXCLUDE(options, included, excluded, expected_exception = None):
    opts = { "ddlOnly": True, "showProgress": False }
    opts.update(options)
    if expected_exception:
        EXPECT_FAIL("ValueError", expected_exception, test_output_absolute, opts)
    else:
        EXPECT_SUCCESS([test_schema], test_output_absolute, opts)
    for i in included:
        EXPECT_FILE_CONTAINS(f"CREATE USER IF NOT EXISTS {get_user_account_for_output(i)}", os.path.join(test_output_absolute, "@.users.sql"))
    for e in excluded:
        EXPECT_FILE_NOT_CONTAINS(f"CREATE USER IF NOT EXISTS {get_user_account_for_output(e)}", os.path.join(test_output_absolute, "@.users.sql"))

#@<> don't include or exclude any users, all accounts are dumped
# some accounts are always excluded
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": [], "excludeUsers": [] }, ["'first'@'localhost'", "'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"], ["'mysql.infoschema'", "'mysql.session'", "'mysql.sys'"])

#@<> include non-existent user, no accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["third"] }, [], ["'first'@'localhost'", "'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> exclude non-existent user, all accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "excludeUsers": ["third"] }, ["'first'@'localhost'", "'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"], [])

#@<> include an existing user, one account is dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first@localhost"] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include an existing user, one account is dumped - single quotes
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["'first'@'localhost'"] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include an existing user, one account is dumped - double quotes
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ['"first"@"localhost"'] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include an existing user, one account is dumped - backticks
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["`first`@`localhost`"] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include using just the username, two accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first"] }, ["'first'@'localhost'", "'first'@'10.11.12.13'"], ["'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

EXPECT_STDOUT_MATCHES(re.compile(r'2 out of \d+ users will be dumped\.'))

#@<> include using just the same username twice, two accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "first"] }, ["'first'@'localhost'", "'first'@'10.11.12.13'"], ["'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include using just the username, exclude different accounts using just the username, two accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first"], "excludeUsers": ["second"] }, ["'first'@'localhost'", "'first'@'10.11.12.13'"], ["'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include and exclude the same username, conflicting options -> exception
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first"], "excludeUsers": ["first"] }, [], [], "Conflicting filtering options")

#@<> include using just the username, exclude one of the accounts, one account is dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first"], "excludeUsers": ["first@10.11.12.13"] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include using just the username, exclude one of the accounts, one account is dumped - single quotes
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first"], "excludeUsers": ["'first'@'10.11.12.13'"] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include using just the username, exclude one of the accounts, one account is dumped - double quotes
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first"], "excludeUsers": ['"first"@"10.11.12.13"'] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include using just the username, exclude one of the accounts, one account is dumped - backticks
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first"], "excludeUsers": ["`first`@`10.11.12.13`"] }, ["'first'@'localhost'"], ["'first'@'10.11.12.13'", "'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include using two usernames, four accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "second"] }, ["'first'@'localhost'", "'first'@'10.11.12.13'", "'second'@'localhost'", "'second'@'10.11.12.14'"], ["'firstfirst'@'localhost'"])

#@<> include using two usernames, exclude one of them, conflicting options -> exception
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "second"], "excludeUsers": ["second"] }, [], [], "Conflicting filtering options")

#@<> include using two usernames, exclude one of the accounts, three accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "second"], "excludeUsers": ["second@localhost"] }, ["'first'@'localhost'", "'first'@'10.11.12.13'", "'second'@'10.11.12.14'"], ["'firstfirst'@'localhost'", "'second'@'localhost'"])

#@<> include using an username and an account, three accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "second@localhost"] }, ["'first'@'localhost'", "'first'@'10.11.12.13'", "'second'@'localhost'"], ["'firstfirst'@'localhost'", "'second'@'10.11.12.14'"])

#@<> include using an username and an account, exclude using username, conflicting options -> exception
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "second@localhost"], "excludeUsers": ["second"]  }, [], [], "Conflicting filtering options")

#@<> include using an username and an account, exclude using an account, conflicting options -> exception
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "second@localhost"], "excludeUsers": ["second@localhost"]  }, [], [], "Conflicting filtering options")

#@<> include using an username and non-existing username, exclude using a non-existing username, two accounts are dumped
EXPECT_INCLUDE_EXCLUDE({ "includeUsers": ["first", "third"], "excludeUsers": ["fourth"]  }, ["'first'@'localhost'", "'first'@'10.11.12.13'"], ["'firstfirst'@'localhost'", "'second'@'localhost'", "'second'@'10.11.12.14'"])

#@<> drop test users
session.run_sql("DROP USER 'first'@'localhost';")
session.run_sql("DROP USER 'first'@'10.11.12.13';")
session.run_sql("DROP USER 'firstfirst'@'localhost';")
session.run_sql("DROP USER 'second'@'localhost';")
session.run_sql("DROP USER 'second'@'10.11.12.14';")

#@<> WL13807-FR4.11 - The `options` dictionary may contain an `excludeTables` key with a list of strings, which specifies the names of tables to be excluded from the dump.
# WL13807-TSFR4_38
TEST_ARRAY_OF_STRINGS_OPTION("excludeTables")

EXPECT_SUCCESS([test_schema], test_output_absolute, { "excludeTables": [], "ddlOnly": True, "showProgress": False })

# WL13807-TSFR4_33
# WL13807-TSFR4_35
# WL13807-TSFR4_37
EXPECT_SUCCESS(None, test_output_absolute, { "excludeTables": [ "`{0}`.`{1}`".format(test_schema, test_table_non_unique), "`{0}`.`{1}`".format(world_x_schema, world_x_table) ], "ddlOnly": True, "showProgress": False })
# WL13807-TSFR10_3
EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_non_unique) + ".sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_primary) + ".sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_unique) + ".sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_no_index) + ".sql")))

#@<> WL13807-FR4.11.1 - The table names must be in form `schema.table`. Both `schema` and `table` must be valid MySQL identifiers and must be quoted with backtick (`` ` ``) character when required.
# WL13807-TSFR4_36
EXPECT_FAIL("ValueError", "Argument #2: The table to be excluded must be in the following form: schema.table, with optional backtick quotes, wrong value: 'dummy'.", test_output_relative, { "excludeTables": [ "dummy" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be excluded 'dummy.dummy.dummy': Invalid object name, expected end of name, but got: '.'", test_output_relative, { "excludeTables": [ "dummy.dummy.dummy" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be excluded '@.dummy': Invalid character in identifier", test_output_relative, { "excludeTables": [ "@.dummy" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be excluded 'dummy.@': Invalid character in identifier", test_output_relative, { "excludeTables": [ "dummy.@" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be excluded '@.@': Invalid character in identifier", test_output_relative, { "excludeTables": [ "@.@" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be excluded '1.dummy': Invalid identifier: identifiers may begin with a digit but unless quoted may not consist solely of digits.", test_output_relative, { "excludeTables": [ "1.dummy" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be excluded 'dummy.1': Invalid identifier: identifiers may begin with a digit but unless quoted may not consist solely of digits.", test_output_relative, { "excludeTables": [ "dummy.1" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be excluded '2.1': Invalid identifier: identifiers may begin with a digit but unless quoted may not consist solely of digits.", test_output_relative, { "excludeTables": [ "2.1" ] })

#@<> WL13807-FR4.11.2 - If the specified table does not exist in the schema, or the schema is not included in dump, the table name is discarded.
# WL13807-TSFR4_34
EXPECT_SUCCESS(None, test_output_absolute, { "excludeTables": [ "`{0}`.`dummy`".format(test_schema), "`@`.dummy", "dummy.`@`", "`@`.`@`", "`1`.dummy", "dummy.`1`", "`2`.`1`" ], "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR4.11.3 - If the `excludeTables` option is not given, a default value of an empty list must be used instead.
# WL13807-TSFR4_32
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_non_unique) + ".sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_primary) + ".sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_unique) + ".sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_no_index) + ".sql")))

# WL13807-FR5 - The `util.dumpInstance()` function must additionally accept the following options:

#@<> WL13807-FR5.1 - The `options` dictionary may contain an `excludeSchemas` key with a list of strings, which specifies the names of schemas to be excluded from the dump.
# WL13807-TSFR5_6
TEST_ARRAY_OF_STRINGS_OPTION("excludeSchemas")

# WL13807-TSFR5_2
EXPECT_SUCCESS(None, test_output_absolute, { "excludeSchemas": exclude_all_but_types_schema, "ddlOnly": True, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(types_schema) + ".sql")))

for schema in exclude_all_but_types_schema:
    EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(schema) + ".sql")))

#@<> excludeSchemas + excludeTables
EXPECT_SUCCESS(None, test_output_absolute, { "excludeSchemas": exclude_all_but_types_schema, "excludeTables": [ "`{0}`.`{1}`".format(test_schema, test_table_non_unique), "`{0}`.`dummy`".format(test_schema), "`@`.dummy" ], "ddlOnly": True, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(types_schema) + ".sql")))

for schema in exclude_all_but_types_schema:
    EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(schema) + ".sql")))

#@<> WL13807-FR5.1.1 - If the specified schema does not exist, it is discarded from the list.
# WL13807-TSFR5_3
EXPECT_SUCCESS(None, test_output_absolute, { "excludeSchemas": exclude_all_but_types_schema + [ "dummy" ], "ddlOnly": True, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(types_schema) + ".sql")))

for schema in exclude_all_but_types_schema:
    EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(schema) + ".sql")))

#@<> WL13807-FR5.1.2 - If the `excludeSchemas` option is not given, a default value of an empty list must be used instead.
# WL13807-TSFR5_1
EXPECT_SUCCESS(None, test_output_absolute, { "ddlOnly": True, "showProgress": False })

for schema in all_schemas:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(schema) + ".sql")), schema)

# WL13807-FR5.1.3 - The following schemas must be always excluded:
# * information_schema
# * mysql
# * ndbinfo
# * performance_schema
# * sys
# WL13807-TSFR5_7
for schema in ["information_schema", "mysql", "ndbinfo", "performance_schema", "sys"]:
    EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(schema) + ".sql")))

#@<> WL13807-FR6 - The data dumps for the following tables must be excluded from any dumps that include their respective schemas. DDL must still be generated:
# * `mysql.apply_status`
# * `mysql.general_log`
# * `mysql.schema`
# * `mysql.slow_log`
# WL13807-TSFR6_1
# this requirement does not apply to dump_instance(), as according to FR5.1.3, mysql schema is always excluded

#@<> run dump for all SQL-related tests below
EXPECT_SUCCESS([types_schema, test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR9 - For each schema dumped, a DDL file with the base name as specified in FR8 and `.sql` extension must be created in the output directory.
# * The schema DDL file must contain all objects being dumped, including routines and events if enabled by options.
# WL13807-TSFR9_1
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(types_schema) + ".sql")))
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql")))

#@<> WL13807-FR10 - For each table dumped, a DDL file must be created with a base name as specified in FR7.1, and `.sql` extension.
# * The table DDL file must contain all objects being dumped.
# WL13807-TSFR10_1
for table in types_schema_tables:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(types_schema, table) + ".sql")))

for table in [test_table_primary, test_table_unique, test_table_non_unique, test_table_no_index]:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, table) + ".sql")))

#@<> WL13807-FR10.1 - If the `triggers` option was set to `true` and the dumped table has triggers, a DDL file must be created with a base name as specified in FR7.1, and `.triggers.sql` extension. File must contain all triggers for that table.
# WL13807-TSFR10_4
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_no_index) + ".triggers.sql")))

for table in [test_table_primary, test_table_unique, test_table_non_unique]:
    EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, table) + ".triggers.sql")))

#@<> WL13807-FR11 - For each view dumped, a DDL file must be created with a base name as specified in FR7.1, and `.sql` extension.
# WL13807-TSFR11_1
for view in types_schema_views:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(types_schema, view) + ".sql")))

for view in [test_view]:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, view) + ".sql")))

#@<> WL13807-FR11.1 - For each view dumped, a DDL file must be created with a base name as specified in FR7.1, and `.pre.sql` extension. This file must contain SQL statements which create a table with the same structure as the dumped view.
# WL13807-TSFR11_3
for view in types_schema_views:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(types_schema, view) + ".pre.sql")))

for view in [test_view]:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, view) + ".pre.sql")))

#@<> WL13807-FR12 - The following DDL files must be created in the output directory:
# * A file with the name `@.sql`, containing the SQL statements which should be executed before the whole dump is imported.
# * A file with the name `@.post.sql`, containing the SQL statements which should be executed after the whole dump is imported.
# WL13807-TSFR12_1
for f in [ "@.sql", "@.post.sql" ]:
    EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, f)))

#@<> WL13807-FR12.1 - If the `users` option was set to `true`, a file with the name `@.users.sql` must be created in the output directory:
# * The dump file must contain SQL statements to create users, roles and grant privileges.
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, "@.users.sql")))
EXPECT_FILE_CONTAINS("CREATE USER IF NOT EXISTS", os.path.join(test_output_absolute, "@.users.sql"))
EXPECT_FILE_CONTAINS("GRANT ", os.path.join(test_output_absolute, "@.users.sql"))

#@<> Check for roles {VER(>=8.0.0)}
EXPECT_FILE_CONTAINS(f"CREATE USER IF NOT EXISTS `{test_role}`@`%` IDENTIFIED WITH 'caching_sha2_password'", os.path.join(test_output_absolute, "@.users.sql"))
EXPECT_FILE_CONTAINS(f"GRANT USAGE ON *.* TO `{test_role}`@`%`;", os.path.join(test_output_absolute, "@.users.sql"))

#@<> WL13807-FR13 - Once the dump is complete, in addition to the summary described in WL#13804, FR15, the following information must be presented to the user:
# * The number of schemas dumped.
# * The number of tables dumped.
# WL13807: WL13804-FR15 - Once the dump is complete, the summary of the export process must be presented to the user. It must contain:
# * The number of rows written.
# * The number of bytes actually written to the data dump files.
# * The number of data bytes written to the data dump files. (only if `compression` option is not set to `none`)
# * The average throughout in bytes written per second.
# WL13807-TSFR13_1
EXPECT_SUCCESS([types_schema, test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

EXPECT_STDOUT_CONTAINS("Schemas dumped: 2")
EXPECT_STDOUT_CONTAINS("Tables dumped: {0}".format(len(types_schema_tables) + 4))
EXPECT_STDOUT_CONTAINS("Uncompressed data size: 0 bytes")
EXPECT_STDOUT_CONTAINS("Compressed data size: 0 bytes")
EXPECT_STDOUT_CONTAINS("Rows written: 0")
EXPECT_STDOUT_CONTAINS("Bytes written: 0 bytes")
EXPECT_STDOUT_CONTAINS("Average uncompressed throughput: 0.00 B/s")
EXPECT_STDOUT_CONTAINS("Average compressed throughput: 0.00 B/s")

# test without compression
EXPECT_SUCCESS([types_schema, test_schema], test_output_absolute, { "compression": "none", "ddlOnly": True, "showProgress": False })

EXPECT_STDOUT_CONTAINS("Schemas dumped: 2")
EXPECT_STDOUT_CONTAINS("Tables dumped: {0}".format(len(types_schema_tables) + 4))
EXPECT_STDOUT_CONTAINS("Data size:")
EXPECT_STDOUT_CONTAINS("Rows written: 0")
EXPECT_STDOUT_CONTAINS("Bytes written: 0 bytes")
EXPECT_STDOUT_CONTAINS("Average throughput: 0.00 B/s")

#@<> WL13807-FR14 - SQL scripts for DDL must be idempotent. That is, executing the same script multiple times (including when some of the attempts have failed) should result in the same schema that would be left by a single successful execution.
# * All SQL statements which create objects must not fail if object with the same type and name already exist.
# * Existing schemas and tables with the same names as the ones being dumped must not be deleted.
# * Existing views with the same names as the ones being dumped may be deleted.
# * Existing functions, stored procedures and events with the same names as the ones being dumped must be deleted.
# * If the `triggers` option was set to `true`, existing triggers with the same names as the ones being dumped must be deleted.
EXPECT_SUCCESS([test_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

all_sql_files = []
# order is important
all_sql_files.append("@.sql")
all_sql_files.append("@.users.sql")
all_sql_files.append(encode_schema_basename(test_schema) + ".sql")

for table in [test_table_primary, test_table_unique, test_table_non_unique, test_table_no_index]:
    all_sql_files.append(encode_table_basename(test_schema, table) + ".sql")

for view in [test_view]:
    all_sql_files.append(encode_table_basename(test_schema, view) + ".pre.sql")

for view in [test_view]:
    all_sql_files.append(encode_table_basename(test_schema, view) + ".sql")

all_sql_files.append(encode_table_basename(test_schema, test_table_no_index) + ".triggers.sql")
all_sql_files.append("@.post.sql")

recreate_verification_schema()

for f in all_sql_files:
    for i in range(0, 2):
        EXPECT_EQ(0, testutil.call_mysqlsh([uri + "/" + verification_schema, "--sql", "--file", os.path.join(test_output_absolute, f)]))

drop_all_schemas(all_schemas)

#@<> WL13807-FR15 - All created files should have permissions set to rw-r-----, owner should be set to the user running Shell. {__os_type != "windows"}
# WL13807-TSFR15_1
EXPECT_SUCCESS([test_schema], test_output_absolute, { "showProgress": False })

for f in os.listdir(test_output_absolute):
    path = os.path.join(test_output_absolute, f)
    EXPECT_EQ(0o640, stat.S_IMODE(os.stat(path).st_mode))
    EXPECT_EQ(os.getuid(), os.stat(path).st_uid)

#@<> WL13807-FR16.1 - The `options` dictionary may contain a `ocimds` key with a Boolean or string value, which specifies whether the compatibility checks with `MySQL HeatWave Service` and DDL substitutions should be done.
TEST_BOOL_OPTION("ocimds")

#@<> tables with missing PKs
missing_pks = {
    "xtest": [
        "t_bigint",
        "t_bit",
        "t_char",
        "t_date",
        "t_decimal1",
        "t_decimal2",
        "t_decimal3",
        "t_double",
        "t_enum",
        "t_float",
        "t_geom",
        "t_geom_all",
        "t_int",
        "t_integer",
        "t_json",
        "t_lchar",
        "t_lob",
        "t_mediumint",
        "t_numeric1",
        "t_numeric2",
        "t_real",
        "t_set",
        "t_smallint",
        "t_tinyint",
    ],
    incompatible_schema: [
        incompatible_table_data_directory,
        incompatible_table_encryption,
        incompatible_table_index_directory,
        incompatible_table_tablespace,
        incompatible_table_wrong_engine,
    ],
    test_schema: [
        test_table_unique,
        test_table_non_unique,
        test_table_no_index
    ]
}

#@<> WL13807-FR16.1.1 - If the `ocimds` option is set to `true`, the following must be done:
# * General
#   * Add the `mysql` schema to the schema exclusion list
# * GRANT
#   * Check whether users or roles are granted the following privileges and error out if so.
#     * SUPER,
#     * FILE,
#     * RELOAD,
#     * BINLOG_ADMIN,
#     * SET_USER_ID.
# * CREATE TABLE
#   * If ENGINE is not `InnoDB`, an exception must be raised.
#   * DATA|INDEX DIRECTORY and ENCRYPTION options must be commented out.
#   * Same restrictions for partitions.
# * CHARSETS - checks whether db objects use any other character set than supported utf8mb4.
# WL13807-TSFR16_1
# WL14506-TSFR_1_2
# WL14506-TSFR_1_3
excluded_schemas = [ "xtest" ]
excluded_tables = []

for table in missing_pks[test_schema]:
    excluded_tables.append("`{0}`.`{1}`".format(test_schema, table))

recreate_verification_schema()
target_version = "8.1.0"
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "targetVersion": target_version, "ocimds": True, "excludeSchemas": excluded_schemas, "excludeTables": excluded_tables })

# BUG#35663805 print a note to always use the lastest shell
EXPECT_STDOUT_CONTAINS("NOTE: When migrating to MySQL HeatWave Service, please always use the latest available version of MySQL Shell.")

EXPECT_STDOUT_CONTAINS(f"Checking for compatibility with MySQL HeatWave Service {target_version}")

if __version_num < 80000:
    EXPECT_STDOUT_CONTAINS("NOTE: MySQL Server 5.7 detected, please consider upgrading to 8.0 first.")
    EXPECT_STDOUT_CONTAINS("Checking for potential upgrade issues.")

EXPECT_STDOUT_CONTAINS(strip_restricted_grants(test_user_account, test_privileges).error())

EXPECT_STDOUT_CONTAINS(comment_data_index_directory(incompatible_schema, incompatible_table_data_directory).fixed())

EXPECT_STDOUT_CONTAINS(comment_encryption(incompatible_schema, incompatible_table_encryption).fixed())

if __version_num < 80000 and __os_type != "windows":
    EXPECT_STDOUT_CONTAINS(comment_data_index_directory(incompatible_schema, incompatible_table_index_directory).fixed())

EXPECT_STDOUT_CONTAINS(force_innodb_unsupported_storage(incompatible_schema, incompatible_table_index_directory).error())

EXPECT_STDOUT_CONTAINS(strip_tablespaces(incompatible_schema, incompatible_table_tablespace).error())

EXPECT_STDOUT_CONTAINS(force_innodb_unsupported_storage(incompatible_schema, incompatible_table_wrong_engine).error())
EXPECT_STDOUT_CONTAINS(force_innodb_row_format_fixed(incompatible_schema, incompatible_table_wrong_engine).error())

EXPECT_STDOUT_CONTAINS(strip_definers_definer_clause(incompatible_schema, incompatible_view).error())
EXPECT_STDOUT_CONTAINS(strip_definers_security_clause(incompatible_schema, incompatible_view).error())

EXPECT_STDOUT_CONTAINS(f"Compatibility issues with MySQL HeatWave Service {target_version} were found. Please use the 'compatibility' option to apply compatibility adaptations to the dumped DDL.")

for plugin in allowed_authentication_plugins:
    EXPECT_STDOUT_NOT_CONTAINS(skip_invalid_accounts_plugin(get_test_user_account(plugin), plugin).error())

for plugin in disallowed_authentication_plugins:
    EXPECT_STDOUT_CONTAINS(skip_invalid_accounts_plugin(get_test_user_account(plugin), plugin).error())
    # invalid user is removed from further checks, there should be no errors about restricted privileges
    msg = strip_restricted_grants(get_test_user_account(plugin), []).error()
    EXPECT_STDOUT_NOT_CONTAINS(msg[:msg.find("privilege")])

# BUG#32213605 - list of privileges allowed in MDS
# there should be no errors on USAGE privilege
EXPECT_STDOUT_NOT_CONTAINS("USAGE")
# there should be no errors about the user which only has allowed privileges
EXPECT_STDOUT_NOT_CONTAINS(get_test_user_account(test_all_allowed_privileges))
# all disallowed privileges should be reported
EXPECT_STDOUT_CONTAINS(strip_restricted_grants(get_test_user_account(test_disallowed_privileges), disallowed_privileges).error())

# BUG#32741098 - list users which do not have a password
EXPECT_STDOUT_CONTAINS(skip_invalid_accounts_no_password(test_user_no_pwd).error())

# WL14506-FR1 - When a dump is executed with the ocimds option set to true, for each table that would be dumped which does not contain a primary key, an error must be reported.
# WL14506-TSFR_1_8
for table in missing_pks[incompatible_schema]:
    EXPECT_STDOUT_CONTAINS(create_invisible_pks(incompatible_schema, table).error())

# WL14506-TSFR_1_2
# WL14506-TSFR_1_3
for table in missing_pks["xtest"] + missing_pks[test_schema]:
    EXPECT_STDOUT_NOT_CONTAINS(table)

# WL14506-FR1.1 - The following message must be printed:
# WL14506-TSFR_1_8
EXPECT_STDOUT_CONTAINS("""
ERROR: One or more tables without Primary Keys were found.

       MySQL HeatWave Service High Availability (MySQL HeatWave Service HA) requires Primary Keys to be present in all tables.
       To continue with the dump you must do one of the following:

       * Create PRIMARY keys in all tables before dumping them.
         MySQL 8.0.23 supports the creation of invisible columns to allow creating Primary Key columns with no impact to applications. For more details, see https://dev.mysql.com/doc/refman/en/invisible-columns.html.
         This is considered a best practice for both performance and usability and will work seamlessly with MySQL HeatWave Service.

       * Add the "create_invisible_pks" to the "compatibility" option.
         The dump will proceed and loader will automatically add Primary Keys to tables that don't have them when loading into MySQL HeatWave Service.
         This will make it possible to enable HA in MySQL HeatWave Service without application impact.
         However, Inbound Replication into a DB System HA instance (at the time of the release of MySQL Shell 8.0.24) will still not be possible.

       * Add the "ignore_missing_pks" to the "compatibility" option.
         This will disable this check and the dump will be produced normally, Primary Keys will not be added automatically.
         It will not be possible to load the dump in an HA enabled DB System instance.
""")

#@<> BUG#33159903 table with too many columns
# setup
tested_schema = "tested_schema"
tested_table = "too_many_columns"
columns_count = 1018

session.run_sql(f"CREATE SCHEMA !;", [ tested_schema ])
session.run_sql(f"CREATE TABLE !.! ({', '.join(f'col{i} int' for i in range(columns_count))}) ENGINE=MyISAM;", [ tested_schema, tested_table ])

# test
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "ocimds": True })
EXPECT_STDOUT_CONTAINS(too_many_columns(tested_schema, tested_table, columns_count).error())

# cleanup
session.run_sql(f"DROP SCHEMA !;", [ tested_schema ])

#@<> WL14506-TSFR_2_1
util.help("dump_instance")

EXPECT_STDOUT_CONTAINS("""
      create_invisible_pks - Each table which does not have a Primary Key will
      have one created when the dump is loaded. The following Primary Key is
      added to the table:
      `my_row_id` BIGINT UNSIGNED AUTO_INCREMENT INVISIBLE PRIMARY KEY

      At the time of the release of MySQL Shell 8.0.24, dumps created with this
      value cannot be used with Inbound Replication into an MySQL HeatWave
      Service DB System instance with High Availability. Mutually exclusive
      with the ignore_missing_pks value.
""")
EXPECT_STDOUT_CONTAINS("""
      ignore_missing_pks - Ignore errors caused by tables which do not have
      Primary Keys. Dumps created with this value cannot be used in MySQL
      HeatWave Service DB System instance with High Availability. Mutually
      exclusive with the create_invisible_pks value.
""")
EXPECT_STDOUT_CONTAINS("""
      At the time of the release of MySQL Shell 8.0.24, in order to use Inbound
      Replication into an MySQL HeatWave Service DB System instance with High
      Availability, all tables at the source server need to have Primary Keys.
      This needs to be fixed manually before running the dump. Starting with
      MySQL 8.0.23 invisible columns may be used to add Primary Keys without
      changing the schema compatibility, for more information see:
      https://dev.mysql.com/doc/refman/en/invisible-columns.html.

      In order to use MySQL HeatWave Service DB Service instance with High
      Availability, all tables must have a Primary Key. This can be fixed
      automatically using the create_invisible_pks compatibility value.
""")

#@<> BUG#31403104: if users is false, errors about the users should not be included
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "ocimds": True, "users": False })
EXPECT_STDOUT_NOT_CONTAINS(strip_restricted_grants(test_user_account, test_privileges).error())

for plugin in disallowed_authentication_plugins:
    EXPECT_STDOUT_NOT_CONTAINS(skip_invalid_accounts_plugin(get_test_user_account(plugin), plugin).error())

#@<> BUG#31403104: compatibility checks are enabled, but users and SQL is not dumped, this should succeed
# WL14506-TSFR_1_4
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "ocimds": True, "dataOnly": True, "users": False, "showProgress": False })

#@<> WL13807-FR16.1.2 - If the `ocimds` option is not given, a default value of `false` must be used instead.
# WL13807-TSFR16_2
# WL14506-TSFR_1_1
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

#@<> WL13807-FR16.2 - The `options` dictionary may contain a `compatibility` key with an array of strings value, which specifies the `MySQL HeatWave Service`-related compatibility modifications that should be applied when creating the DDL files.
TEST_ARRAY_OF_STRINGS_OPTION("compatibility")

EXPECT_FAIL("ValueError", "Argument #2: Unknown compatibility option: dummy", test_output_relative, { "compatibility": [ "dummy" ] })
EXPECT_FAIL("ValueError", "Argument #2: Unknown compatibility option: ", test_output_relative, { "compatibility": [ "" ] })

#@<> WL13807-FR16.2.1 - The `compatibility` option may contain the following values:
# * `force_innodb` - replace incompatible table engines with `InnoDB`,
# * `strip_restricted_grants` - remove disallowed grants.
# * `strip_tablespaces` - remove unsupported tablespace syntax.
# * `strip_definers` - remove DEFINER clause from views, triggers, events and routines and change SQL SECURITY property to INVOKER for views and routines.
# BUG#32115948 - added `skip_invalid_accounts` - removes users using unsupported authentication plugins
# WL14506-FR2 - The compatibility option of the dump utilities must support a new value: ignore_missing_pks.
# WL14506-TSFR_1_9
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "ocimds": True, "compatibility": [ "force_innodb", "ignore_missing_pks", "strip_definers", "strip_restricted_grants", "strip_tablespaces", "skip_invalid_accounts" ] , "ddlOnly": True, "showProgress": False })

# WL14506-FR2.2 - The following message must be printed:
# WL14506-TSFR_1_9
EXPECT_STDOUT_CONTAINS("""
NOTE: One or more tables without Primary Keys were found.

      This issue is ignored.
      This dump cannot be loaded into an MySQL HeatWave Service DB System instance with High Availability.
""")

# WL14506-FR3 - The compatibility option of the dump utilities must support a new value: create_invisible_pks.
# create_invisible_pks and ignore_missing_pks are mutually exclusive
# WL14506-TSFR_1_10
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "ocimds": True, "compatibility": [ "create_invisible_pks", "force_innodb", "strip_definers", "strip_restricted_grants", "strip_tablespaces", "skip_invalid_accounts" ] , "ddlOnly": True, "showProgress": False })

# WL14506-FR3.1.1 - The following message must be printed:
# WL14506-TSFR_1_10
EXPECT_STDOUT_CONTAINS("""
NOTE: One or more tables without Primary Keys were found.

      Missing Primary Keys will be created automatically when this dump is loaded.
      This will make it possible to enable High Availability in MySQL HeatWave Service DB System instance without application impact.
      However, Inbound Replication into a DB System HA instance (at the time of the release of MySQL Shell 8.0.24) will still not be possible.
""")

#@<> WL14506-FR3.1 - When a dump is executed with the ocimds option set to true and the compatibility option contains the create_invisible_pks value, for each table that would be dumped which does not contain a primary key, an information should be printed that an invisible primary key will be created when loading the dump.
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "compatibility": [ "create_invisible_pks" ] , "ddlOnly": True, "showProgress": False })

for table in missing_pks[incompatible_schema]:
    EXPECT_STDOUT_CONTAINS(create_invisible_pks(incompatible_schema, table).fixed())

#@<> WL14506-FR3.2 - When a dump is executed and the compatibility option contains the create_invisible_pks value, for each table that would be dumped which does not contain a primary key but has a column named my_row_id, an error must be reported.
# WL14506-TSFR_3.2_1
table = missing_pks[incompatible_schema][0]
session.run_sql("ALTER TABLE !.! ADD COLUMN my_row_id int;", [incompatible_schema, table])

EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_relative, { "compatibility": [ "create_invisible_pks" ] }, True)
EXPECT_STDOUT_CONTAINS(create_invisible_pks_name_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS("Could not apply some of the compatibility options")

WIPE_OUTPUT()
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "ocimds": True, "compatibility": [ "create_invisible_pks" ] })
EXPECT_STDOUT_CONTAINS(create_invisible_pks_name_conflict(incompatible_schema, table).error())

session.run_sql("ALTER TABLE !.! DROP COLUMN my_row_id;", [incompatible_schema, table])

#@<> WL14506-FR3.4 - When a dump is executed and the compatibility option contains the create_invisible_pks value, for each table that would be dumped which does not contain a primary key but has a column with an AUTO_INCREMENT attribute, an error must be reported.
table = missing_pks[incompatible_schema][0]
session.run_sql("ALTER TABLE !.! ADD COLUMN idx int AUTO_INCREMENT UNIQUE;", [incompatible_schema, table])

EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_relative, { "compatibility": [ "create_invisible_pks" ] }, True)
EXPECT_STDOUT_CONTAINS(create_invisible_pks_auto_increment_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS("Could not apply some of the compatibility options")

WIPE_OUTPUT()
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "ocimds": True, "compatibility": [ "create_invisible_pks" ] })
EXPECT_STDOUT_CONTAINS(create_invisible_pks_auto_increment_conflict(incompatible_schema, table).error())

session.run_sql("ALTER TABLE !.! DROP COLUMN idx;", [incompatible_schema, table])

#@<> WL14506-FR3.2 + WL14506-FR3.4 - same column
table = missing_pks[incompatible_schema][0]
session.run_sql("ALTER TABLE !.! ADD COLUMN my_row_id int AUTO_INCREMENT UNIQUE;", [incompatible_schema, table])

EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_relative, { "compatibility": [ "create_invisible_pks" ] }, True)
EXPECT_STDOUT_CONTAINS(create_invisible_pks_name_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS(create_invisible_pks_auto_increment_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS("Could not apply some of the compatibility options")

WIPE_OUTPUT()
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "ocimds": True, "compatibility": [ "create_invisible_pks" ] })
EXPECT_STDOUT_CONTAINS(create_invisible_pks_name_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS(create_invisible_pks_auto_increment_conflict(incompatible_schema, table).error())

session.run_sql("ALTER TABLE !.! DROP COLUMN my_row_id;", [incompatible_schema, table])

#@<> WL14506-FR3.2 + WL14506-FR3.4 - different columns
table = missing_pks[incompatible_schema][0]
session.run_sql("ALTER TABLE !.! ADD COLUMN my_row_id int;", [incompatible_schema, table])
session.run_sql("ALTER TABLE !.! ADD COLUMN idx int AUTO_INCREMENT UNIQUE;", [incompatible_schema, table])

EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_relative, { "compatibility": [ "create_invisible_pks" ] }, True)
EXPECT_STDOUT_CONTAINS(create_invisible_pks_name_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS(create_invisible_pks_auto_increment_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS("Could not apply some of the compatibility options")

WIPE_OUTPUT()
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "ocimds": True, "compatibility": [ "create_invisible_pks" ] })
EXPECT_STDOUT_CONTAINS(create_invisible_pks_name_conflict(incompatible_schema, table).error())
EXPECT_STDOUT_CONTAINS(create_invisible_pks_auto_increment_conflict(incompatible_schema, table).error())

session.run_sql("ALTER TABLE !.! DROP COLUMN my_row_id;", [incompatible_schema, table])
session.run_sql("ALTER TABLE !.! DROP COLUMN idx;", [incompatible_schema, table])

#@<> WL14506-FR3.3 - When a dump is executed and the compatibility option contains both create_invisible_pks and ignore_missing_pks values, an error must be reported and process must be aborted.
# WL14506-TSFR_3.3_1
EXPECT_FAIL("ValueError", "Argument #2: The 'create_invisible_pks' and 'ignore_missing_pks' compatibility options cannot be used at the same time.", test_output_relative, { "compatibility": [ "create_invisible_pks", "ignore_missing_pks" ] })

#@<> WL13807-FR16.2.1 - force_innodb
# WL13807-TSFR16_3
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "compatibility": [ "force_innodb" ] , "ddlOnly": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS(force_innodb_unsupported_storage(incompatible_schema, incompatible_table_index_directory).fixed())
EXPECT_STDOUT_CONTAINS(force_innodb_unsupported_storage(incompatible_schema, incompatible_table_wrong_engine).fixed())
EXPECT_STDOUT_CONTAINS(force_innodb_row_format_fixed(incompatible_schema, incompatible_table_wrong_engine).fixed())

#@<> WL14506-FR2.1 - When a dump is executed with the ocimds option set to true and the compatibility option contains the ignore_missing_pks value, for each table that would be dumped which does not contain a primary key, a note must be displayed, stating that this issue is ignored.
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "compatibility": [ "ignore_missing_pks" ] , "ddlOnly": True, "showProgress": False })

for table in missing_pks[incompatible_schema]:
    EXPECT_STDOUT_CONTAINS(ignore_missing_pks(incompatible_schema, table).fixed())

#@<> WL13807-FR16.2.1 - strip_definers
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "compatibility": [ "strip_definers" ] , "ddlOnly": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS(strip_definers_definer_clause(incompatible_schema, incompatible_view).fixed())
EXPECT_STDOUT_CONTAINS(strip_definers_security_clause(incompatible_schema, incompatible_view).fixed())

#@<> WL13807-FR16.2.1 - strip_restricted_grants
# WL13807-TSFR16_5
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "compatibility": [ "strip_restricted_grants" ] , "ddlOnly": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS(strip_restricted_grants(test_user_account, test_privileges).fixed())

#@<> WL13807-FR16.2.1 - strip_tablespaces
# WL13807-TSFR16_4
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "compatibility": [ "strip_tablespaces" ] , "ddlOnly": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS(strip_tablespaces(incompatible_schema, incompatible_table_tablespace).fixed())

# BUG#32115948 - added `skip_invalid_accounts` - removes users using unsupported authentication plugins
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "compatibility": [ "skip_invalid_accounts" ] , "ddlOnly": True, "showProgress": False })

for plugin in disallowed_authentication_plugins:
    EXPECT_STDOUT_CONTAINS(skip_invalid_accounts_plugin(get_test_user_account(plugin), plugin).fixed())

# BUG#32741098 - users which do not have a passwords are removed from the dump by 'skip_invalid_accounts'
EXPECT_STDOUT_CONTAINS(skip_invalid_accounts_no_password(test_user_no_pwd).fixed())

#@<> WL13807-FR16.2.2 - If the `compatibility` option is not given, a default value of `[]` must be used instead.
# WL13807-TSFR16_6
EXPECT_SUCCESS([incompatible_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_STDOUT_NOT_CONTAINS(force_innodb_unsupported_storage(incompatible_schema, incompatible_table_index_directory).fixed())
EXPECT_STDOUT_NOT_CONTAINS(force_innodb_unsupported_storage(incompatible_schema, incompatible_table_wrong_engine).fixed())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_definer_clause(incompatible_schema, incompatible_view).fixed())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_security_clause(incompatible_schema, incompatible_view).fixed())
EXPECT_STDOUT_NOT_CONTAINS(strip_restricted_grants(test_user_account, test_privileges).fixed())
EXPECT_STDOUT_NOT_CONTAINS(strip_tablespaces(incompatible_schema, incompatible_table_tablespace).fixed())

# WL13807-FR7 - The table data dump must be written in the output directory, to a file with a base name as specified in FR7.1, and a `.tsv` extension.
# For WL13807-FR7.1 please see above.
# WL13807-FR7.2 - If multiple table data dump files are to be created (the `chunking` option is set to `true`), the base name of each file must consist of a base name, as specified in FR6, followed by `@N` (or `@@N` in case of the last file), where `N` is the zero-based ordinal number of the file.
# WL13807-FR7.3 - The format of an output file must be the same as the default format used by the `util.importTable()` function, as specified in WL#12193.
# WL13807-FR7.4 - While the data is being written to an output file, the data dump file must be suffixed with a `.dumping` extension. Once writing is finished, the file must be renamed to its original name.
# Data consistency tests.

#@<> test a single table with no chunking
EXPECT_SUCCESS([world_x_schema], test_output_absolute, { "chunking": False, "compression": "none", "showProgress": False })
TEST_LOAD(world_x_schema, world_x_table)

#@<> test multiple tables with chunking
EXPECT_SUCCESS([test_schema], test_output_absolute, { "bytesPerChunk": "1M", "compression": "none", "showProgress": False })
TEST_LOAD(test_schema, test_table_primary)
TEST_LOAD(test_schema, test_table_unique)
# these are not chunked because they don't have an appropriate column
TEST_LOAD(test_schema, test_table_non_unique)
TEST_LOAD(test_schema, test_table_no_index)

#@<> test multiple tables with various data types
EXPECT_SUCCESS([types_schema], test_output_absolute, { "chunking": False, "compression": "none", "showProgress": False })

for table in types_schema_tables:
    TEST_LOAD(types_schema, table)

#@<> test privileges required to dump an instance
class PrivilegeError:
    def __init__(self, exception_message, error_message="", exception_type="RuntimeError", output_dir_created=False, fatal=True):
        self.exception_message = exception_message
        self.error_message = error_message
        self.exception_type = exception_type
        self.output_dir_created = output_dir_created
        self.fatal = fatal

# if this list ever changes, online docs need to be updated
required_privileges = {
    "EVENT": PrivilegeError(  # database-level privilege
        re.compile(r"While 'Gathering information': User {0} is missing the following privilege\(s\) for schema `.+`: EVENT.".format(test_user_account)),
        exception_type = "Error: Shell Error (52008)"
    ),
    "RELOAD": PrivilegeError(  # global privilege; if this privilege is missing, FTWRL will fail and dump will fallback to LOCK TABLES
        re.compile(r"While 'Initializing': Unable to lock tables: User {0} is missing the following privilege\(s\) for table `.+`\.`.+`: LOCK TABLES.".format(test_user_account)),
        "WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...",
        exception_type = "Error: Shell Error (52002)"
    ),
    "SELECT": PrivilegeError(  # table-level privilege
        re.compile(r"While 'Gathering information': User {0} is missing the following privilege\(s\) for table `.+`\.`.+`: SELECT.".format(test_user_account)),
        exception_type = "Error: Shell Error (52009)"
    ),
    "SHOW VIEW": PrivilegeError(  # table-level privilege
        re.compile(r"While 'Writing .*': Fatal error during dump"),
        f"MySQL Error 1142 (42000): SHOW VIEW command denied to user {test_user_account}",
        output_dir_created=True,
        exception_type = "Error: Shell Error (52006)"
    ),
    "TRIGGER": PrivilegeError(  # table-level privilege
        re.compile(r"While 'Gathering information': User {0} is missing the following privilege\(s\) for table `.+`\.`.+`: TRIGGER.".format(test_user_account)),
        exception_type = "Error: Shell Error (52009)"
    ),
    "REPLICATION CLIENT": PrivilegeError(  # global privilege
        "NO EXCEPTION!",
        "WARNING: Could not fetch the binary log information: MySQL Error 1227 (42000): Access denied; you need (at least one of) the SUPER, REPLICATION CLIENT privilege(s) for this operation",
        fatal=False
    ),
}

if __version_num >= 80000:
    # when running a consistent dump on 8.0, LOCK INSTANCE FOR BACKUP is executed, which requires BACKUP_ADMIN privilege
    # BUG#33697289 - this is no longer an error, consistency is checked instead
    required_privileges["BACKUP_ADMIN"] = PrivilegeError(  # global privilege
        "NO EXCEPTION!",
        f"NOTE: Backup lock is not available to the account {test_user_account} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.",
        fatal=False
    )
    # 8.0 has roles which are checked prior to running the dump, if user is missing the SELECT privilege, error will be reported at this stage
    required_privileges["SELECT"] = PrivilegeError(  # table-level privilege
        "Unable to get roles information.",
        f"ERROR: Unable to check privileges for user {test_user_account}. User requires SELECT privilege on mysql.* to obtain information about all roles."
    )

# setup the user, grant only required privileges
create_users()
session.run_sql(f"REVOKE ALL PRIVILEGES ON *.* FROM {test_user_account};")
for privilege in required_privileges.keys():
    session.run_sql(f"GRANT {privilege} ON *.* TO {test_user_account};")

# reconnect as test user
setup_session(test_user_uri(__mysql_sandbox_port1))

# create session for root
root_session = mysql.get_session(uri)

# user has all the required privileges, this should succeed
EXPECT_SUCCESS(all_schemas, test_output_absolute, { "showProgress": False })
# check if events are here
EXPECT_FILE_CONTAINS("CREATE DEFINER=`{0}`@`{1}` EVENT IF NOT EXISTS `{2}`".format(__user, __host, test_schema_event), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
# check if routines are here
EXPECT_FILE_CONTAINS("CREATE DEFINER=`{0}`@`{1}` PROCEDURE `{2}`".format(__user, __host, test_schema_procedure), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
EXPECT_FILE_CONTAINS("CREATE DEFINER=`{0}`@`{1}` FUNCTION `{2}`".format(__user, __host, test_schema_function), os.path.join(test_output_absolute, encode_schema_basename(test_schema) + ".sql"))
# check is users are here
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, "@.users.sql")))
# check if triggers are here
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_table_basename(test_schema, test_table_no_index) + ".triggers.sql")))

# check if revoking one of the privileges results in a failure
for privilege, error in required_privileges.items():
    print("--> testing:", privilege)
    root_session.run_sql(f"REVOKE {privilege} ON *.* FROM {test_user_account};")
    WIPE_STDOUT()
    if error.fatal:
        EXPECT_FAIL(error.exception_type, error.exception_message, test_output_absolute, { "showProgress": False }, expect_dir_created=error.output_dir_created)
    else:
        EXPECT_SUCCESS(all_schemas, test_output_absolute, { "showProgress": False })
    EXPECT_STDOUT_CONTAINS(error.error_message)
    # repeat with dry run
    WIPE_STDOUT()
    if error.fatal:
        EXPECT_FAIL(error.exception_type, error.exception_message, test_output_absolute, { "dryRun": True, "showProgress": False }, expect_dir_created=False)
    else:
        EXPECT_SUCCESS(all_schemas, test_output_absolute, { "dryRun": True, "showProgress": False })
    EXPECT_STDOUT_CONTAINS(error.error_message)
    root_session.run_sql(f"GRANT {privilege} ON *.* TO {test_user_account};")

# cleanup
root_session.close()
setup_session()
create_users()

#@<> dump table when different character set/SQL mode is used
# this should be the last test that uses `test_schema`, as it drops it in order to not mess up with test
# (schema name contains non-ASCII characters, it's difficult to encode it properly in order for it to be excluded)
session.run_sql("DROP SCHEMA IF EXISTS !;", [ test_schema ])

session.run_sql("SET NAMES 'latin1';")
session.run_sql("SET GLOBAL SQL_MODE='ANSI_QUOTES,NO_AUTO_VALUE_ON_ZERO,NO_BACKSLASH_ESCAPES,NO_DIR_IN_CREATE,NO_ZERO_DATE,PAD_CHAR_TO_FULL_LENGTH';")

EXPECT_SUCCESS([world_x_schema], test_output_absolute, { "defaultCharacterSet": "latin1", "bytesPerChunk": "1M", "compression": "none", "showProgress": False })
TEST_LOAD(world_x_schema, world_x_table)

session.run_sql("SET NAMES 'utf8mb4';")
session.run_sql("SET GLOBAL SQL_MODE='';")

#@<> BUG#33173739 - lock one of the tables, user has privileges required to execute FTWRL, dry run will execute it do double check the privileges, but will not hang
session.run_sql("LOCK TABLES !.! WRITE", [ types_schema, types_schema_tables[0] ])

EXPECT_SUCCESS([types_schema], test_output_absolute, { "dryRun": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS("Global read lock acquired")

session.run_sql("UNLOCK TABLES")

#@<> BUG#33173739 - user has privileges required to execute FTWRL, dumper will execute it do double check the privileges, but it throws access denied error, fallback to LOCK TABLES {not __dbug_off}
testutil.set_trap("mysql", ["sql == FLUSH TABLES WITH READ LOCK;"], { "code": 1045, "msg": "Access denied for user ‘root’@‘%’ (using password: YES)", "state": "28000" })

for dry_run in [ True, False ]:
    WIPE_OUTPUT()
    EXPECT_SUCCESS([types_schema], test_output_absolute, { "dryRun": dry_run, "showProgress": False })
    EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")

testutil.clear_traps("mysql")

#@<> BUG#33173739 - user has privileges required to execute FTWRL, dumper will execute it do double check the privileges, but it throws some random error {not __dbug_off}
testutil.set_trap("mysql", ["sql == FLUSH TABLES WITH READ LOCK;"], { "code": 1226, "msg": "User 'root' has exceeded the 'max_questions' resource (current value: 2)", "state": "42000" })

EXPECT_FAIL("Error: Shell Error (52001)", "While 'Initializing': Unable to acquire global read lock", test_output_absolute, { "showProgress": False })
EXPECT_STDOUT_CONTAINS("ERROR: Failed to acquire global read lock: MySQL Error 1226 (42000): User 'root' has exceeded the 'max_questions' resource (current value: 2)")

testutil.clear_traps("mysql")

#@<> prepare user privileges, switch user
create_users()
session.run_sql(f"GRANT ALL ON *.* TO {test_user_account};")
session.run_sql(f"REVOKE RELOAD /*!80023 , FLUSH_TABLES */ ON *.* FROM {test_user_account};")
shell.connect(test_user_uri(__mysql_sandbox_port1))

#@<> try to run consistent dump using a user which does not have required privileges for FTWRL but LOCK TABLES are ok
EXPECT_SUCCESS([types_schema], test_output_absolute, { "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")

#@<> BUG#32695301 - lock one of the mysql tables, dry run should not attempt to execute LOCK TABLES and dump should succeed
setup_session()
session.run_sql("LOCK TABLES mysql.user WRITE")
shell.connect(test_user_uri(__mysql_sandbox_port1))

EXPECT_SUCCESS([types_schema], test_output_absolute, { "dryRun": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")

setup_session()
session.run_sql("UNLOCK TABLES")

#@<> revoke lock tables from mysql.*  {VER(>=8.0.16)}
setup_session()
session.run_sql("SET GLOBAL partial_revokes=1")
session.run_sql(f"REVOKE LOCK TABLES ON mysql.* FROM {test_user_account};")
shell.connect(test_user_uri(__mysql_sandbox_port1))

#@<> try again, this time it should succeed but without locking mysql.* tables  {VER(>=8.0.16)}
EXPECT_SUCCESS([types_schema], test_output_absolute, { "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_CONTAINS(f"WARNING: Could not lock mysql system tables: User {test_user_account} is missing the following privilege(s) for schema `mysql`: LOCK TABLES.")

#@<> BUG#32695301 - lock one of the dumped tables, dry run should not attempt to execute LOCK TABLES and dump should succeed  {VER(>=8.0.16)}
setup_session()
session.run_sql("LOCK TABLES !.! WRITE", [ types_schema, types_schema_tables[0] ])
shell.connect(test_user_uri(__mysql_sandbox_port1))

EXPECT_SUCCESS([types_schema], test_output_absolute, { "dryRun": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_CONTAINS(f"WARNING: Could not lock mysql system tables: User {test_user_account} is missing the following privilege(s) for schema `mysql`: LOCK TABLES.")

setup_session()
session.run_sql("UNLOCK TABLES")

#@<> revoke lock tables from the rest
setup_session()
session.run_sql(f"REVOKE LOCK TABLES ON *.* FROM {test_user_account};")
shell.connect(test_user_uri(__mysql_sandbox_port1))

#@<> try to run consistent dump using a user which does not have any required privileges
EXPECT_FAIL("Error: Shell Error (52002)", re.compile(r"While 'Initializing': Unable to lock tables: User {0} is missing the following privilege\(s\) for table `.+`\.`.+`: LOCK TABLES.".format(test_user_account)), test_output_absolute, { "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_CONTAINS("ERROR: Unable to acquire global read lock neither table read locks")

#@<> BUG#32695301 - dry run should fail as well
EXPECT_FAIL("Error: Shell Error (52002)", re.compile(r"While 'Initializing': Unable to lock tables: User {0} is missing the following privilege\(s\) for table `.+`\.`.+`: LOCK TABLES.".format(test_user_account)), test_output_absolute, { "dryRun": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_CONTAINS("ERROR: Unable to acquire global read lock neither table read locks")

#@<> using the same user, run inconsistent dump
EXPECT_SUCCESS([types_schema], test_output_absolute, { "consistent": False, "ddlOnly": True, "showProgress": False })

#@<> BUG#32695301 - cleanup
setup_session()
create_users()

#@<> BUG#32695301 - restore partial_revokes {VER(>=8.0.16)}
session.run_sql("SET GLOBAL partial_revokes=0")

#@<> BUG#33697289 additional consistency checks if user is missing some of the privileges
# setup
setup_session()
create_users()
session.run_sql(f"GRANT ALL ON *.* TO {test_user_account};")
# user cannot execute FTWRL and LOCK INSTANCE FOR BACKUP
session.run_sql(f"REVOKE RELOAD /*!80023 , FLUSH_TABLES */ /*!80000 , BACKUP_ADMIN */ ON *.* FROM {test_user_account};")

tested_schema = "test_schema"
tested_table = "test_table"
reason = f"available to the account {test_user_account}" if __version_num >= 80000 else "supported in MySQL 5.7"

# constantly create tables
def constantly_create_tables():
    tables_to_create = 500
    session.run_sql("DROP SCHEMA IF EXISTS !;", [ tested_schema ])
    session.run_sql("CREATE SCHEMA !;", [ tested_schema ])
    for i in range(tables_to_create):
        session.run_sql(f"CREATE TABLE {tested_schema}.{tested_table}_{i} (a int)")
    create_tables = f"""v = {tables_to_create}
while True:
    session.run_sql("CREATE TABLE {tested_schema}.{tested_table}_{{0}} (a int)".format(v))
    v = v + 1
session.close()
"""
    # run a process which constantly creates tables
    pid = testutil.call_mysqlsh_async(["--py", uri], create_tables)
    # wait a bit for process to start
    time.sleep(1)
    return pid

# connect
shell.connect(test_user_uri(__mysql_sandbox_port1))

#@<> BUG#33697289 create a process which will add tables in the background
pid = constantly_create_tables()

#@<> BUG#33697289 test - backup lock is not available
EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_absolute, { "includeSchemas": [ tested_schema ], "consistent": True, "showProgress": False, "threads": 1 }, expect_dir_created = True)
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.")
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: The value of the gtid_executed system variable has changed during the dump, from: '.+' to: '.+'."))
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: Checking \d+ recent transactions for schema changes, use the 'skipConsistencyChecks' option to skip this check."))
EXPECT_STDOUT_CONTAINS("WARNING: DDL changes detected during DDL dump without a lock.")
EXPECT_STDOUT_CONTAINS(f"ERROR: Backup lock is not {reason} and DDL changes were not blocked. The consistency of the dump cannot be guaranteed.")
EXPECT_STDOUT_CONTAINS("NOTE: In order to overcome this issue, use a read-only replica with replication stopped, or, if dumping from a primary, then enable super_read_only system variable and ensure that any inbound replication channels are stopped.")
EXPECT_STDOUT_MATCHES(re.compile(r"ERROR: \[Worker00\d\]: Consistency check has failed"))

#@<> BUG#33697289 terminate the process immediately
testutil.wait_mysqlsh_async(pid, 0)

#@<> BUG#34556560 create a process which will add tables in the background - skipConsistencyChecks
pid = constantly_create_tables()

#@<> BUG#34556560 test - backup lock is not available - skipConsistencyChecks
EXPECT_SUCCESS([ tested_schema ], test_output_absolute, { "consistent": True, "skipConsistencyChecks": True, "showProgress": False, "threads": 1 })
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.")
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: The value of the gtid_executed system variable has changed during the dump, from: '.+' to: '.+'."))
EXPECT_STDOUT_CONTAINS("NOTE: The 'skipConsistencyChecks' option is set, assuming there were no DDL changes.")
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes were not blocked. The DDL is consistent, the world may resume now.")

#@<> BUG#34556560 terminate the process immediately - skipConsistencyChecks
testutil.wait_mysqlsh_async(pid, 0)

#@<> BUG#33697289 create a process which will add tables in the background (2) {not __dbug_off}
pid = constantly_create_tables()

#@<> BUG#33697289 fail if gtid is disabled and DDL changes {not __dbug_off}
testutil.dbug_set("+d,dumper_gtid_disabled")

EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_absolute, { "includeSchemas": [ tested_schema ], "consistent": True, "showProgress": False, "threads": 1 }, expect_dir_created = True)
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.")
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: The binlog position has changed during the dump, from: '.+' to: '.+'."))
EXPECT_STDOUT_CONTAINS("NOTE: Checking recent transactions for schema changes, use the 'skipConsistencyChecks' option to skip this check.")
EXPECT_STDOUT_CONTAINS("WARNING: DDL changes detected during DDL dump without a lock.")
EXPECT_STDOUT_CONTAINS(f"ERROR: Backup lock is not {reason} and DDL changes were not blocked. The consistency of the dump cannot be guaranteed.")
EXPECT_STDOUT_CONTAINS("NOTE: In order to overcome this issue, use a read-only replica with replication stopped, or, if dumping from a primary, then enable super_read_only system variable and ensure that any inbound replication channels are stopped.")
EXPECT_STDOUT_MATCHES(re.compile(r"ERROR: \[Worker00\d\]: Consistency check has failed"))

testutil.dbug_set("")

#@<> BUG#33697289 terminate the process immediately, it will not stop on its own {not __dbug_off}
testutil.wait_mysqlsh_async(pid, 0)

#@<> BUG#34556560 create a process which will add tables in the background (2) - skipConsistencyChecks {not __dbug_off}
pid = constantly_create_tables()

#@<> BUG#34556560 fail if gtid is disabled and DDL changes - skipConsistencyChecks {not __dbug_off}
testutil.dbug_set("+d,dumper_gtid_disabled")

EXPECT_SUCCESS([ tested_schema ], test_output_absolute, { "consistent": True, "skipConsistencyChecks": True, "showProgress": False, "threads": 1 })
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.")
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: The binlog position has changed during the dump, from: '.+' to: '.+'."))
EXPECT_STDOUT_CONTAINS("NOTE: The 'skipConsistencyChecks' option is set, assuming there were no DDL changes.")
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes were not blocked. The DDL is consistent, the world may resume now.")

testutil.dbug_set("")

#@<> BUG#34556560 terminate the process immediately, it will not stop on its own - skipConsistencyChecks {not __dbug_off}
testutil.wait_mysqlsh_async(pid, 0)

#@<> BUG#33697289 without the process, the dump should succeed
EXPECT_SUCCESS([ tested_schema ], test_output_absolute, { "consistent": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.")
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes were not blocked. The DDL is consistent, the world may resume now.")

#@<> BUG#33697289 fail if binlog and gtid are disabled {not __dbug_off}
testutil.dbug_set("+d,dumper_binlog_disabled,dumper_gtid_disabled")

EXPECT_FAIL("Error: Shell Error (52002)", "While 'Initializing': Unable to lock tables: Consistency check has failed.", test_output_absolute, { "includeSchemas": [ tested_schema ], "consistent": True, "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_CONTAINS(f"""
ERROR: The current user does not have required privileges to execute FLUSH TABLES WITH READ LOCK.
    Backup lock is not {reason} and DDL changes cannot be blocked.
    The gtid_mode system variable is set to OFF or OFF_PERMISSIVE.
    The log_bin system variable is set to OFF or the current user does not have required privileges to execute SHOW MASTER STATUS.
The consistency of the dump cannot be guaranteed.
""")

testutil.dbug_set("")

#@<> BUG#34556560 GTID-based consistency check if too sensitive - setup
def constantly_update_table():
    tables_to_create = 500
    session.run_sql("DROP SCHEMA IF EXISTS !;", [ tested_schema ])
    session.run_sql("CREATE SCHEMA !;", [ tested_schema ])
    for i in range(tables_to_create):
        session.run_sql(f"CREATE TABLE {tested_schema}.{tested_table}_{i} (a int)")
    update_table = f"""v = 0
session.run_sql("DROP SCHEMA IF EXISTS {tested_schema}_2")
session.run_sql("CREATE SCHEMA {tested_schema}_2")
session.run_sql("CREATE TABLE {tested_schema}_2.{tested_table} (a int)")
while True:
    session.run_sql("INSERT INTO {tested_schema}_2.{tested_table} VALUES ({{0}})".format(v))
    v = v + 1
session.close()
"""
    # run a process which constantly updates a table
    pid = testutil.call_mysqlsh_async(["--py", uri], update_table)
    # wait a bit for process to start
    time.sleep(1)
    return pid

#@<> BUG#34556560 create a process which will update a table in the background
pid = constantly_update_table()

#@<> BUG#34556560 - backup lock is not available
EXPECT_SUCCESS([ tested_schema ], test_output_absolute, { "consistent": True, "showProgress": False, "threads": 1 })
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.")
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: The value of the gtid_executed system variable has changed during the dump, from: '.+' to: '.+'."))
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: Checking \d+ recent transactions for schema changes, use the 'skipConsistencyChecks' option to skip this check."))
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes were not blocked. The DDL is consistent, the world may resume now.")

#@<> BUG#34556560 terminate the process immediately
testutil.wait_mysqlsh_async(pid, 0)

#@<> BUG#34556560 create a process which will update a table in the background (2) {not __dbug_off}
pid = constantly_update_table()

#@<> BUG#34556560 - gtid is disabled {not __dbug_off}
testutil.dbug_set("+d,dumper_gtid_disabled")

EXPECT_SUCCESS([ tested_schema ], test_output_absolute, { "consistent": True, "showProgress": False, "threads": 1 })
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes will not be blocked. The dump may fail with an error if schema changes are made while dumping.")
EXPECT_STDOUT_CONTAINS("WARNING: The current user lacks privileges to acquire a global read lock using 'FLUSH TABLES WITH READ LOCK'. Falling back to LOCK TABLES...")
EXPECT_STDOUT_MATCHES(re.compile(r"NOTE: The binlog position has changed during the dump, from: '.+' to: '.+'."))
EXPECT_STDOUT_CONTAINS("NOTE: Checking recent transactions for schema changes, use the 'skipConsistencyChecks' option to skip this check.")
EXPECT_STDOUT_CONTAINS(f"NOTE: Backup lock is not {reason} and DDL changes were not blocked. The DDL is consistent, the world may resume now.")

testutil.dbug_set("")

#@<> BUG#34556560 terminate the process immediately, it will not stop on its own {not __dbug_off}
testutil.wait_mysqlsh_async(pid, 0)

#@<> BUG#34556560 reconnect to the user with full privilages, restore test user account
setup_session()
create_users()

#@<> BUG#34556560 create a process which will add tables in the background - backup lock works {VER(>=8.0.0)}
pid = constantly_create_tables()

#@<> BUG#34556560 test - backup lock works {VER(>=8.0.0)}
EXPECT_SUCCESS([ tested_schema ], test_output_absolute, { "consistent": True, "showProgress": False, "threads": 1 })
EXPECT_STDOUT_CONTAINS("Locking instance for backup")
EXPECT_STDOUT_NOT_CONTAINS("Backup lock is not")
EXPECT_STDOUT_NOT_CONTAINS("skipConsistencyChecks")

#@<> BUG#34556560 terminate the process immediately - backup lock works {VER(>=8.0.0)}
testutil.wait_mysqlsh_async(pid, 0)

#@<> BUG#33697289, BUG#34556560 cleanup
session.run_sql("DROP SCHEMA IF EXISTS !;", [ tested_schema ])
session.run_sql("DROP SCHEMA IF EXISTS !;", [ tested_schema + "_2" ])

#@<> An error should occur when dumping using oci+os://
EXPECT_FAIL("ValueError", "Directory handling for oci+os protocol is not supported.", 'oci+os://sakila')

#@<> BUG#32490714 - running a dump should not change binlog position
[binlog_file, binlog_position, _, _, _] = session.run_sql('SHOW MASTER STATUS;').fetch_one()
EXPECT_SUCCESS([types_schema], test_output_absolute, { "showProgress": False })
[new_binlog_file, new_binlog_position, _, _, _] = session.run_sql('SHOW MASTER STATUS;').fetch_one()

EXPECT_EQ(binlog_file, new_binlog_file, "binlog file should not change")
EXPECT_EQ(binlog_position, new_binlog_position, "binlog position should not change")

#@<> BUG#32515696 dump should not fail if GTID_EXECUTED system variable is not available {not __dbug_off}
testutil.set_trap("mysql", ["sql == SELECT @@GLOBAL.GTID_EXECUTED;"], { "code": 1193, "msg": "Unknown system variable 'GTID_EXECUTED'.", "state": "HY000" })

EXPECT_SUCCESS([types_schema], test_output_absolute, { "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: Failed to fetch value of @@GLOBAL.GTID_EXECUTED.")

testutil.clear_traps("mysql")

#@<> BUG#32515696 dump should not fail if table histograms are not available {VER(>=8.0.0) and not __dbug_off}
testutil.set_trap("mysql", ["sql regex .*number-of-buckets-specified.*"], { "code": 1109, "msg": "Unknown table 'COLUMN_STATISTICS' in information_schema.", "state": "42S02" })

EXPECT_SUCCESS([types_schema], test_output_absolute, { "showProgress": False })
EXPECT_STDOUT_CONTAINS("WARNING: Failed to fetch table histograms.")

testutil.clear_traps("mysql")

#@<> BUG#32430402 metadata should contain information about binlog
EXPECT_SUCCESS([types_schema], test_output_absolute, { "ddlOnly": True, "showProgress": False })

with open(os.path.join(test_output_absolute, "@.json"), encoding="utf-8") as json_file:
    metadata = json.load(json_file)
    EXPECT_EQ(True, "binlogFile" in metadata, "'binlogFile' should be in metadata")
    EXPECT_EQ(True, "binlogPosition" in metadata, "'binlogPosition' should be in metadata")

#@<> BUG#32528110 shell could crash if exception is thrown from the main thread and one of the worker threads is slow to start {not __dbug_off}
testutil.set_trap("mysql", ["sql == SELECT @@GLOBAL.HOSTNAME;"], { "code": 7777, "msg": "Internal error.", "state": "HY000" })
testutil.set_trap("dumper", ["op == WORKER_SLEEP_AT_START", "id == 0"], { "sleep": 1000 })

EXPECT_FAIL("DBError: MySQL Error (7777)", "Internal error.", test_output_absolute, { "showProgress": False })

testutil.clear_traps("mysql")
testutil.clear_traps("dumper")

#@<> BUG#33223635 when JSON output is requested, running a dump with showProgress: true should produce only valid JSON
shutil.rmtree(test_output_absolute, True)
os.mkdir(test_output_absolute)

EXPECT_EQ(0, testutil.call_mysqlsh([uri, "--json=raw", "--interactive=full", "--", "util", "dump-instance", test_output_absolute, "--show-progress=true"]))

for line in testutil.fetch_captured_stdout(False).splitlines():
    EXPECT_NO_THROWS(lambda: json.loads(line), f"testing line: {line}")

#@<> BUG#32109967 run a dump when connected via socket {__os_type != 'windows'}
# connect using socket
setup_session(get_socket_uri(session, uri))
# host should not be specified in URI
EXPECT_FALSE("host" in shell.parse_uri(session.uri))
# run a successful dump
EXPECT_SUCCESS([types_schema], test_output_absolute, { "showProgress": False })
# restore connection
setup_session()

#@<> BUG#34049624 - dumping users from MariaDB is not supported {not __dbug_off}
testutil.dbug_set("+d,dumper_dump_mariadb")

# trying to dump users results in error
EXPECT_FAIL("Error: Shell Error (52037)", "While 'Initializing': Dumping user accounts is currently not supported in MariaDB. Set the 'users' option to false to continue.", test_output_absolute, { "users": True, "dryRun": dry_run, "showProgress": False })
EXPECT_FAIL("Error: Shell Error (52037)", "While 'Initializing': Dumping user accounts is currently not supported in MariaDB. Set the 'users' option to false to continue.", test_output_absolute, { "users": True, "showProgress": False })

# dumping without users works fine
EXPECT_SUCCESS([types_schema], test_output_absolute, { "users": False, "dryRun": dry_run, "showProgress": False })
EXPECT_SUCCESS([types_schema], test_output_absolute, { "users": False, "showProgress": False })

testutil.dbug_set("")

#@<> WL14244 - help entries
util.help('dump_instance')

# WL14244-TSFR_1_1
EXPECT_STDOUT_CONTAINS("""
      - includeSchemas: list of strings (default: empty) - List of schemas to
        be included in the dump.
""")

# WL14244-TSFR_2_1
EXPECT_STDOUT_CONTAINS("""
      - includeTables: list of strings (default: empty) - List of tables or
        views to be included in the dump in the format of schema.table.
""")

# WL14244-TSFR_3_1
EXPECT_STDOUT_CONTAINS("""
      - includeRoutines: list of strings (default: empty) - List of routines to
        be included in the dump in the format of schema.routine.
""")

# WL14244-TSFR_4_1
EXPECT_STDOUT_CONTAINS("""
      - excludeRoutines: list of strings (default: empty) - List of routines to
        be excluded from the dump in the format of schema.routine.
""")

# WL14244-TSFR_5_1
EXPECT_STDOUT_CONTAINS("""
      - includeEvents: list of strings (default: empty) - List of events to be
        included in the dump in the format of schema.event.
""")

# WL14244-TSFR_6_1
EXPECT_STDOUT_CONTAINS("""
      - excludeEvents: list of strings (default: empty) - List of events to be
        excluded from the dump in the format of schema.event.
""")

# WL14244-TSFR_7_1
EXPECT_STDOUT_CONTAINS("""
      - includeTriggers: list of strings (default: empty) - List of triggers to
        be included in the dump in the format of schema.table (all triggers
        from the specified table) or schema.table.trigger (the individual
        trigger).
""")

# WL14244-TSFR_8_1
EXPECT_STDOUT_CONTAINS("""
      - excludeTriggers: list of strings (default: empty) - List of triggers to
        be excluded from the dump in the format of schema.table (all triggers
        from the specified table) or schema.table.trigger (the individual
        trigger).
""")

#@<> WL14244 - helpers
def dump_and_load(options):
    WIPE_STDOUT()
    # remove everything from the server
    wipeout_server(session)
    # create sample DB structure
    session.run_sql("CREATE SCHEMA existing_schema_1")
    session.run_sql("CREATE TABLE existing_schema_1.existing_table (id INT)")
    session.run_sql("CREATE VIEW existing_schema_1.existing_view AS SELECT * FROM existing_schema_1.existing_table")
    session.run_sql("CREATE EVENT existing_schema_1.existing_event ON SCHEDULE EVERY 1 YEAR DO BEGIN END")
    session.run_sql("CREATE FUNCTION existing_schema_1.existing_routine() RETURNS INT DETERMINISTIC RETURN 1")
    session.run_sql("CREATE TRIGGER existing_schema_1.existing_trigger AFTER DELETE ON existing_schema_1.existing_table FOR EACH ROW BEGIN END")
    session.run_sql("CREATE SCHEMA existing_schema_2")
    session.run_sql("CREATE TABLE existing_schema_2.existing_table (id INT)")
    session.run_sql("CREATE VIEW existing_schema_2.existing_view AS SELECT * FROM existing_schema_2.existing_table")
    session.run_sql("CREATE EVENT existing_schema_2.existing_event ON SCHEDULE EVERY 1 YEAR DO BEGIN END")
    session.run_sql("CREATE PROCEDURE existing_schema_2.existing_routine() DETERMINISTIC BEGIN END")
    session.run_sql("CREATE TRIGGER existing_schema_2.existing_trigger AFTER DELETE ON existing_schema_2.existing_table FOR EACH ROW BEGIN END")
    # we're only interested in DDL, progress is not important
    options["ddlOnly"] = True
    options["showProgress"] = False
    # do the dump
    shutil.rmtree(test_output_absolute, True)
    util.dump_instance(test_output_absolute, options)
    # remove everything from the server once again, load the dump
    wipeout_server(session)
    util.load_dump(test_output_absolute, { "showProgress": False })
    # fetch data about the current DB structure
    return snapshot_instance(session)

def entries(snapshot, keys = []):
    entry = snapshot["schemas"]
    for key in keys:
        entry = entry[key]
    return sorted(list(entry.keys()))

#@<> WL14244-TSFR_1_2
EXPECT_EQ(["existing_schema_1", "existing_schema_2"], entries(dump_and_load({})))
EXPECT_EQ(["existing_schema_1", "existing_schema_2"], entries(dump_and_load({ "includeSchemas": [] })))

#@<> WL14244-TSFR_1_3
EXPECT_EQ(["existing_schema_2"], entries(dump_and_load({ "includeSchemas": [ "existing_schema_2", "non_existing_schema" ] })))

#@<> WL14244-TSFR_1_4
# BUG#33502098
EXPECT_FAIL("Error: Shell Error (52010)", "While 'Gathering information': Filters for schemas result in an empty set.", test_output_relative, { "includeSchemas": [ "non_existing_schema" ], "users": False })

#@<> WL14244 - includeTables - invalid values
EXPECT_FAIL("ValueError", "Argument #2: The table to be included must be in the following form: schema.table, with optional backtick quotes, wrong value: 'table'.", test_output_absolute, { "includeTables": [ "table" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse table to be included 'table.@': Invalid character in identifier", test_output_absolute, { "includeTables": [ "table.@" ] })

#@<> WL14244-TSFR_2_3
snapshot = dump_and_load({})
EXPECT_EQ(["existing_table"], entries(snapshot, ["existing_schema_1", "tables"]))
EXPECT_EQ(["existing_view"], entries(snapshot, ["existing_schema_1", "views"]))
EXPECT_EQ(["existing_table"], entries(snapshot, ["existing_schema_2", "tables"]))
EXPECT_EQ(["existing_view"], entries(snapshot, ["existing_schema_2", "views"]))

snapshot = dump_and_load({ "includeTables": [] })
EXPECT_EQ(["existing_table"], entries(snapshot, ["existing_schema_1", "tables"]))
EXPECT_EQ(["existing_view"], entries(snapshot, ["existing_schema_1", "views"]))
EXPECT_EQ(["existing_table"], entries(snapshot, ["existing_schema_2", "tables"]))
EXPECT_EQ(["existing_view"], entries(snapshot, ["existing_schema_2", "views"]))

#@<> WL14244-TSFR_2_5
snapshot = dump_and_load({ "includeTables": ['existing_schema_1.existing_table', 'existing_schema_1.non_existing_table', 'existing_schema_1.existing_view', 'existing_schema_1.non_existing_view', 'non_existing_schema.view', 'non_existing_schema.table'] })
EXPECT_EQ(["existing_table"], entries(snapshot, ["existing_schema_1", "tables"]))
EXPECT_EQ(["existing_view"], entries(snapshot, ["existing_schema_1", "views"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "tables"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "views"]))

#@<> WL14244 - includeRoutines - invalid values
EXPECT_FAIL("ValueError", "Argument #2: The routine to be included must be in the following form: schema.routine, with optional backtick quotes, wrong value: 'routine'.", test_output_absolute, { "includeRoutines": [ "routine" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse routine to be included 'schema.@': Invalid character in identifier", test_output_absolute, { "includeRoutines": [ "schema.@" ] })

#@<> WL14244-TSFR_3_4
snapshot = dump_and_load({})
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_1", "functions"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "procedures"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "functions"]))
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_2", "procedures"]))

snapshot = dump_and_load({ "includeRoutines": [] })
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_1", "functions"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "procedures"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "functions"]))
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_2", "procedures"]))

#@<> WL14244-TSFR_3_7
snapshot = dump_and_load({ "includeRoutines": ['existing_schema_1.existing_routine', 'existing_schema_1.non_existing_routine', 'non_existing_schema.routine'] })
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_1", "functions"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "procedures"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "functions"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "procedures"]))

#@<> WL14244 - excludeRoutines - invalid values
EXPECT_FAIL("ValueError", "Argument #2: The routine to be excluded must be in the following form: schema.routine, with optional backtick quotes, wrong value: 'routine'.", test_output_absolute, { "excludeRoutines": [ "routine" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse routine to be excluded 'schema.@': Invalid character in identifier", test_output_absolute, { "excludeRoutines": [ "schema.@" ] })

#@<> WL14244-TSFR_4_4
snapshot = dump_and_load({})
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_1", "functions"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "procedures"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "functions"]))
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_2", "procedures"]))

snapshot = dump_and_load({ "excludeRoutines": [] })
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_1", "functions"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "procedures"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "functions"]))
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_2", "procedures"]))

#@<> WL14244-TSFR_4_7
snapshot = dump_and_load({ "excludeRoutines": ['existing_schema_1.existing_routine', 'existing_schema_1.non_existing_routine', 'non_existing_schema.routine'] })
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "functions"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "procedures"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "functions"]))
EXPECT_EQ(["existing_routine"], entries(snapshot, ["existing_schema_2", "procedures"]))

#@<> WL14244 - includeEvents - invalid values
EXPECT_FAIL("ValueError", "Argument #2: The event to be included must be in the following form: schema.event, with optional backtick quotes, wrong value: 'event'.", test_output_absolute, { "includeEvents": [ "event" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse event to be included 'schema.@': Invalid character in identifier", test_output_absolute, { "includeEvents": [ "schema.@" ] })

#@<> WL14244-TSFR_5_4
snapshot = dump_and_load({})
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_1", "events"]))
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_2", "events"]))

snapshot = dump_and_load({ "includeEvents": [] })
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_1", "events"]))
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_2", "events"]))

#@<> WL14244-TSFR_5_7
snapshot = dump_and_load({ "includeEvents": ['existing_schema_1.existing_event', 'existing_schema_1.non_existing_event', 'non_existing_schema.event'] })
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_1", "events"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "events"]))

#@<> WL14244 - excludeEvents - invalid values
EXPECT_FAIL("ValueError", "Argument #2: The event to be excluded must be in the following form: schema.event, with optional backtick quotes, wrong value: 'event'.", test_output_absolute, { "excludeEvents": [ "event" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse event to be excluded 'schema.@': Invalid character in identifier", test_output_absolute, { "excludeEvents": [ "schema.@" ] })

#@<> WL14244-TSFR_6_4
snapshot = dump_and_load({})
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_1", "events"]))
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_2", "events"]))

snapshot = dump_and_load({ "excludeEvents": [] })
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_1", "events"]))
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_2", "events"]))

#@<> WL14244-TSFR_6_7
snapshot = dump_and_load({ "excludeEvents": ['existing_schema_1.existing_event', 'existing_schema_1.non_existing_event', 'non_existing_schema.event'] })
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "events"]))
EXPECT_EQ(["existing_event"], entries(snapshot, ["existing_schema_2", "events"]))

#@<> WL14244 - includeTriggers - invalid values
EXPECT_FAIL("ValueError", "Argument #2: The trigger to be included must be in the following form: schema.table or schema.table.trigger, with optional backtick quotes, wrong value: 'trigger'.", test_output_absolute, { "includeTriggers": [ "trigger" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse trigger to be included 'schema.@': Invalid character in identifier", test_output_absolute, { "includeTriggers": [ "schema.@" ] })

#@<> WL14244-TSFR_7_5
snapshot = dump_and_load({})
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_1", "tables", "existing_table", "triggers"]))
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_2", "tables", "existing_table", "triggers"]))

snapshot = dump_and_load({ "includeTriggers": [] })
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_1", "tables", "existing_table", "triggers"]))
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_2", "tables", "existing_table", "triggers"]))

#@<> WL14244-TSFR_7_9
snapshot = dump_and_load({ "includeTriggers": ['existing_schema_1.existing_table', 'existing_schema_1.non_existing_table', 'non_existing_schema.table', 'existing_schema_2.existing_table.existing_trigger', 'existing_schema_1.existing_table.non_existing_trigger'] })
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_1", "tables", "existing_table", "triggers"]))
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_2", "tables", "existing_table", "triggers"]))

#@<> WL14244 - excludeTriggers - invalid values
EXPECT_FAIL("ValueError", "Argument #2: The trigger to be excluded must be in the following form: schema.table or schema.table.trigger, with optional backtick quotes, wrong value: 'trigger'.", test_output_absolute, { "excludeTriggers": [ "trigger" ] })
EXPECT_FAIL("ValueError", "Argument #2: Failed to parse trigger to be excluded 'schema.@': Invalid character in identifier", test_output_absolute, { "excludeTriggers": [ "schema.@" ] })

#@<> WL14244-TSFR_8_5
snapshot = dump_and_load({})
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_1", "tables", "existing_table", "triggers"]))
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_2", "tables", "existing_table", "triggers"]))

snapshot = dump_and_load({ "excludeTriggers": [] })
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_1", "tables", "existing_table", "triggers"]))
EXPECT_EQ(["existing_trigger"], entries(snapshot, ["existing_schema_2", "tables", "existing_table", "triggers"]))

#@<> WL14244-TSFR_8_9
snapshot = dump_and_load({ "excludeTriggers": ['existing_schema_1.existing_table', 'existing_schema_1.non_existing_table', 'non_existing_schema.table', 'existing_schema_2.existing_table.existing_trigger', 'existing_schema_1.existing_table.non_existing_trigger'] })
EXPECT_EQ([], entries(snapshot, ["existing_schema_1", "tables", "existing_table", "triggers"]))
EXPECT_EQ([], entries(snapshot, ["existing_schema_2", "tables", "existing_table", "triggers"]))

#@<> WL14244 - cleanup
session.run_sql("DROP SCHEMA IF EXISTS existing_schema_1")
session.run_sql("DROP SCHEMA IF EXISTS existing_schema_2")

#@<> includeX + excludeX conflicts - helpers
def dump_with_conflicts(options, throws = True):
    WIPE_STDOUT()
    # we're only interested in warnings
    options["dryRun"] = True
    options["showProgress"] = False
    # do the dump
    shutil.rmtree(test_output_absolute, True)
    if throws:
        EXPECT_THROWS(lambda: util.dump_instance(test_output_absolute, options), "ValueError: Util.dump_instance: Conflicting filtering options")
    else:
        # there could be some other exceptions, we ignore them
        try:
            util.dump_instance(test_output_absolute, options)
        except Exception as e:
            print("Exception:", e)

#@<> includeSchemas + excludeSchemas conflicts
# no conflicts
dump_with_conflicts({ "includeSchemas": [], "excludeSchemas": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeSchemas")
EXPECT_STDOUT_NOT_CONTAINS("excludeSchemas")

dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeSchemas": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeSchemas")
EXPECT_STDOUT_NOT_CONTAINS("excludeSchemas")

dump_with_conflicts({ "includeSchemas": [], "excludeSchemas": [ "a" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeSchemas")
EXPECT_STDOUT_NOT_CONTAINS("excludeSchemas")

dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeSchemas": [ "b" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeSchemas")
EXPECT_STDOUT_NOT_CONTAINS("excludeSchemas")

# conflicts
dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeSchemas": [ "a" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeSchemas and excludeSchemas options contain a schema `a`.")

dump_with_conflicts({ "includeSchemas": [ "a", "b" ], "excludeSchemas": [ "a" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeSchemas and excludeSchemas options contain a schema `a`.")

dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeSchemas": [ "a", "b" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeSchemas and excludeSchemas options contain a schema `a`.")

#@<> includeTables + excludeTables conflicts
# no conflicts
dump_with_conflicts({ "includeTables": [], "excludeTables": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeTables": [ "a.t" ], "excludeTables": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeTables": [], "excludeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeTables": [ "a.t" ], "excludeTables": [ "b.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeTables": [ "a.t" ], "excludeTables": [ "a.t1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "includeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "excludeSchemas": [], "includeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeSchemas": [], "includeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeSchemas": [ "a" ], "includeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "excludeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "excludeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "excludeSchemas": [], "excludeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeSchemas": [], "excludeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeTables": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTables")
EXPECT_STDOUT_NOT_CONTAINS("excludeTables")

# conflicts
dump_with_conflicts({ "includeTables": [ "a.t" ], "excludeTables": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTables and excludeTables options contain a table `a`.`t`.")

dump_with_conflicts({ "includeTables": [ "a.t", "b.t" ], "excludeTables": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTables and excludeTables options contain a table `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`t`")

dump_with_conflicts({ "includeTables": [ "a.t", "a.t1" ], "excludeTables": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTables and excludeTables options contain a table `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`t1`")

dump_with_conflicts({ "includeTables": [ "a.t" ], "excludeTables": [ "a.t", "b.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTables and excludeTables options contain a table `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`t`")

dump_with_conflicts({ "includeTables": [ "a.t" ], "excludeTables": [ "a.t", "a.t1" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTables and excludeTables options contain a table `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`t1`")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "includeTables": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTables option contains a table `a`.`t` which refers to an excluded schema.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "includeTables": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTables option contains a table `a`.`t` which refers to a schema which was not included in the dump.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "excludeTables": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The excludeTables option contains a table `a`.`t` which refers to a schema which was not included in the dump.")

#@<> includeEvents + excludeEvents conflicts
# no conflicts
dump_with_conflicts({ "includeEvents": [], "excludeEvents": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeEvents": [ "a.e" ], "excludeEvents": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeEvents": [], "excludeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeEvents": [ "a.e" ], "excludeEvents": [ "b.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeEvents": [ "a.e" ], "excludeEvents": [ "a.e1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "includeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "excludeSchemas": [], "includeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeSchemas": [], "includeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeSchemas": [ "a" ], "includeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "excludeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "excludeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "excludeSchemas": [], "excludeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeSchemas": [], "excludeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeEvents": [ "a.e" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeEvents")
EXPECT_STDOUT_NOT_CONTAINS("excludeEvents")

# conflicts
dump_with_conflicts({ "includeEvents": [ "a.e" ], "excludeEvents": [ "a.e" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeEvents and excludeEvents options contain an event `a`.`e`.")

dump_with_conflicts({ "includeEvents": [ "a.e", "b.e" ], "excludeEvents": [ "a.e" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeEvents and excludeEvents options contain an event `a`.`e`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`e`")

dump_with_conflicts({ "includeEvents": [ "a.e", "a.e1" ], "excludeEvents": [ "a.e" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeEvents and excludeEvents options contain an event `a`.`e`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`e1`")

dump_with_conflicts({ "includeEvents": [ "a.e" ], "excludeEvents": [ "a.e", "b.e" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeEvents and excludeEvents options contain an event `a`.`e`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`e`")

dump_with_conflicts({ "includeEvents": [ "a.e" ], "excludeEvents": [ "a.e", "a.e1" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeEvents and excludeEvents options contain an event `a`.`e`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`e1`")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "includeEvents": [ "a.e" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeEvents option contains an event `a`.`e` which refers to an excluded schema.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "includeEvents": [ "a.e" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeEvents option contains an event `a`.`e` which refers to a schema which was not included in the dump.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "excludeEvents": [ "a.e" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The excludeEvents option contains an event `a`.`e` which refers to a schema which was not included in the dump.")

#@<> includeRoutines + excludeRoutines conflicts
# no conflicts
dump_with_conflicts({ "includeRoutines": [], "excludeRoutines": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeRoutines": [ "a.r" ], "excludeRoutines": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeRoutines": [], "excludeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeRoutines": [ "a.r" ], "excludeRoutines": [ "b.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeRoutines": [ "a.r" ], "excludeRoutines": [ "a.r1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "includeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "excludeSchemas": [], "includeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeSchemas": [], "includeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeSchemas": [ "a" ], "includeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "excludeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "excludeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "excludeSchemas": [], "excludeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeSchemas": [], "excludeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeRoutines": [ "a.r" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeRoutines")
EXPECT_STDOUT_NOT_CONTAINS("excludeRoutines")

# conflicts
dump_with_conflicts({ "includeRoutines": [ "a.r" ], "excludeRoutines": [ "a.r" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeRoutines and excludeRoutines options contain a routine `a`.`r`.")

dump_with_conflicts({ "includeRoutines": [ "a.r", "b.r" ], "excludeRoutines": [ "a.r" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeRoutines and excludeRoutines options contain a routine `a`.`r`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`r`")

dump_with_conflicts({ "includeRoutines": [ "a.r", "a.r1" ], "excludeRoutines": [ "a.r" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeRoutines and excludeRoutines options contain a routine `a`.`r`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`r1`")

dump_with_conflicts({ "includeRoutines": [ "a.r" ], "excludeRoutines": [ "a.r", "b.r" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeRoutines and excludeRoutines options contain a routine `a`.`r`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`r`")

dump_with_conflicts({ "includeRoutines": [ "a.r" ], "excludeRoutines": [ "a.r", "a.r1" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeRoutines and excludeRoutines options contain a routine `a`.`r`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`r1`")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "includeRoutines": [ "a.r" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeRoutines option contains a routine `a`.`r` which refers to an excluded schema.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "includeRoutines": [ "a.r" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeRoutines option contains a routine `a`.`r` which refers to a schema which was not included in the dump.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "excludeRoutines": [ "a.r" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The excludeRoutines option contains a routine `a`.`r` which refers to a schema which was not included in the dump.")

#@<> includeTriggers + excludeTriggers conflicts
# no conflicts
dump_with_conflicts({ "includeTriggers": [], "excludeTriggers": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [], "excludeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [], "excludeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "b.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "b.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "b.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "b.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "a.t1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "a.t1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "a.t1.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "a.t1.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "includeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeSchemas": [], "includeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeSchemas": [], "includeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeSchemas": [ "a" ], "includeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "excludeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeSchemas": [ "b" ], "excludeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeSchemas": [], "excludeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeSchemas": [], "excludeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeSchemas": [ "a" ], "excludeTriggers": [ "a.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeTables": [ "b.t" ], "includeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeTables": [], "includeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTables": [], "includeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTables": [ "a.t" ], "includeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeTables": [ "a.t" ], "excludeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeTables": [ "b.t" ], "excludeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "excludeTables": [], "excludeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTables": [], "excludeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

dump_with_conflicts({ "includeTables": [ "a.t" ], "excludeTriggers": [ "a.t.t" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeTriggers")
EXPECT_STDOUT_NOT_CONTAINS("excludeTriggers")

# conflicts
dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a filter `a`.`t`.")

dump_with_conflicts({ "includeTriggers": [ "a.t", "b.t" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a filter `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`t`")

dump_with_conflicts({ "includeTriggers": [ "a.t", "a.t1" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a filter `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`t1`")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "a.t", "b.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a filter `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`t`")

dump_with_conflicts({ "includeTriggers": [ "a.t" ], "excludeTriggers": [ "a.t", "a.t1" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a filter `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`t1`")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a trigger `a`.`t`.`t`.")

dump_with_conflicts({ "includeTriggers": [ "a.t.t", "b.t.t" ], "excludeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a trigger `a`.`t`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`t`")

dump_with_conflicts({ "includeTriggers": [ "a.t.t", "a.t1.t" ], "excludeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a trigger `a`.`t`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`t1`")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "a.t.t", "b.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a trigger `a`.`t`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`t`")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "a.t.t", "a.t1.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeTriggers and excludeTriggers options contain a trigger `a`.`t`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`t1`")

dump_with_conflicts({ "includeTriggers": [ "a.t.t" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a trigger `a`.`t`.`t` which is excluded by the value of the excludeTriggers option: `a`.`t`.")

dump_with_conflicts({ "includeTriggers": [ "a.t.t", "b.t.t" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a trigger `a`.`t`.`t` which is excluded by the value of the excludeTriggers option: `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`b`.`t`")

dump_with_conflicts({ "includeTriggers": [ "a.t.t", "a.t1.t" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a trigger `a`.`t`.`t` which is excluded by the value of the excludeTriggers option: `a`.`t`.")
EXPECT_STDOUT_NOT_CONTAINS("`a`.`t1`")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "includeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a filter `a`.`t` which refers to an excluded schema.")

dump_with_conflicts({ "excludeSchemas": [ "a" ], "includeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a trigger `a`.`t`.`t` which refers to an excluded schema.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "includeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a filter `a`.`t` which refers to a schema which was not included in the dump.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "includeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a trigger `a`.`t`.`t` which refers to a schema which was not included in the dump.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The excludeTriggers option contains a filter `a`.`t` which refers to a schema which was not included in the dump.")

dump_with_conflicts({ "includeSchemas": [ "b" ], "excludeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The excludeTriggers option contains a trigger `a`.`t`.`t` which refers to a schema which was not included in the dump.")

dump_with_conflicts({ "excludeTables": [ "a.t" ], "includeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a filter `a`.`t` which refers to an excluded table.")

dump_with_conflicts({ "excludeTables": [ "a.t" ], "includeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a trigger `a`.`t`.`t` which refers to an excluded table.")

dump_with_conflicts({ "includeTables": [ "b.t" ], "includeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a filter `a`.`t` which refers to a table which was not included in the dump.")

dump_with_conflicts({ "includeTables": [ "b.t" ], "includeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeTriggers option contains a trigger `a`.`t`.`t` which refers to a table which was not included in the dump.")

dump_with_conflicts({ "includeTables": [ "b.t" ], "excludeTriggers": [ "a.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The excludeTriggers option contains a filter `a`.`t` which refers to a table which was not included in the dump.")

dump_with_conflicts({ "includeTables": [ "b.t" ], "excludeTriggers": [ "a.t.t" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The excludeTriggers option contains a trigger `a`.`t`.`t` which refers to a table which was not included in the dump.")

#@<> includeUsers + excludeUsers conflicts
# no conflicts
dump_with_conflicts({ "includeUsers": [], "excludeUsers": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [ "u" ], "excludeUsers": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [], "excludeUsers": [ "u" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [], "excludeUsers": [ "u@h" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [ "u" ], "excludeUsers": [ "u1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [ "u1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [ "u" ], "excludeUsers": [ "u1@h" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [ "u@h1" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

dump_with_conflicts({ "includeUsers": [ "u" ], "excludeUsers": [ "u@h" ] }, False)
EXPECT_STDOUT_NOT_CONTAINS("includeUsers")
EXPECT_STDOUT_NOT_CONTAINS("excludeUsers")

# conflicts
dump_with_conflicts({ "includeUsers": [ "u" ], "excludeUsers": [ "u" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@''.")

dump_with_conflicts({ "includeUsers": [ "u", "u1" ], "excludeUsers": [ "u" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@''.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u" ], "excludeUsers": [ "u", "u1" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@''.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [ "u@h" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@'h'.")

dump_with_conflicts({ "includeUsers": [ "u@h", "u1" ], "excludeUsers": [ "u@h" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@'h'.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u@h", "u1@h" ], "excludeUsers": [ "u@h" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@'h'.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [ "u@h", "u1" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@'h'.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [ "u@h", "u1@h" ] })
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@'h'.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [ "u" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeUsers option contains a user 'u'@'h' which is excluded by the value of the excludeUsers option: 'u'@''.")

dump_with_conflicts({ "includeUsers": [ "u@h", "u1" ], "excludeUsers": [ "u" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeUsers option contains a user 'u'@'h' which is excluded by the value of the excludeUsers option: 'u'@''.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u@h", "u1@h" ], "excludeUsers": [ "u" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeUsers option contains a user 'u'@'h' which is excluded by the value of the excludeUsers option: 'u'@''.")
EXPECT_STDOUT_NOT_CONTAINS("u1")

dump_with_conflicts({ "includeUsers": [ "u@h", "u" ], "excludeUsers": [ "u" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeUsers option contains a user 'u'@'h' which is excluded by the value of the excludeUsers option: 'u'@''.")
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@''.")

dump_with_conflicts({ "includeUsers": [ "u@h" ], "excludeUsers": [ "u", "u@h" ] })
EXPECT_STDOUT_CONTAINS("ERROR: The includeUsers option contains a user 'u'@'h' which is excluded by the value of the excludeUsers option: 'u'@''.")
EXPECT_STDOUT_CONTAINS("ERROR: Both includeUsers and excludeUsers options contain a user 'u'@'h'.")

#@<> WL15311 - setup
schema_name = "wl15311"
no_partitions_table_name = "no_partitions"
no_partitions_table_name_quoted = quote_identifier(schema_name, no_partitions_table_name)
partitions_table_name = "partitions"
partitions_table_name_quoted = quote_identifier(schema_name, partitions_table_name)
subpartitions_table_name = "subpartitions"
subpartitions_table_name_quoted = quote_identifier(schema_name, subpartitions_table_name)
all_tables = [ no_partitions_table_name, partitions_table_name, subpartitions_table_name ]
subpartition_prefix = "@o" if __os_type == "windows" else "@ó"

create_all_schemas()
all_schemas.append(schema_name)

session.run_sql("DROP SCHEMA IF EXISTS !", [schema_name])
session.run_sql("CREATE SCHEMA IF NOT EXISTS !", [schema_name])

session.run_sql("CREATE TABLE !.! (`id` int NOT NULL AUTO_INCREMENT PRIMARY KEY, `data` blob)", [ schema_name, no_partitions_table_name ])

session.run_sql("""CREATE TABLE !.!
(`id` int NOT NULL AUTO_INCREMENT PRIMARY KEY, `data` blob)
PARTITION BY RANGE (`id`)
(PARTITION x0 VALUES LESS THAN (10000),
 PARTITION x1 VALUES LESS THAN (20000),
 PARTITION x2 VALUES LESS THAN (30000),
 PARTITION x3 VALUES LESS THAN MAXVALUE)""", [ schema_name, partitions_table_name ])

session.run_sql(f"""CREATE TABLE !.!
(`id` int, `data` blob)
PARTITION BY RANGE (`id`)
SUBPARTITION BY KEY (id)
SUBPARTITIONS 2
(PARTITION `{subpartition_prefix}0` VALUES LESS THAN (10000),
 PARTITION `{subpartition_prefix}1` VALUES LESS THAN (20000),
 PARTITION `{subpartition_prefix}2` VALUES LESS THAN (30000),
 PARTITION `{subpartition_prefix}3` VALUES LESS THAN MAXVALUE)""", [ schema_name, subpartitions_table_name ])

for x in range(4):
    session.run_sql(f"""INSERT INTO !.! (`data`) VALUES {",".join([f"('{random_string(100,200)}')" for i in range(10000)])}""", [ schema_name, partitions_table_name ])
session.run_sql("INSERT INTO !.! SELECT * FROM !.!", [ schema_name, subpartitions_table_name, schema_name, partitions_table_name ])
session.run_sql("INSERT INTO !.! SELECT * FROM !.!", [ schema_name, no_partitions_table_name, schema_name, partitions_table_name ])

for table in all_tables:
    session.run_sql("ANALYZE TABLE !.!;", [ schema_name, table ])

#@<> WL15311_TSFR_3_1
help_text = """
      - where: dictionary (default: not set) - A key-value pair of a table name
        in the format of schema.table and a valid SQL condition expression used
        to filter the data being exported.
"""
EXPECT_TRUE(help_text in util.help("dump_instance"))

#@<> WL15311_TSFR_3_1_1, WL15311_TSFR_3_2_1
TEST_MAP_OF_STRINGS_OPTION("where")

#@<> WL15311_TSFR_3_1_1_1
EXPECT_FAIL("ValueError", "Argument #2: The table name key of the 'where' option must be in the following form: schema.table, with optional backtick quotes, wrong value: 'no_dot'.", test_output_absolute, {"where": { "no_dot": "1 = 1" }})

#@<> WL15311_TSFR_3_1_1_2
TEST_DUMP_AND_LOAD([ schema_name ], { "where": { no_partitions_table_name_quoted: "id > 12345", subpartitions_table_name_quoted: "" } })
EXPECT_GT(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))
# WL15311_TSFR_3_2_5_1
EXPECT_EQ(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))
EXPECT_EQ(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "where": { no_partitions_table_name_quoted: "id > 12345 AND (id < 23456)", partitions_table_name_quoted: "id > 12345" } })
EXPECT_GT(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))
EXPECT_GT(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))

#@<> WL15311_TSFR_3_1_2_1
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "ddlOnly": True, "where": { no_partitions_table_name_quoted: "id > 12345" }, "showProgress": False })

#@<> WL15311_TSFR_3_1_2_2
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "dryRun": True, "where": { no_partitions_table_name_quoted: "id > 12345" }, "showProgress": False })

#@<> WL15311_TSFR_3_1_2_3
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "includeTables": [ partitions_table_name_quoted ], "where": { no_partitions_table_name_quoted: "id > 12345" }, "showProgress": False })

#@<> WL15311_TSFR_3_1_2_4
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "excludeTables": [ no_partitions_table_name_quoted ], "where": { no_partitions_table_name_quoted: "id > 12345" }, "showProgress": False })

#@<> WL15311_TSFR_3_1_2_5
TEST_DUMP_AND_LOAD([ schema_name, types_schema ], { "excludeSchemas": [ types_schema ], "where": { no_partitions_table_name_quoted: "id > 12345", quote_identifier(types_schema, types_schema_tables[0]): "1=1" }, "showProgress": False })

#@<> WL15311_TSFR_3_1_2_10 - schema or table do not exist
TEST_DUMP_AND_LOAD([ schema_name ], { "where": { quote_identifier("schema", "table"): "1 = 2", quote_identifier(schema_name, "table"): "1 = 2" } })

#@<> WL15311_TSFR_3_2_1_1
TEST_DUMP_AND_LOAD([ schema_name ], { "where": { no_partitions_table_name_quoted: "1 = 2", partitions_table_name_quoted: "1 = 1" } })
EXPECT_EQ(0, count_rows(verification_schema, no_partitions_table_name))
EXPECT_EQ(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))

#@<> WL15311_TSFR_3_2_3_1
EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_absolute, { "where": { no_partitions_table_name_quoted: "THIS_IS_NO_SQL" }, "showProgress": False }, True)
EXPECT_STDOUT_CONTAINS("MySQL Error 1054 (42S22): Unknown column 'THIS_IS_NO_SQL' in 'where clause'")

WIPE_STDOUT()
EXPECT_FAIL("Error: Shell Error (52006)", re.compile(r"While '.*': Fatal error during dump"), test_output_absolute, { "where": { no_partitions_table_name_quoted: "1 = 1 ; DROP TABLE mysql.user ; SELECT 1 FROM DUAL" }, "showProgress": False }, True)
EXPECT_STDOUT_CONTAINS("MySQL Error 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '; DROP TABLE mysql.user ; SELECT 1 FROM DUAL) ORDER BY")

WIPE_STDOUT()
EXPECT_FAIL("ValueError", f"Argument #2: Malformed condition used for table '{schema_name}'.'{no_partitions_table_name}': 1 = 1) --", test_output_absolute, { "where": { no_partitions_table_name_quoted: "1 = 1) --" }, "showProgress": False })

WIPE_STDOUT()
EXPECT_FAIL("ValueError", f"Argument #2: Malformed condition used for table '{schema_name}'.'{no_partitions_table_name}': (1 = 1", test_output_absolute, { "where": { no_partitions_table_name_quoted: "(1 = 1" }, "showProgress": False })


#@<> WL15311_TSFR_3_2_4_1
TEST_DUMP_AND_LOAD([ schema_name ], {})
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "where": {} })
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "where": { no_partitions_table_name_quoted: "" } })
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))

#@<> WL15311_TSFR_4_1
help_text = """
      - partitions: dictionary (default: not set) - A key-value pair of a table
        name in the format of schema.table and a list of valid partition names
        used to limit the data export to just the specified partitions.
"""
EXPECT_TRUE(help_text in util.help("dump_instance"))

#@<> WL15311_TSFR_4_1_1, WL15311_TSFR_4_2_1, WL15311_TSFR_4_2_2
TEST_MAP_OF_ARRAY_OF_STRINGS_OPTION("partitions")

#@<> WL15311_TSFR_4_1_1_1
EXPECT_FAIL("ValueError", "Argument #2: The table name key of the 'partitions' option must be in the following form: schema.table, with optional backtick quotes, wrong value: 'no_dot'.", test_output_absolute, {"partitions": { "no_dot": [ "p0" ] }})

#@<> WL15311_TSFR_4_1_1_2
TEST_DUMP_AND_LOAD([ schema_name ], { "where": { partitions_table_name_quoted: "1 = 1" }, "partitions": { partitions_table_name_quoted: [ "x1" ] } })
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))
EXPECT_GT(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "where": { partitions_table_name_quoted: "id > 12345" }, "partitions": { partitions_table_name_quoted: [ "x1" ] } })
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))
EXPECT_GT(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "where": { partitions_table_name_quoted: "id > 12345" }, "partitions": { partitions_table_name_quoted: [ "x1", "x2" ] } })
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))
EXPECT_GT(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "where": { partitions_table_name_quoted: "id > 12345" }, "partitions": { partitions_table_name_quoted: [ "x0" ] } })
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))
EXPECT_EQ(0, count_rows(verification_schema, partitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "where": { partitions_table_name_quoted: "id > 12345" }, "partitions": { subpartitions_table_name_quoted: [ f"{subpartition_prefix}1" ] } })
EXPECT_EQ(count_rows(schema_name, no_partitions_table_name), count_rows(verification_schema, no_partitions_table_name))
EXPECT_GT(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))
EXPECT_GT(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

#@<> WL15311_TSFR_4_2_1_1, WL15311_TSFR_4_2_2_1
TEST_DUMP_AND_LOAD([ schema_name ], { "partitions": { subpartitions_table_name_quoted: [ f"{subpartition_prefix}1", f"{subpartition_prefix}2" ] } })
EXPECT_GT(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "partitions": { subpartitions_table_name_quoted: [ f"{subpartition_prefix}1", f"{subpartition_prefix}2sp0" ] } })
EXPECT_GT(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "partitions": { subpartitions_table_name_quoted: [ f"{subpartition_prefix}1sp0", f"{subpartition_prefix}2sp0" ] } })
EXPECT_GT(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

#@<> WL15311_TSFR_4_1_2_1
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "ddlOnly": True, "partitions": { partitions_table_name_quoted: [ "x1" ] }, "showProgress": False })

#@<> WL15311_TSFR_4_1_2_2
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "dryRun": True, "partitions": { partitions_table_name_quoted: [ "x1" ] }, "showProgress": False })

#@<> WL15311_TSFR_4_1_2_3
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "includeTables": [ subpartitions_table_name_quoted ], "partitions": { partitions_table_name_quoted: [ "x1" ] }, "showProgress": False })

#@<> WL15311_TSFR_4_1_2_4
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "excludeTables": [ partitions_table_name_quoted ], "partitions": { partitions_table_name_quoted: [ "x1" ] }, "showProgress": False })

#@<> WL15311_TSFR_4_1_2_5
EXPECT_SUCCESS(None, test_output_absolute, { "excludeSchemas": [ types_schema ], "partitions": { partitions_table_name_quoted: [ "x1" ], quote_identifier(types_schema, types_schema_tables[0]): [ "x1" ] }, "showProgress": False })

#@<> WL15311_TSFR_4_1_2_10 - schema or table do not exist
TEST_DUMP_AND_LOAD([ schema_name ], { "partitions": { quote_identifier("schema", "table"): [ "x1" ], quote_identifier(schema_name, "table"): [ "x1" ] } })

#@<> WL15311_TSFR_4_2_3_1
EXPECT_FAIL("ValueError", "Invalid partitions", test_output_absolute, { "partitions": { subpartitions_table_name_quoted: [ "SELECT 1" ] }, "showProgress": False })
EXPECT_STDOUT_CONTAINS(f"ERROR: Following partitions were not found in table '{schema_name}'.'{subpartitions_table_name}': 'SELECT 1'")

WIPE_STDOUT()
EXPECT_FAIL("ValueError", "Invalid partitions", test_output_absolute, { "partitions": { subpartitions_table_name_quoted: [ f"{subpartition_prefix}9" ] }, "showProgress": False })
EXPECT_STDOUT_CONTAINS(f"ERROR: Following partitions were not found in table '{schema_name}'.'{subpartitions_table_name}': '{subpartition_prefix}9'")

WIPE_STDOUT()
EXPECT_FAIL("ValueError", "Invalid partitions", test_output_absolute, { "partitions": { subpartitions_table_name_quoted: [ f"{subpartition_prefix}9", f"{subpartition_prefix}1sp9" ] }, "showProgress": False })
EXPECT_STDOUT_CONTAINS(f"ERROR: Following partitions were not found in table '{schema_name}'.'{subpartitions_table_name}': '{subpartition_prefix}1sp9', '{subpartition_prefix}9'")

WIPE_STDOUT()
EXPECT_FAIL("ValueError", "Invalid partitions", test_output_absolute, { "partitions": { partitions_table_name_quoted: [ "x6" ], subpartitions_table_name_quoted: [ f"{subpartition_prefix}9" ] }, "showProgress": False })
EXPECT_STDOUT_CONTAINS(f"ERROR: Following partitions were not found in table '{schema_name}'.'{subpartitions_table_name}': '{subpartition_prefix}9'")
EXPECT_STDOUT_CONTAINS(f"ERROR: Following partitions were not found in table '{schema_name}'.'{partitions_table_name}': 'x6'")

#@<> WL15311_TSFR_4_2_4_1, WL15311_TSFR_4_2_5_1
TEST_DUMP_AND_LOAD([ schema_name ], {})
EXPECT_EQ(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "partitions": {} })
EXPECT_EQ(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "partitions": { subpartitions_table_name_quoted: [] } })
EXPECT_EQ(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

TEST_DUMP_AND_LOAD([ schema_name ], { "partitions": { partitions_table_name_quoted: [ "x1" ], subpartitions_table_name_quoted: [] } })
EXPECT_GT(count_rows(schema_name, partitions_table_name), count_rows(verification_schema, partitions_table_name))
EXPECT_EQ(count_rows(schema_name, subpartitions_table_name), count_rows(verification_schema, subpartitions_table_name))

#@<> WL15311 - cleanup
session.run_sql("DROP SCHEMA !;", [schema_name])
all_schemas.pop()

#@<> BUG#34952027 - ocimds option detects schema-level grants with wildcards
wild_account = "'test_34952027'@'localhost'"

def account_for_grant():
    return get_user_account_for_output(wild_account)

session.run_sql(f"CREATE USER {wild_account} IDENTIFIED BY 'pwd'")
# regular schema-level grant
schema_level_grant = f"GRANT SELECT ON `miscellaneous`.* TO {account_for_grant()}"
session.run_sql(schema_level_grant)
# schema-level grant with _ wildcard
schema_level_grant_with_underscore = f"GRANT SELECT ON `sample_schema`.* TO {account_for_grant()}"
session.run_sql(schema_level_grant_with_underscore)
# schema-level grant with % wildcard
schema_level_grant_with_percent = f"GRANT SELECT ON `all%`.* TO {account_for_grant()}"
session.run_sql(schema_level_grant_with_percent)
# schema-level grant with escaped _ wildcard
schema_level_grant_with_escaped_underscore = f"GRANT SELECT ON `sample\\_schema`.* TO {account_for_grant()}"
session.run_sql(schema_level_grant_with_escaped_underscore)
# schema-level grant with escaped % wildcard
schema_level_grant_with_escaped_percent = f"GRANT SELECT ON `all\\%`.* TO {account_for_grant()}"
session.run_sql(schema_level_grant_with_escaped_percent)

#@<> BUG#34952027 - dumping with ocimds fails
EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "ocimds": True, "users": True, "includeUsers": [ wild_account ], "includeSchemas": [ "invalid" ], "dryRun": True, "showProgress": False })

EXPECT_STDOUT_CONTAINS("""
ERROR: One or more accounts with database level grants containing wildcard characters were found.

      Loading these grants into a DB System instance may lead to unexpected results, as the partial_revokes system variable is enabled, which in turn changes the interpretation of wildcards in GRANT statements.
      To continue with the dump you must do one of the following:

      * Use the "excludeUsers" dump option to exclude problematic accounts.

      * Set the "users" dump option to false in order to disable user dumping.

      * Add the "ignore_wildcard_grants" to the "compatibility" option to ignore these issues.

      For more information on the interaction between wildcard database level grants and partial_revokes system variable please refer to: https://dev.mysql.com/doc/refman/en/grant.html
""")

EXPECT_STDOUT_NOT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant).error())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_underscore).error())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_percent).error())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_escaped_underscore).error())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_escaped_percent).error())

#@<> BUG#34952027 - dumping with ocimds and partial_revokes=ON succeeds {VER(>=8.0.16)}
session.run_sql("SET @@GLOBAL.partial_revokes = ON")
EXPECT_SUCCESS([ "invalid" ], test_output_relative, { "ocimds": True, "users": True, "includeUsers": [ wild_account ], "dryRun": True, "showProgress": False })
EXPECT_STDOUT_NOT_CONTAINS("wildcard")
session.run_sql("SET @@GLOBAL.partial_revokes = OFF")

#@<> BUG#34952027 - dumping with ocimds and ignore_wildcard_grants succeeds
EXPECT_SUCCESS([ "invalid" ], test_output_relative, { "ocimds": True, "compatibility": [ "ignore_wildcard_grants" ],"users": True, "includeUsers": [ wild_account ], "dryRun": True, "showProgress": False })
EXPECT_STDOUT_NOT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant).fixed())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_underscore).fixed())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_percent).fixed())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_escaped_underscore).fixed())
EXPECT_STDOUT_CONTAINS(ignore_wildcard_grants(wild_account, schema_level_grant_with_escaped_percent).fixed())

#@<> BUG#34952027 - cleanup
session.run_sql(f"DROP USER IF EXISTS {wild_account}")

#@<> Drop roles {VER(>=8.0.0)}
session.run_sql("DROP ROLE IF EXISTS ?;", [ test_role ])

#@<> BUG#35550282 - exclude `mysql_audit` schema if the `ocimds` option is set
# setup
schema_name = "mysql_audit"

session.run_sql("DROP SCHEMA IF EXISTS !", [schema_name])
session.run_sql("CREATE SCHEMA !", [schema_name])

#@<> BUG#35550282 - option is not set, schema is dumped
EXPECT_SUCCESS(None, test_output_absolute, { "ddlOnly": True, "showProgress": False })
EXPECT_TRUE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(schema_name) + ".sql")))

#@<> BUG#35550282 - option is set, schema is not dumped
EXPECT_SUCCESS(None, test_output_absolute, { "ocimds": True, "compatibility": ["ignore_missing_pks"], "users": False, "ddlOnly": True, "showProgress": False })
EXPECT_FALSE(os.path.isfile(os.path.join(test_output_absolute, encode_schema_basename(schema_name) + ".sql")))

#@<> BUG#35550282 - cleanup
session.run_sql("DROP SCHEMA !;", [schema_name])

#@<> WL15887 - setup
schema_name = "wl15887"
account_name = get_test_user_account("sample_account")
role_name = get_test_user_account("sample_role")

account_names = [ account_name ]

if __version_num >= 80000:
    account_names.append(role_name)

def setup_db(account):
    session.run_sql("DROP SCHEMA IF EXISTS !", [schema_name])
    session.run_sql("CREATE SCHEMA !", [schema_name])
    session.run_sql("CREATE TABLE !.! (`id` MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB;", [ schema_name, test_table_primary ])
    session.run_sql(f"CREATE DEFINER={account} EVENT !.! ON SCHEDULE EVERY 1 HOUR DO BEGIN END;", [ schema_name, test_schema_event ])
    session.run_sql(f"CREATE DEFINER={account} FUNCTION !.!(s CHAR(20)) RETURNS CHAR(50) DETERMINISTIC RETURN CONCAT('Hello, ',s,'!');", [ schema_name, test_schema_function ])
    session.run_sql(f"CREATE DEFINER={account} PROCEDURE !.!() SQL SECURITY DEFINER BEGIN END", [ schema_name, test_schema_procedure ])
    session.run_sql(f"CREATE DEFINER={account} TRIGGER !.! BEFORE UPDATE ON ! FOR EACH ROW BEGIN END;", [ schema_name, test_table_trigger, test_table_primary ])
    session.run_sql(f"CREATE DEFINER={account} SQL SECURITY INVOKER VIEW !.! AS SELECT * FROM !.!;", [ schema_name, test_view, schema_name, test_table_primary ])

create_all_schemas()
setup_db(test_user_account)
create_users()
session.run_sql(f"CREATE USER {account_name} IDENTIFIED BY 'pass'")

if __version_num >= 80000:
    session.run_sql(f"CREATE ROLE {role_name}")

#@<> WL15887-TSFR_1_1
help_text = """
      - targetVersion: string (default: current version of Shell) - Specifies
        version of the destination MySQL server.
"""
EXPECT_TRUE(help_text in util.help("dump_schemas"))

#@<> WL15887-TSFR_1_1_2 - option type
TEST_STRING_OPTION("targetVersion")

#@<> WL15887-TSFR_1_1_1 - invalid values
EXPECT_FAIL("ValueError", "Argument #2: Invalid value of the 'targetVersion' option: '8.1.', Error parsing version", test_output_absolute, { "targetVersion": "8.1.", "includeSchemas": [ schema_name ], "users": False, "showProgress": False })
EXPECT_FAIL("ValueError", "Argument #2: Invalid value of the 'targetVersion' option: 'abc', Error parsing version", test_output_absolute, { "targetVersion": "abc", "includeSchemas": [ schema_name ], "users": False, "showProgress": False })
EXPECT_FAIL("ValueError", "Argument #2: Invalid value of the 'targetVersion' option: empty", test_output_absolute, { "targetVersion": "", "includeSchemas": [ schema_name ], "users": False, "showProgress": False })

#@<> WL15887-TSFR_1_2_1 - wrong values - greater
for i in range(3):
    version = __mysh_version_no_extra.split(".")
    version[i] = str(int(version[i]) + 1)
    version = ".".join(version)
    EXPECT_FAIL("ValueError", f"Argument #2: Requested MySQL version '{version}' is newer than the maximum version '{__mysh_version_no_extra}' supported by this version of MySQL Shell", test_output_absolute, { "targetVersion": version, "includeSchemas": [ schema_name ], "users": False, "showProgress": False })

#@<> WL15887-TSFR_1_3_1 - wrong values - lower
EXPECT_FAIL("ValueError", "Argument #2: Requested MySQL version '8.0.24' is older than the minimum version '8.0.25' supported by this version of MySQL Shell", test_output_absolute, { "targetVersion": "8.0.24", "includeSchemas": [ schema_name ], "users": False, "showProgress": False })
EXPECT_FAIL("ValueError", "Argument #2: Requested MySQL version '7.9.26' is older than the minimum version '8.0.25' supported by this version of MySQL Shell", test_output_absolute, { "targetVersion": "7.9.26", "includeSchemas": [ schema_name ], "users": False, "showProgress": False })

#@<> WL15887 - valid values
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "targetVersion": "8.0.25", "dryRun": True, "users": False, "showProgress": False })
EXPECT_SUCCESS([ schema_name ], test_output_absolute, { "targetVersion": __mysh_version_no_extra, "dryRun": True, "users": False, "showProgress": False })

#@<> WL15887-TSFR_1_4_1 - implict value of targetVersion
EXPECT_SUCCESS([ schema_name ], test_output_relative, { "ocimds": True, "dryRun": True, "users": False, "showProgress": False })
EXPECT_STDOUT_CONTAINS(f"Checking for compatibility with MySQL HeatWave Service {__mysh_version_no_extra}")

# WL15887-TSFR_2_1 - implict value of targetVersion, warnings
EXPECT_STDOUT_CONTAINS(strip_definers_definer_clause(schema_name, test_schema_event, "Event", test_user_account).warning())
EXPECT_STDOUT_CONTAINS(strip_definers_definer_clause(schema_name, test_schema_function, "Function", test_user_account).warning())
EXPECT_STDOUT_CONTAINS(strip_definers_definer_clause(schema_name, test_schema_procedure, "Procedure", test_user_account).warning())
EXPECT_STDOUT_CONTAINS(strip_definers_definer_clause(schema_name, test_table_trigger, "Trigger", test_user_account).warning())
EXPECT_STDOUT_CONTAINS(strip_definers_definer_clause(schema_name, test_view, "View", test_user_account).warning())

EXPECT_STDOUT_CONTAINS(strip_definers_security_clause(schema_name, test_schema_function, "Function").warning())
EXPECT_STDOUT_CONTAINS(strip_definers_security_clause(schema_name, test_schema_procedure, "Procedure").warning())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_security_clause(schema_name, test_view, "View").warning())

EXPECT_STDOUT_CONTAINS(f"""
NOTE: One or more objects with the DEFINER clause were found.

      The 'targetVersion' option was not set and compatibility was checked with the MySQL HeatWave Service {__mysh_version_no_extra}.
      Loading the dump will fail if it is loaded into an DB System instance that does not support the SET_ANY_DEFINER privilege, which was introduced in 8.2.0.
""")

#@<> WL15887-TSFR_3_1_1 - restricted accounts
for account in ["mysql.infoschema", "mysql.session", "mysql.sys", "ociadmin", "ocidbm", "ocirpl"]:
    account = f"`{account}`@`localhost`"
    setup_db(account)
    WIPE_OUTPUT()
    EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "targetVersion": __mysh_version_no_extra, "ocimds": True, "dryRun": True, "includeSchemas": [ schema_name ], "users": False, "showProgress": False })
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_restricted_user_name(schema_name, test_schema_event, "Event", account).error())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_restricted_user_name(schema_name, test_schema_function, "Function", account).error())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_restricted_user_name(schema_name, test_schema_procedure, "Procedure", account).error())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_restricted_user_name(schema_name, test_table_trigger, "Trigger", account).error())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_restricted_user_name(schema_name, test_view, "View", account).error())

# restore schema
setup_db(test_user_account)

#@<> WL15887-TSFR_3_2_1 - valid account
EXPECT_SUCCESS([ schema_name ], test_output_relative, { "targetVersion": __mysh_version_no_extra, "ocimds": True, "dryRun": True, "users": False, "showProgress": False })

# no warnings about DEFINER=
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_definer_clause(schema_name, test_schema_event, "Event", test_user_account).warning())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_definer_clause(schema_name, test_schema_function, "Function", test_user_account).warning())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_definer_clause(schema_name, test_schema_procedure, "Procedure", test_user_account).warning())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_definer_clause(schema_name, test_table_trigger, "Trigger", test_user_account).warning())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_definer_clause(schema_name, test_view, "View", test_user_account).warning())

# WL15887-TSFR_3_5_1 - no warnings about SQL SECURITY
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_security_clause(schema_name, test_schema_function, "Function").warning())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_security_clause(schema_name, test_schema_procedure, "Procedure").warning())
EXPECT_STDOUT_NOT_CONTAINS(strip_definers_security_clause(schema_name, test_view, "View").warning())

# WL15887-TSFR_3_3_1 - no account is not included in the dump
EXPECT_STDOUT_CONTAINS(definer_clause_uses_unknown_account_once().warning())

#@<> WL15887-TSFR_3_3_1 - user does not exist/is excluded
for account in [ account_name, "`invalid-account`@`localhost`" ]:
    setup_db(account)
    WIPE_OUTPUT()
    EXPECT_FAIL("Error: Shell Error (52004)", "While 'Validating MySQL HeatWave Service compatibility': Compatibility issues were found", test_output_relative, { "includeUsers": [ test_user_account ], "targetVersion": __mysh_version_no_extra, "ocimds": True, "dryRun": True, "includeSchemas": [ schema_name ], "users": True, "showProgress": False })
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_unknown_account(schema_name, test_schema_event, "Event", account).warning())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_unknown_account(schema_name, test_schema_function, "Function", account).warning())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_unknown_account(schema_name, test_schema_procedure, "Procedure", account).warning())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_unknown_account(schema_name, test_table_trigger, "Trigger", account).warning())
    EXPECT_STDOUT_CONTAINS(definer_clause_uses_unknown_account(schema_name, test_view, "View", account).warning())

# restore schema
setup_db(test_user_account)

#@<> WL15887-TSFR_4_1 - note about strip_definers
EXPECT_SUCCESS([ schema_name ], test_output_relative, { "compatibility": [ "strip_definers" ], "targetVersion": __mysh_version_no_extra, "ocimds": True, "dryRun": True, "users": False, "showProgress": False })
EXPECT_STDOUT_CONTAINS(f"NOTE: The 'targetVersion' option is set to {__mysh_version_no_extra}. This version supports the SET_ANY_DEFINER privilege, using the 'strip_definers' compatibility option is unnecessary.")

#@<> WL15887-TSFR_5_1 - user/role with SET_ANY_DEFINER {VER(>=8.2.0)}
for account in account_names:
    session.run_sql(f"GRANT SET_ANY_DEFINER ON *.* TO {account}")
    WIPE_OUTPUT()
    EXPECT_SUCCESS([ schema_name ], test_output_relative, { "compatibility": [ "strip_restricted_grants" ], "includeUsers": [ account ], "targetVersion": __mysh_version_no_extra, "ocimds": True, "dryRun": True, "users": True, "showProgress": False })
    EXPECT_STDOUT_NOT_CONTAINS("SET_ANY_DEFINER")
    session.run_sql(f"REVOKE SET_ANY_DEFINER ON *.* FROM {account}")

#@<> WL15887-TSFR_6_1 - user/role with SET_USER_ID {VER(>=8.0.0)}
for account in account_names:
    session.run_sql(f"GRANT SET_USER_ID ON *.* TO {account}")
    WIPE_OUTPUT()
    EXPECT_SUCCESS([ schema_name ], test_output_relative, { "compatibility": [ "strip_restricted_grants" ], "includeUsers": [ account ], "targetVersion": __mysh_version_no_extra, "ocimds": True, "dryRun": True, "users": True, "showProgress": False })
    EXPECT_STDOUT_CONTAINS(strip_restricted_grants_set_user_id_replaced(account).fixed())
    session.run_sql(f"REVOKE SET_USER_ID ON *.* FROM {account}")

#@<> WL15887 - cleanup
session.run_sql("DROP SCHEMA IF EXISTS !;", [schema_name])
session.run_sql(f"DROP USER {account_name}")

if __version_num >= 80000:
    session.run_sql(f"DROP ROLE {role_name}")

#@<> BUG#35680824 - warnings on grants for system schemas should not be printed
# setup
test_account = "'test_35680824'@'localhost'"

def account_for_grant():
    return get_user_account_for_output(test_account)

session.run_sql(f"CREATE USER {test_account} IDENTIFIED BY 'pwd'")
# it's not possible to grant a privilege on information_schema
session.run_sql(f"GRANT SELECT ON `mysql`.* TO {account_for_grant()}")
session.run_sql(f"GRANT SELECT ON `performance_schema`.`global_variables` TO {account_for_grant()}")
session.run_sql(f"GRANT EXECUTE ON FUNCTION `sys`.`version_major` TO {account_for_grant()}")

#@<> BUG#35680824 - test
EXPECT_SUCCESS(None, test_output_relative, { "ocimds": True, "users": True, "includeUsers": [ test_account ], "includeSchemas": [ "invalid" ], "dryRun": True, "showProgress": False })
EXPECT_STDOUT_NOT_CONTAINS(account_for_grant())

#@<> BUG#35680824 - cleanup
session.run_sql(f"DROP USER IF EXISTS {test_account}")

#@<> Cleanup
drop_all_schemas()
session.run_sql("SET GLOBAL local_infile = false;")
session.close()
testutil.destroy_sandbox(__mysql_sandbox_port1)
shutil.rmtree(incompatible_table_directory, True)
