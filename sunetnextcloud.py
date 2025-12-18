"""Sunet Drive Support Module for unit and general testing
Author: Richard Freitag <freitag@sunet.se>
TestTarget is a helper class containing node-information, as well as for saving and retrieving node-local usernames/passwords.
expected.yaml contains expected results when retrieving status.php from a Sunet Drive node
"""

import logging
import os
import random
import string
import sys
import time
import unittest
from datetime import datetime
from enum import Enum

import HtmlTestRunner
import pyotp
import requests
import xmlrunner
import yaml
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import EdgeOptions, FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

g_requestTimeout = 30

# Change to local directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

target_env = os.environ.get("NextcloudTestTarget")
if target_env == "localhost":
    g_expectedFile = "expected_localhost.yaml"
elif target_env == "custom":
    g_expectedFile = "expected_custom.yaml"
else:
    g_expectedFile = "expected.yaml"

use_driver_service = False
if os.environ.get("SELENIUM_DRIVER_SERVICE") == "True":
    use_driver_service = True
geckodriver_path = "/snap/bin/geckodriver"

opsbase = "sunet-drive-ops/"
opsCommonFile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
# opsCosmosDbFile = opsbase + "/global/overlay/etc/puppet/cosmos-db.yaml"

ocsheaders = {"OCS-APIRequest": "true"}


def get_value(env, raiseException=True):
    value = os.environ.get(env)
    if value == "":
        logger.warning(f"{env} is empty!")
    if value is None:
        msg = f"Environment variable {env} is not set!"
        if raiseException:
            raise Exception(msg)
        else:
            logger.error(msg)
            pass
    return value


