#
# Copyright (c) 2016 Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
"""
Unit tests for mysql_gadgets.common.tools module.
"""
import os
import stat
import subprocess
import sys
import time
import unittest

from mysql_gadgets.common import server

from mysql_gadgets.common import tools
from mysql_gadgets.exceptions import GadgetError
from unit_tests.utils import GadgetsTestCase, SERVER_CNX_OPT

if sys.version_info > (3, 0):
    # Python 3
    import configparser  # pylint: disable=E0401,C0411
else:
    # Python 2
    import ConfigParser as configparser  # pylint: disable=E0401,C0411


class TestTools(GadgetsTestCase):
    """Class to test mysql_gadgets.common.tools module.
    """

    @property
    def num_servers_required(self):
        """Property defining the number of servers required by the test.
        """
        return 1

    def setUp(self):
        """ Setup base server connection (for all tests).
        """
        self.server_cnx = {'conn_info': self.options[SERVER_CNX_OPT][0]}
        self.server = server.Server(self.server_cnx)
        self.server.connect()

    def tearDown(self):
        """ Disconnect base server (for all tests).
        """
        self.server.disconnect()

    def test_get_tool_path(self):
        """ Test get_tool_path function.
        """
        # Get server basedir.
        basedir = self.server.exec_query(
            "SHOW VARIABLES LIKE '%basedir%'")[0][1]

        # Find 'mysqld' using default option.
        res = tools.get_tool_path(basedir, 'mysqld')
        self.assertIn("mysqld", res,
                      "The 'mysqld' file is expected to be found in basedir.")

        # Find 'mysqld' and return result with quotes.
        res = tools.get_tool_path(basedir, 'mysqld', quote=True)
        self.assertIn("mysqld", res,
                      "The 'mysqld' file is expected to be found in basedir.")
        quote_char = "'" if os.name == "posix" else '"'
        self.assertEqual(res[0], quote_char,
                         "Result expected to be quoted with "
                         "({0}).".format(quote_char))

        # Find 'mysqld' using the default path list.
        bindir = os.path.join(basedir, 'bin')
        res = tools.get_tool_path('.', 'mysqld', defaults_paths=[bindir])
        self.assertIn("mysqld", res,
                      "The 'mysqld' file is expected to be found in"
                      "defaults_paths.")

        # Find 'mysqld' using the PATH variable.
        path_var = os.environ['PATH']
        os.environ['PATH'] = bindir
        try:
            res = tools.get_tool_path('.', 'mysqld', search_path=True)
        finally:
            # Make sure the PATH variable is restored.
            os.environ['PATH'] = path_var
        self.assertIn("mysqld", res,
                      "The 'mysqld' file is expected to be found in PATH.")

        # Try to find a non existing tool (error raised by default).
        with self.assertRaises(GadgetError):
            tools.get_tool_path(basedir, 'non_existing_tool')

        # Try to find a non existing tool with required set to False.
        res = tools.get_tool_path(basedir, 'non_existing_tool', required=False)
        self.assertIsNone(res, "None expected when trying to find"
                               "'non_existing_tool'")

    def test_get_abs_path(self):
        """Test get_abs_path function"""

        # passing a valid abs_path should return the same path
        abs_path = __file__
        self.assertTrue(os.path.isabs(abs_path))
        self.assertEqual(tools.get_abs_path(abs_path), abs_path)

        # passing an invalid absolute path as relative_to should return an
        # error
        bad_abs_path = "../not_a_valid_abs_path"
        self.assertFalse(os.path.isabs(bad_abs_path))
        with self.assertRaises(GadgetError):
            tools.get_abs_path("../..", bad_abs_path)

        # passing it a relative path should return it joined together with
        # the relative_to path be it a file or a dir
        dirname = os.path.dirname(__file__)
        expected = os.path.normpath(os.path.join(dirname, '../..'))
        res = tools.get_abs_path("../..", dirname)
        self.assertEqual(res, expected)
        res = tools.get_abs_path("../..", __file__)
        self.assertEqual(res, expected)

    def test_create_option_file(self):
        """test the create_option_file function"""
        # using an invalid prefix dir must raise an error
        with self.assertRaises(GadgetError):
            tools.create_option_file({}, prefix_dir="NOT_A_VALID_PREFIX_DIR")

        # Check that config file by default is created in the home folder.
        f_path = tools.create_option_file({})
        try:
            f_dir, _ = os.path.split(f_path)
            home_path = os.path.normpath(os.path.expanduser("~"))
            self.assertEqual(home_path, f_dir)
            self.assertTrue(os.path.isfile(f_path))
            mode = os.stat(f_path).st_mode
            # Check that owner can read it.
            self.assertTrue(mode & stat.S_IRUSR)
            # Check that owner can write to it.
            self.assertTrue(mode & stat.S_IWUSR)
            # Check that owner cannot execute it.
            if not sys.platform.startswith("win"):
                # On windows mkstemp (used by create_option_file) creates
                # a file with 666 permission bits instead of 600 as expected.
                self.assertFalse(mode & stat.S_IXUSR)
                # Check that group users cannot read it.
                self.assertFalse(mode & stat.S_IRGRP)
                # Check that group users cannot write to it.
                self.assertFalse(mode & stat.S_IWGRP)
                # Check that it is not executable for group users.
                self.assertFalse(mode & stat.S_IXGRP)
                # Check that other users cannot read it.
                self.assertFalse(mode & stat.S_IROTH)
                # Check that other users cannot write to it.
                self.assertFalse(mode & stat.S_IWOTH)
                # Check that it is not executable for other users.
                self.assertFalse(mode & stat.S_IXOTH)
        finally:
            os.remove(f_path)
        # Check that config file is created on a provided dir with the
        # correct permissions.
        test_dir, _ = os.path.split(__file__)
        f_path = tools.create_option_file({}, prefix_dir=test_dir)
        try:
            f_dir, _ = os.path.split(f_path)
            self.assertEqual(test_dir, f_dir)
            self.assertTrue(os.path.isfile(f_path))
            mode = os.stat(f_path).st_mode
            # Check that owner can read it.
            self.assertTrue(mode & stat.S_IRUSR)
            # Check that owner can write to it.
            self.assertTrue(mode & stat.S_IWUSR)
            # Check that owner cannot execute it.
            self.assertFalse(mode & stat.S_IXUSR)
            if not sys.platform.startswith("win"):
                # On windows mkstemp (used by create_option_file) creates
                # a file with 666 permission bits instead of 600 as expected.
                # Check that group users cannot read it.
                self.assertFalse(mode & stat.S_IRGRP)
                # Check that group users cannot write to it.
                self.assertFalse(mode & stat.S_IWGRP)
                # Check that it is not executable for group users.
                self.assertFalse(mode & stat.S_IXGRP)
                # Check that other users cannot read it.
                self.assertFalse(mode & stat.S_IROTH)
                # Check that other users cannot write to it.
                self.assertFalse(mode & stat.S_IWOTH)
                # Check that it is not executable for other users.
                self.assertFalse(mode & stat.S_IXOTH)
        finally:
            os.remove(f_path)

        # Check that config file is created on a provided dir with a provided
        # name and correct permissions.
        test_dir, _ = os.path.split(__file__)
        f_path = tools.create_option_file({}, name="opt_file_test",
                                          prefix_dir=test_dir)
        try:
            f_dir, f_name = os.path.split(f_path)
            self.assertEqual(test_dir, f_dir)
            self.assertEqual("opt_file_test", f_name)
            self.assertTrue(os.path.isfile(f_path))
            mode = os.stat(f_path).st_mode
            # Check that owner can read it.
            self.assertTrue(mode & stat.S_IRUSR)
            # Check that owner can write to it.
            self.assertTrue(mode & stat.S_IWUSR)
            # Check that owner cannot execute it.
            self.assertFalse(mode & stat.S_IXUSR)
            # trying to create a file in the same directory with the same name
            # should return an error
            with self.assertRaises(GadgetError):
                tools.create_option_file({}, name="opt_file_test",
                                         prefix_dir=test_dir)

            if not sys.platform.startswith("win"):
                # On windows mkstemp (used by create_option_file) creates
                # a file with 666 permission bits instead of 600 as expected.
                # Check that group users cannot read it.
                self.assertFalse(mode & stat.S_IRGRP)
                # Check that group users cannot write to it.
                self.assertFalse(mode & stat.S_IWGRP)
                # Check that it is not executable for group users.
                self.assertFalse(mode & stat.S_IXGRP)
                # Check that other users cannot read it.
                self.assertFalse(mode & stat.S_IROTH)
                # Check that other users cannot write to it.
                self.assertFalse(mode & stat.S_IWOTH)
                # Check that it is not executable for other users.
                self.assertFalse(mode & stat.S_IXOTH)
        finally:
            os.remove(f_path)

        # Check that its contents are correct
        conf_dict = ({"section1": {"option1": "val1", "option12": None},
                      "section2": {"option2": None, "option21": "val21"}})
        f_path = tools.create_option_file(conf_dict, prefix_dir=test_dir)
        try:
            c = configparser.RawConfigParser(allow_no_value=True)
            c.read(f_path)
            # Check they have the same sections
            self.assertEqual(set(conf_dict.keys()), set(c.sections()))
            # Check that they have the same options
            for section in conf_dict:
                self.assertEqual(set(conf_dict[section].keys()),
                                 set(c.options(section)))
            # Check they have the same values
            for section in conf_dict:
                for option in conf_dict[section].keys():
                    self.assertEqual(conf_dict[section][option],
                                     c.get(section, option))

        finally:
            os.remove(f_path)

    def test_get_subclass_dict(self):
        """test get_subclass_dict function"""

        # create some classes to test the method
        class A(object):
            """Class A"""
            pass

        class B(A):
            """Class B"""
            pass

        class C(A):
            """Class C"""
            pass

        class D(B):
            """Class D"""
            pass

        class E(B, C):
            """Class E"""
            pass

        sub_dict = tools.get_subclass_dict(A)
        # Check that the keys are the name of the subclasses
        self.assertEqual(set(['B', 'C', 'D', 'E']), set(sub_dict.keys()))
        # Check that the values are the subclasses themselves
        self.assertTrue(type(sub_dict['B']) is type(B))
        self.assertTrue(type(sub_dict['C']) is type(C))
        self.assertTrue(type(sub_dict['D']) is type(D))
        self.assertTrue(type(sub_dict['E']) is type(E))

    def test_is_listening(self):
        """test is_listening function"""
        # the port on which the server is running should be listening
        self.assertTrue(tools.is_listening("localhost", self.server.port))

        # but a free port should not be listening
        self.assertFalse(tools.is_listening("not_a_valid_host", 1234))

    def test_is_executable(self):
        """Test is_executable function"""
        # python is an executable file
        try:
            python_path = tools.get_tool_path(None, "python", required=True,
                                              search_path=True)
        except GadgetError:
            raise unittest.SkipTest("Couldn't find python executable.")
        self.assertTrue(tools.is_executable(python_path))

        # a simple file is not executable, list this test file is not
        # executable
        if os.name == "posix":
            # on windows the test file is deemed as executable
            self.assertFalse(tools.is_executable(__file__))
        # A file that does not exist is also not executable
        self.assertFalse(tools.is_executable(__file__ + "aa"))

    def test_run_subprocess(self):
        """Test run_subprocess function"""
        # Run a simple echo command
        try:
            echo_path = tools.get_tool_path(None, "echo", required=True,
                                            search_path=True)
        except GadgetError:
            raise unittest.SkipTest("Couldn't find echo executable.")
        p = tools.run_subprocess("{0} output".format(echo_path),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        out, err = p.communicate()
        ret_code = p.returncode
        # process ran ok
        self.assertEqual(ret_code, 0)
        self.assertEqual(out, "output\n")
        self.assertEqual("", err)

    def test_stop_process_with_pid(self):
        """Test stop_process_with_pid function"""

        # launch a process that sleeps for a minute and try to kill it
        if os.name == "nt":
            cmd = "ping 127.0.0.1 -n 60 > NUL"
        else:
            cmd = "sleep 60"

        # test terminate
        proc = tools.run_subprocess(cmd, shell=True)
        pid = proc.pid
        tools.stop_process_with_pid(pid, force=False)
        # sleep a little just to give time for the proc to end
        time.sleep(3)
        # make sure process terminated with sigterm
        self.assertTrue(bool(proc.poll()))
        if os.name == "nt":
            # on windows if process was interrupted it should have exited with
            # the value of the signal received
            self.assertEqual(proc.returncode, 15)
        else:
            # on unix it exits with negative value of the signal received
            self.assertEqual(proc.returncode, -15)

        # test kill
        proc = tools.run_subprocess(cmd, shell=True)
        pid = proc.pid
        tools.stop_process_with_pid(pid, force=True)
        # sleep a little just to give time for the proc to end
        time.sleep(3)
        # make sure process terminated
        self.assertTrue(bool(proc.poll()))
        if os.name == "nt":
            # on windows if process was interrupted it should have exited with
            # return code 1
            self.assertEqual(proc.returncode, 1)
        else:
            # on unix it exits with negative value of the signal received
            self.assertEqual(proc.returncode, -9)

        # Trying to terminate or kill a non existing pid should return error
        with self.assertRaises(GadgetError):
            tools.stop_process_with_pid(-23, force=False)

        with self.assertRaises(GadgetError):
            tools.stop_process_with_pid(-23, force=True)
