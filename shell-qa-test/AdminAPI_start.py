import subprocess
import time
import sys
import datetime
import platform
import os
import threading
import functools
import unittest
import json
import xmlrunner
import shutil
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('AdminAPI_Log_Execution.txt', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

############   Retrieve variables from configuration file    ##########################
class LOCALHOST:
    user =""
    password = ""
    host = ""
    xprotocol_port = ""
    port =""
class REMOTEHOST:
    user = ""
    password =""
    host = ""
    xprotocol_port = ""
    port = ""

if 'CONFIG_PATH' in os.environ and 'MYSQLX_PATH' in os.environ and os.path.isfile(os.environ['CONFIG_PATH']) and os.path.isfile(os.environ['MYSQLX_PATH']):
    # **** JENKINS EXECUTION ****
    config_path = os.environ['CONFIG_PATH']
    config=json.load(open(config_path))
    MYSQL_SHELL = os.environ['MYSQLX_PATH']
    Exec_files_location = os.environ['AUX_FILES_PATH']
    cluster_Path = os.environ['CLUSTER_PATH']
    XSHELL_QA_TEST_ROOT = os.environ['XSHELL_QA_TEST_ROOT']
    XMLReportFilePath = XSHELL_QA_TEST_ROOT+"/adminapi_qa_test.xml"
    testFilesPath = os.environ['testFilesPath']
else:
    # **** LOCAL EXECUTION ****
    config = json.load(open('config_local.json'))
    MYSQL_SHELL = str(config["general"]["xshell_path"])
    Exec_files_location = str(config["general"]["aux_files_path"])
    cluster_Path = str(config["general"]["cluster_path"])
    XMLReportFilePath = "adminapi_qa_test.xml"
    testFilesPath = "./adminapi_testfiles"

#########################################################################

LOCALHOST.user = str(config["local"]["user"])
LOCALHOST.password = str(config["local"]["password"])
LOCALHOST.host = str(config["local"]["host"])
LOCALHOST.xprotocol_port = str(config["local"]["xprotocol_port"])
LOCALHOST.port = str(config["local"]["port"])

REMOTEHOST.user = str(config["remote"]["user"])
REMOTEHOST.password = str(config["remote"]["password"])
REMOTEHOST.host = str(config["remote"]["host"])
REMOTEHOST.xprotocol_port = str(config["remote"]["xprotocol_port"])
REMOTEHOST.port = str(config["remote"]["port"])



class globalvar:
    last_found=""
    last_search=""

  # ----------------------------------------------------------------------

logger.debug("------------ AdminAPI Test Start... ---------- ")
if __name__ == '__main__':
  suite = unittest.TestSuite()
  suite.addTest(unittest.TestLoader().discover(testFilesPath, pattern="test_MYS_setup.py"))
  sortedtestfileNames = sorted(os.listdir(testFilesPath))
  for Testfilename in sortedtestfileNames:
      if os.path.splitext(Testfilename)[1] == ".py":
          suite.addTests(unittest.TestLoader().discover(testFilesPath, pattern=Testfilename))
  logger.debug("------------ Number of Test Cases To Be Executed: " + str(suite.countTestCases()) + " ---------- ")
  testRunner = xmlrunner.XMLTestRunner(file(XMLReportFilePath, "w"))
  testRunner.verbosity=3
  testRunner.run(suite)