class TestTarget(object):
    with open(g_expectedFile, "r") as stream:
        expectedResults = yaml.safe_load(stream)

    if os.path.exists(opsCommonFile):
        with open(opsCommonFile, "r") as stream:
            opsCommonConfig = yaml.safe_load(stream)
    else:
        logger.warning(
            f"File {opsCommonFile} not found, you should check out the ops repo to test against expected values!"
        )

    baseurl = expectedResults["global"]["baseUrl"]
    testprefix = expectedResults["global"]["testPrefix"]
    nodeprefix = expectedResults["global"]["nodePrefix"]
    docprefix = expectedResults["global"]["docPrefix"]
    indexsuffix = expectedResults["global"]["indexSuffix"]
    ocsheaders = ocsheaders

    # default target is test, unless overwritten by initializing with 'prod'
    targetprefix = "." + testprefix

    nodestotest = None
    allnodes = expectedResults["global"]["allnodes"]
    fullnodes = expectedResults["global"]["fullnodes"]
    multinodes = expectedResults["global"]["multinodes"]
    aliasnodes = expectedResults["global"]["aliasnodes"]
    browsers = expectedResults["global"]["testBrowsers"]

    allnodes.sort()
    fullnodes.sort()
    multinodes.sort()

    target = "test"
    platform = sys.platform

    ocsheaders = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "OCS-APIRequest": "true",
    }

    def __init__(self, target=None, loglevel=logging.INFO):
        global target_env
        logging.getLogger().setLevel(loglevel)
        logger.info(f"Using test results file: {g_expectedFile}")
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        logger.info(f"Working directory is {dname}")
        customers_env = os.environ.get("NextcloudTestCustomers")
        if customers_env is not None:
            customers_env = customers_env.split(",")
            self.nodestotest = customers_env
        else:
            customers_env = ["all"]
        testbrowsers = os.environ.get("NextcloudTestBrowsers")
        testrunner = os.environ.get("NextcloudTestRunner")
        testfilesize = os.environ.get("NextcloudTestFileSize")
        testgridaddress = os.environ.get("NextcloudTestGridAddress")

        if testgridaddress is None:
            logger.info("Using default grid address http://127.0.0.1:4444/wd/hub")
            self.testgridaddress = "http://127.0.0.1:4444/wd/hub"

        if testfilesize is None:
            logger.info("Using default file size M")
            self.testfilesize = "M"
        elif (testfilesize == "M") or (testfilesize == "G"):
            logger.info(f"Using {testfilesize}B file size")
            self.testfilesize = testfilesize
        else:
            logger.warning(f"Unknown file size {testfilesize}B, using MB as default")
            self.testrunner = "M"

        if testrunner is None:
            logger.info("Using default xml test runner")
            self.testrunner = "xml"
        elif (testrunner == "xml") or (testrunner == "html") or ("txt"):
            logger.info(f"Using {testrunner} test runner")
            self.testrunner = testrunner
        else:
            logger.warning(f"Unknown testrunner {testrunner}, using html as default")
            self.testrunner = "html"

        if target is not None:
            logger.info(f"Test target initialized by caller: {target}")
            testtarget = target
        elif target_env is not None:
            logger.info(
                f"Test target initialized by environment variable: {target_env}"
            )
            testtarget = target_env
        else:
            logger.warning("Test target initialized by default value: test")
            testtarget = "test"

        if testtarget not in ["prod", "test", "localhost", "custom"]:
            logger.error(f"Unsupported test target: {target}, exiting...")
            sys.exit()

        sys.stdout.flush()
        if testtarget == "prod":
            self.target = "prod"
            self.targetprefix = ""
        elif testtarget == "localhost":
            self.target = "localhost"
        elif testtarget == "custom":
            self.target = "custom"
        else:
            self.target = "test"
            self.targetprefix = "." + self.testprefix

        if len(customers_env) == 1 or self.target == "custom":
            if "all" not in customers_env[0]:
                self.nodestotest = customers_env

        if customers_env[0] == "all" or customers_env[0] == "allnodes":
            self.nodestotest = self.allnodes
            logger.info(f"Testing all {len(self.nodestotest)} nodes")

        if customers_env[0] == "fullnodes":
            self.nodestotest = self.fullnodes
            logger.info(f"Testing {len(self.nodestotest)} full nodes")

        if customers_env[0] == "multinodes":
            self.nodestotest = self.multinodes
            logger.info(f"Testing {len(self.nodestotest)} multi nodes")

        # If we have a custom list of nodes set in the environment variable
        if len(customers_env) != len(self.fullnodes) and "all" not in customers_env[0]:
            self.allnodes = customers_env
            self.fullnodes = self.allnodes

        # Override browsers to test from expected.yaml with value(s) in environment variable
        if testbrowsers is not None:
            self.browsers = testbrowsers.split(",")

        if testtarget == "localhost":
            self.targetprefix = ""
            self.nodeprefix = ""
            self.delimiter = ""
            self.verify = False  # Do not verify SSL when testing locally
        elif testtarget == "custom":
            self.delimiter = ""
            self.verify = True
        else:
            self.delimiter = "."  # URL delimiter
            self.verify = True

    def getnodeprefix(self, node):
        if (node == "none") or (node == "localhost"):
            prefix = self.nodeprefix
        elif len(self.nodeprefix) == 0:
            prefix = node
        else:
            prefix = node + "." + self.nodeprefix
        return prefix

    def is_multinode(self, node):
        try:
            self.opsCommonConfig["multinode_mapping"][node]["server"]
            return True
        except Exception:
            return False

    def get_multinode(self, node):
        return self.opsCommonConfig["multinode_mapping"][node]["server"]

    def get_multinode_port(self, node):
        return self.opsCommonConfig["multinode_mapping"][node]["port"]

    def get_node_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
        )

    def get_node_base_url(self, node):
        return (
            self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl
        )

    def get_base_url(self):
        return self.nodeprefix + self.targetprefix + self.delimiter + self.baseurl

    def get_node_login_url(self, node, direct=True):
        if direct:
            return (
                "https://"
                + self.getnodeprefix(node)
                + self.targetprefix
                + self.delimiter
                + self.baseurl
                + self.indexsuffix
                + "/login?direct=1"
            )
        else:
            return (
                "https://"
                + self.getnodeprefix(node)
                + self.targetprefix
                + self.delimiter
                + self.baseurl
                + self.indexsuffix
            )

    def get_login_url(self):
        return (
            "https://"
            + self.nodeprefix
            + self.targetprefix
            + self.delimiter
            + self.baseurl
        )

    def get_node_post_logout_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/login?clear=1"
        )

    def get_node_post_logout_simple_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/login"
        )

    def get_node_post_logout_saml_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/apps/user_saml/saml/selectUserBackEnd?redirectUrl="
        )

    def get_settings_user_security_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/settings/user/security"
        )

    def get_post_logout_url(self):
        if self.target == "test":
            return "https://service.seamlessaccess.org/ds/?entityID=https%3A%2F%2Fidp-proxy.drive.test.sunet.se%2Fsp&return=https%3A%2F%2Fdrive.test.sunet.se"
        elif self.target == "prod":
            return "https://service.seamlessaccess.org/ds/?entityID=https%3A%2F%2Fdrive-idp-proxy.sunet.se%2Fsp&return=https%3A%2F%2Fdrive.sunet.se"
        else:
            return "TBD"

    def get_ocs_capabilities_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/capabilities"
        )

    def get_openapi_url(self, node, path, basic_auth=True):
        if basic_auth:
            urlPrefix = "https://$USERNAME$:$PASSWORD$@"
        else:
            urlPrefix = ""

        return (
            urlPrefix
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + path
        )

    def get_all_apps_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/apps"
        )

    def get_app_url(self, node, app):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/apps/"
            + app
        )

    def get_users_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/users"
        )

    def get_user_url(self, node, user):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/users/"
            + user
        )

    def get_groups_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/groups"
        )

    def get_group_url(self, node, group):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/groups/"
            + group
        )

    def get_groups_details_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/groups/details"
        )

    def get_group_details_url(self, node, group):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/groups/"
            + group
        )

    def get_add_user_fe_url(self, node, id):
        return (
            "https://$USERNAME$:$PASSWORD$@node"
            + str(id)
            + "."
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/users"
        )

    def get_share_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_sharing/api/v1/shares"
        )

    def get_share_id_url(self, node, id):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_sharing/api/v1/shares/"
            + id
        )

    def get_add_user_multinode_url(self, node):
        server = self.opsCommonConfig["multinode_mapping"][node]["server"]
        port = self.opsCommonConfig["multinode_mapping"][node]["port"]
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + server
            + "."
            + self.nodeprefix
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + ":"
            + str(port)
            + "/ocs/v2.php/cloud/users"
        )

    def get_userinfo_url(self, node, userid):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/users/"
            + userid
        )

    def get_user_url(self, node, username):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/users/"
            + username
        )

    def get_disable_user_url(self, node, username):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/cloud/users/"
            + username
            + "/disable"
        )

    def get_dashboard_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/apps/dashboard/"
        )

    def get_folder_url(self, node, foldername):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/apps/files/?dir=/"
            + foldername
        )

    def get_webdav_url(self, node, username):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/remote.php/dav/files/"
            + username
            + "/"
        )

    def get_file_lock_url(self, node, filename):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_lock/lock/"
            + filename
        )

    def get_file_lock_curl(self, node, username, filename):
        return (
            "curl -X LOCK --url https://"
            + username
            + ":$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/remote.php/dav/files/"
            + username
            + "/"
            + filename
            + " --header 'X-User-Lock: 1'"
        )

    def get_file_unlock_curl(self, node, username, filename):
        return (
            "curl -X UNLOCK --url https://"
            + username
            + ":$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/remote.php/dav/files/"
            + username
            + "/"
            + filename
            + " --header 'X-User-Lock: 1'"
        )

    def get_shares_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_sharing/api/v1/shares"
        )

    def get_remote_shares_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares"
        )

    def get_pending_shares_url(self, node):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending"
        )

    def get_pending_shares_id_url(self, node, id):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending/"
            + str(id)
        )

    def get_delete_share_url(self, node, id):
        return (
            "https://$USERNAME$:$PASSWORD$@"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/files_sharing/api/v1/shares/"
            + id
        )

    def get_serverinfo_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/ocs/v2.php/apps/serverinfo/api/v1/info"
        )

    def get_metadata_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/apps/user_saml/saml/metadata?idp=1"
        )

    def get_node_entity_id(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + self.indexsuffix
            + "/apps/user_saml/saml/metadata"
        )

    def get_collabora_node_url(self, node):
        if len(self.nodeprefix) == 0:
            return (
                "https://"
                + self.docprefix
                + str(node)
                + self.targetprefix
                + self.delimiter
                + self.baseurl
            )
        return (
            "https://"
            + self.docprefix
            + str(node)
            + "."
            + self.getnodeprefix("none")
            + self.targetprefix
            + self.delimiter
            + self.baseurl
        )

    def get_collabora_capabilities_url(self, node):
        if len(self.nodeprefix) == 0:
            return (
                "https://"
                + self.docprefix
                + str(node)
                + self.targetprefix
                + self.delimiter
                + self.baseurl
                + "/hosting/capabilities"
            )
        return (
            "https://"
            + self.docprefix
            + str(node)
            + "."
            + self.getnodeprefix("none")
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/hosting/capabilities"
        )

    def get_fullnode_status_urls(self):
        nodeurls = []
        for node in self.fullnodes:
            nodeurls.append(
                "https://"
                + self.getnodeprefix(node)
                + self.targetprefix
                + self.delimiter
                + self.baseurl
                + "/status.php"
            )
        return nodeurls

    def get_multinode_status_urls(self):
        nodeurls = []
        for node in self.multinodes:
            nodeurls.append(
                "https://"
                + self.getnodeprefix(node)
                + self.targetprefix
                + self.delimiter
                + self.baseurl
                + "/status.php"
            )
        return nodeurls

    def get_allnode_status_urls(self):
        nodeurls = []
        for node in self.allnodes:
            nodeurls.append(
                "https://"
                + self.getnodeprefix(node)
                + self.targetprefix
                + self.delimiter
                + self.baseurl
                + "/status.php"
            )
        return nodeurls

    def get_status_url(self, node):
        return (
            "https://"
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/status.php"
        )

    def get_node_status_url(self, node, id):
        return (
            "https://node"
            + str(id)
            + "."
            + self.getnodeprefix(node)
            + self.targetprefix
            + self.delimiter
            + self.baseurl
            + "/status.php"
        )

    def get_webdav_root(self, username):
        return "/remote.php/dav/files/" + username + "/"

    def get_ocsuser(self, node, raiseException=True):
        if self.platform == "win32":
            usercmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsUser '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == "linux":
            env = "NEXTCLOUD_OCS_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniumuser(self, node, raiseException=True):
        if self.platform == "win32":
            usercmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUser '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == "linux":
            env = "NEXTCLOUD_SELENIUM_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfauser(self, node, raiseException=True):
        if self.platform == "win32":
            usercmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUser '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_MFA_USER_"
                + node.upper()
                + "_"
                + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_jupyteruser(self, node):
        if self.platform == "win32":
            usercmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUser '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == "linux":
            env = "NEXTCLOUD_JUPYTER_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_ocsuserpassword(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsPassword '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = "NEXTCLOUD_OCS_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniumuserpassword(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserPassword '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_PASSWORD_"
                + node.upper()
                + "_"
                + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfauserpassword(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserPassword '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_MFA_PASSWORD_"
                + node.upper()
                + "_"
                + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_jupyteruserpassword(self, node):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserPassword '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_JUPYTER_PASSWORD_" + node.upper() + "_" + self.target.upper()
            )
            return get_value(env)
        else:
            raise NotImplementedError

    def get_ocsuserapppassword(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsAppPassword '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_OCS_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniumuserapppassword(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserAppPassword '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_APP_PASSWORD_"
                + node.upper()
                + "_"
                + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfauserapppassword(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserAppPassword '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_"
                + node.upper()
                + "_"
                + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniumusertotpsecret(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserTotpSecret '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_SECRET_" + node.upper() + "_" + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfausertotpsecret(self, node, raiseException=True):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserTotpSecret '
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_MFA_SECRET_"
                + node.upper()
                + "_"
                + self.target.upper()
            )
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def save_ocsusercredentials(self, node):
        if self.platform == "win32":
            cmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Save-OcsCredentials '
                + node
                + " "
                + self.target
                + ' }"'
            )
            os.system(cmd)
        elif self.platform == "linux":
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_seleniumusercredentials(self, node):
        if self.platform == "win32":
            cmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Save-SeleniumCredentials '
                + node
                + " "
                + self.target
                + ' }"'
            )
            os.system(cmd)
        elif self.platform == "linux":
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_ocsuserappcredentials(self, node):
        if self.platform == "win32":
            cmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Save-OcsAppCredentials '
                + node
                + " "
                + self.target
                + ' }"'
            )
            os.system(cmd)
        elif self.platform == "linux":
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_seleniumuserappcredentials(self, node):
        if self.platform == "win32":
            cmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Save-SeleniumAppCredentials '
                + node
                + " "
                + self.target
                + ' }"'
            )
            os.system(cmd)
        elif self.platform == "linux":
            raise NotImplementedError
        else:
            raise NotImplementedError

    def get_samlusername(self, userid):
        if self.platform == "win32":
            usercmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserName '
                + userid
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == "linux":
            env = "NEXTCLOUD_SAML_USER_" + userid.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_samluseralias(self, userid):
        if self.platform == "win32":
            usercmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserName '
                + userid
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SAML_USER_"
                + userid.upper()
                + "_ALIAS_"
                + self.target.upper()
            )
            return get_value(env)
        else:
            raise NotImplementedError

    def get_samluserpassword(self, userid):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserPassword '
                + userid
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SAML_PASSWORD_" + userid.upper() + "_" + self.target.upper()
            )
            return get_value(env)
        else:
            raise NotImplementedError

    def get_samlusertotpsecret(self, userid):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserTotpSecret '
                + userid
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SELENIUM_SAML_MFA_SECRET_"
                + userid.upper()
                + "_"
                + self.target.upper()
            )
            return get_value(env)
        else:
            raise NotImplementedError

    def save_samlusercredentials(self, userid):
        if self.platform == "win32":
            cmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Save-SamlUserCredentials '
                + userid
                + " "
                + self.target
                + ' }"'
            )
            os.system(cmd)
        elif self.platform == "linux":
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_userappcredentials(self, userid, node):
        if self.platform == "win32":
            cmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Save-UserAppCredentials '
                + userid
                + " "
                + node
                + " "
                + self.target
                + ' }"'
            )
            os.system(cmd)
        elif self.platform == "linux":
            raise NotImplementedError
        else:
            raise NotImplementedError

    def get_userapppassword(self, userid, node):
        if self.platform == "win32":
            pwdcmd = (
                'powershell -command "& { . ./NodeCredentials.ps1; Get-UserAppPassword '
                + userid
                + " "
                + node
                + " "
                + self.target
                + ' }"'
            )
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == "linux":
            env = (
                "NEXTCLOUD_SAML_PASSWORD_" + userid.upper() + "_" + self.target.upper()
            )
            return get_value(env)
        else:
            raise NotImplementedError

    def run_tests(self, filename):
        logger.info(f"Running tests for {filename}")
        ts = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
        reportName = f"nextcloud-{self.expectedResults[self.target]['status']['version']}-{filename}-{ts}.xml"
        if self.testrunner == "xml":
            reportFolder = "test-reports/"
            reportFullPath = f"{reportFolder}{reportName}"
            with open(reportFullPath, "wb") as output:
                unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
        elif self.testrunner == "txt":
            unittest.main(
                testRunner=unittest.TextTestRunner(resultclass=NumbersTestResult)
            )
        else:
            reportFolder = "test-reports-html/"
            unittest.main(
                testRunner=HtmlTestRunner.HTMLTestRunner(
                    output=reportFolder,
                    combine_reports=False,
                    report_name=reportName,
                    add_timestamp=False,
                ),
                resultclass=NumbersTestResult,
            )


class Helper:
    def get_random_string(self, length):
        # With combination of lower and upper case
        result_str = "".join(random.choice(string.ascii_letters) for i in range(length))
        # print random string
        return result_str


class SeleniumHelper:
    class UserType(Enum):
        SELENIUM = 1
        SELENIUM_MFA = 2
        OCS = 3
        BASIC = 4
        UNKNOWN = -1

    def __init__(self, browser, nextcloudnode) -> None:
        self.nextcloudnode = nextcloudnode
        self.drv = TestTarget()
        delay = 30
        self.prepare_driver(browser)
        self.wait = WebDriverWait(self.driver, delay)
        pass

    def prepare_driver(self, browser):
        try:
            if browser == "chrome":
                options = ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-extensions")

                if not self.drv.verify:
                    options.add_argument("--ignore-certificate-errors")
                self.driver = webdriver.Chrome(options=options)
            elif browser == "firefox":
                if not use_driver_service:
                    logger.info("Initialize Firefox driver without driver service")
                    options = FirefoxOptions()
                    if not self.drv.verify:
                        options.add_argument("--ignore-certificate-errors")
                    # options.add_argument("--headless")
                    self.driver = webdriver.Firefox(options=options)
                else:
                    logger.info(
                        "Initialize Firefox driver using snap geckodriver and driver service"
                    )
                    driver_service = webdriver.FirefoxService(
                        executable_path=geckodriver_path
                    )
                    self.driver = webdriver.Firefox(
                        service=driver_service, options=options
                    )
            elif browser == "edge":
                if not use_driver_service:
                    logger.info("Initialize Edge driver without driver service")
                    options = EdgeOptions()
                    if not self.drv.verify:
                        options.add_argument("--ignore-certificate-errors")
                    # options.add_argument("--headless")
                    self.driver = webdriver.Edge(options=options)
                else:
                    logger.info(
                        "Initialize Edge driver using snap geckodriver and driver service"
                    )
                    driver_service = webdriver.FirefoxService(
                        executable_path=geckodriver_path
                    )
                    self.driver = webdriver.Firefox(
                        service=driver_service, options=options
                    )
            elif browser == "firefox_grid":
                logger.info("Initialize Firefox grid driver")
                options = FirefoxOptions()
                # options.add_argument("--no-sandbox")
                # options.add_argument("--disable-dev-shm-usage")
                # options.add_argument("--disable-gpu")
                # options.add_argument("--disable-extensions")
                if not self.drv.verify:
                    options.add_argument("--ignore-certificate-errors")
                self.driver = webdriver.Remote(
                    command_executor=self.drv.testgridaddress, options=options
                )
            elif browser == "chrome_grid":
                logger.info(f"Initialize Chrome grid driver")
                if not self.drv.verify:
                    options.add_argument("--ignore-certificate-errors")
                options = ChromeOptions()
                self.driver = webdriver.Remote(
                    command_executor=self.drv.testgridaddress, options=options
                )
            elif browser == "edge_grid":
                logger.info(f"Initialize Edge grid driver")
                if not self.drv.verify:
                    options.add_argument("--ignore-certificate-errors")
                options = EdgeOptions()
                self.driver = webdriver.Remote(
                    command_executor=self.drv.testgridaddress, options=options
                )
                logger.info(f"Edge grid driver init done")
            else:
                logger.error(f"Unknown browser {browser}")
                raise Exception(f"Unknown browser {browser}")
        except Exception as e:
            logger.error(f"Error initializing driver for {browser}: {e}")
            raise Exception(f"Error initializing driver for {browser}: {e}")
        return

    def delete_cookies(self):
        cookies = self.driver.get_cookies()
        logger.debug(f"Deleting all cookies: {cookies}")
        self.driver.delete_all_cookies()
        logger.info("All cookies deleted")
        return

    def nodelogin(
        self,
        usertype: UserType,
        username="",
        password="",
        apppwd="",
        totpsecret="",
        mfaUser=True,
        skipAppMenuCheck=False,
        addOtp=False,
        acceptToS=False,
    ):
        nodetotpsecret = ""
        loginurl = self.drv.get_node_login_url(self.nextcloudnode)
        if usertype == usertype.SELENIUM:
            nodeuser = self.drv.get_seleniumuser(self.nextcloudnode)
            nodepwd = self.drv.get_seleniumuserpassword(self.nextcloudnode)
            nodetotpsecret = self.drv.get_seleniumusertotpsecret(self.nextcloudnode)
            isMfaUser = mfaUser
        elif usertype == usertype.SELENIUM_MFA:
            nodeuser = self.drv.get_seleniummfauser(self.nextcloudnode)
            nodepwd = self.drv.get_seleniummfauserpassword(self.nextcloudnode)
            nodetotpsecret = self.drv.get_seleniummfausertotpsecret(self.nextcloudnode)
            isMfaUser = mfaUser
        elif usertype == usertype.OCS:
            nodeuser = self.drv.get_ocsuser(self.nextcloudnode)
            nodepwd = self.drv.get_ocsuserpassword(self.nextcloudnode)
            nodetotpsecret = totpsecret
            isMfaUser = True
        elif usertype == usertype.BASIC:
            nodeuser = username
            nodepwd = password
            nodetotpsecret = totpsecret
            isMfaUser = mfaUser
        else:
            logger.error(f"Unknown usertype {usertype}")
            return False

        loginurl = self.drv.get_node_login_url(self.nextcloudnode)

        try:
            r = requests.get(loginurl, timeout=g_requestTimeout, verify=False)
            if "This service is currently unavailable." in r.text:
                raise Exception(f"{self.nextcloudnode} is not available!")
        except Exception as error:
            logger.error(f"Failed to request data from {loginurl}: {error}")
            return

        self.driver.get(loginurl)
        if self.driver.current_url != loginurl:
            logger.warning(f"Retry opening login url: {loginurl}")
            self.driver.get(loginurl)

        try:
            logger.info("Enter username and password")
            currentUrl = self.driver.current_url
            self.wait.until(EC.element_to_be_clickable((By.ID, "user"))).send_keys(
                nodeuser
            )
            self.wait.until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(
                nodepwd + Keys.ENTER
            )
        except Exception as error:
            logger.error(f"Error logging in to {loginurl}: {error}")

        if addOtp:
            logger.info(f"Adding OTP for {username}")
            totpXpath = '//a[@href="/login/setupchallenge/totp"]'
            logger.info(f"Locating {totpXpath}")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, totpXpath)))

            totpselect = self.driver.find_element(By.XPATH, totpXpath)
            totpselect.click()

            self.wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "setup-confirmation__secret")
                )
            )

            nodetotpsecret = self.driver.find_element(
                By.CLASS_NAME, "setup-confirmation__secret"
            ).text.split(" ")[-1]
            totp = pyotp.TOTP(nodetotpsecret)
            currentOtp = totp.now()

            self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*//input[@placeholder="Authentication code"]')
                )
            ).send_keys(currentOtp + Keys.ENTER)
            logger.info(f"OTP added for {username}")
            isMfaUser = True
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "two-factor-provider"))
            )  # Wait for mfa login button and proceed

        if isMfaUser:
            retryCount = 0
            while self.driver.current_url == currentUrl:
                logger.info(f"Wait for URL change after login")
                time.sleep(1)
                retryCount += 1
                if retryCount > g_requestTimeout:
                    logger.error(
                        f"URL did not change after {g_requestTimeout}s: {self.driver.current_url}"
                    )
                    raise TimeoutException
            logger.info(f"MFA login {self.driver.current_url}")
            totpXpath = '//a[contains(@href,"/challenge/totp")]'

            if "selectchallenge" in self.driver.current_url:
                logger.info("Select TOTP provider")
                self.wait.until(EC.element_to_be_clickable((By.XPATH, totpXpath)))
                totpselect = self.driver.find_element(By.XPATH, totpXpath)
                totpselect.click()
            elif "challenge/totp" in self.driver.current_url:
                logger.info("No need to select TOTP provider")
            else:
                logger.error(f"Unexpected url: {self.driver.current_url}")

            currentOtp = 0
            totpRetry = 0
            while totpRetry <= 3:
                totpRetry += 1
                totp = pyotp.TOTP(nodetotpsecret)
                currentOtp = totp.now()
                self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//*//input[@placeholder="Authentication code"]')
                    )
                ).send_keys(currentOtp + Keys.ENTER)
                time.sleep(3)  # Replace with proper check at some point
                if "challenge/totp" in self.driver.current_url:
                    logger.info("Try again")
                    while currentOtp == totp.now():
                        logger.info("Wait for new OTP to be issued")
                        time.sleep(3)
                else:
                    logger.info(f"Logging in to {self.nextcloudnode}")
                    break
        else:
            logger.info("No MFA login")

        if acceptToS:
            logger.info(f"Try to accept ToS: {acceptToS}")
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "terms-content"))
            )  # Wait for the ToS content field

            # Find accept tos button
            acceptButton = None
            try:
                buttons = self.driver.find_elements(By.CLASS_NAME, "button-vue__text")
                for button in buttons:
                    if (
                        "I acknowledge that I have read and agree to the above terms of service"
                        in button.text
                    ):
                        acceptButton = button
            except Exception as error:
                logger.error(f"Unable to find create new app button: {error}")
                return None

            acceptButton.click()

        try:
            if skipAppMenuCheck:
                logger.info("Skip app menu check!")
                return True
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "app-menu")))
            logger.info("App menu is ready!")
        except TimeoutException:
            logger.info("Loading of app menu took too much time!")

        if len(nodetotpsecret) > 0:
            return nodetotpsecret
        else:
            return ""

    def create_app_password(self):
        settingsUrl = self.drv.get_settings_user_security_url(self.nextcloudnode)
        logger.info(f"Open user security settings: {settingsUrl}")
        self.driver.get(settingsUrl)
        self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*//input[@placeholder="App name"]')
            )
        ).send_keys("__testautomation__")

        # Find create new app button
        createButton = None
        try:
            buttons = self.driver.find_elements(By.CLASS_NAME, "button-vue__text")
            for button in buttons:
                if "Create new app password" in button.text:
                    createButton = button
        except Exception as error:
            logger.error(f"Unable to find create new app button: {error}")
            return None

        createButton.click()

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//*//input[@placeholder="Password"]')
            )
        )
        time.sleep(2)
        pwdField = self.driver.find_element(
            By.XPATH, '//*//input[@placeholder="Password"]'
        )
        appPwd = pwdField.get_attribute("value")
        # Click on close icon and return the password
        self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "close-icon"))
        ).click()
        return appPwd


# Override TextTestResult to count subtests as test executions
# Credits: https://stackoverflow.com/questions/45007346/count-subtests-in-python-unittests-separately
class NumbersTestResult(unittest.TextTestResult):
    def addSubTest(self, test, subtest, outcome):
        # handle failures calling base class
        super(NumbersTestResult, self).addSubTest(test, subtest, outcome)
        # add to total number of tests run
        self.testsRun += 1
