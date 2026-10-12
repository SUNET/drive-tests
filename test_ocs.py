"""OCS API tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>

Tests the Nextcloud OCS API on every node under test, mostly as the
OCS admin user with its app password: capabilities, user and group
listing, the required apps (user_saml, auto_groups, stepupauth) and the
lifecycle of a temporary user (create, disable, delete).

Each node is tested in its own thread.

Environment variables:
- NextcloudRandSleep: maximum random start delay in seconds for the
  user lifecycle test, to spread the load over time (default: 60)
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
import unittest
from urllib.parse import quote

import HtmlTestRunner
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import xmlrunner
import random

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
ocsheaders = drv.ocsheaders
expectedResults = drv.expectedResults

g_testPassed = {}
g_requestTimeout = 10
g_maxRandSleep = os.environ.get("NextcloudRandSleep")
if g_maxRandSleep is None:
    g_maxRandSleep = 60
else:
    g_maxRandSleep = int(g_maxRandSleep)

g_userprefix=datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
g_userCooldown = 3      # Seconds to cool down between create, deactivate, delete

logger = logging.getLogger("TestLogger")
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


class AppVersions(threading.Thread):
    """Thread that checks the required apps on a node.

    If user_saml is installed, its version must be listed in expected.yaml.
    auto_groups and stepupauth must be installed; stepupauth is enabled
    with a POST to its app endpoint.
    """
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global logger
        global expectedResults
        global g_testPassed
        logger.info(f"AppVersion thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f"Setting passed for {fullnode} to {g_testPassed.get(fullnode)}")

        rawurl = None
        try:
            userSamlFound = False
            session = requests.Session()
            rawurl = drv.get_all_apps_url(fullnode)
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)

            logger.info(f"Getting apps for {rawurl}")
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception as error:
            logger.error(f"Error getting credentials for {rawurl}:{error}")
            return

        try:
            r = session.get(url, headers=ocsheaders, verify=self.verify, timeout=g_requestTimeout)
        except Exception as error:
            logger.error(f"Error getting apps for {fullnode}:{error}")
            return
        # nodeApps = []   # TODO: Check for apps installed on node
        apps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            apps = j["ocs"]["data"]["apps"]
        except Exception as error:
            logger.error(f"No or invalid JSON reply received from {fullnode}:{error}")
            logger.error(r.text)
            g_testPassed[fullnode] = False
            return

        if "user_saml" in apps:
            userSamlFound = True

        # # user_saml check
        if userSamlFound:
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            rawurl = drv.get_app_url(fullnode, "user_saml")

            logger.info(f" Get app info from {rawurl}")
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)

            try:
                r = session.get(url, headers=ocsheaders, verify=self.verify, timeout=g_requestTimeout)
            except Exception as error:
                logger.error(f"Error getting {rawurl}:{error}")
                g_testPassed[fullnode] = False
                return

            try:
                j = json.loads(r.text)
                # print(json.dumps(j, indent=4, sort_keys=True))
                logger.info(j["ocs"]["data"]["id"])
                logger.info(j["ocs"]["data"]["version"])

            except Exception as error:
                logger.info(f"No JSON reply received from {fullnode}:{error}")
                logger.info(r.text)
                g_testPassed[fullnode] = False
                return

            try:
                self.TestOcsCalls.assertTrue(userSamlFound)
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["id"], "user_saml")
                self.TestOcsCalls.assertTrue(
                    j["ocs"]["data"]["version"]
                    in expectedResults["apps"]["user_saml"][drv.target]["version"]
                )
            except Exception as error:
                logger.error(f"{error}")
                g_testPassed[fullnode] = False
                return

        if "auto_groups" not in apps:
            logger.error(f"Autogroups not found for {fullnode}")
            g_testPassed[fullnode] = False
            return
        else:
            try:
                rawurl = drv.get_app_url(fullnode, "auto_groups")
                url = rawurl.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)
                # r = session.post(url, headers=ocsheaders)
            except Exception as error:
                logger.error(
                    f"Error ensuring auto_groups active on {fullnode}: {error}"
                )
                g_testPassed[fullnode] = False
                return

        if "stepupauth" not in apps:
            logger.error(f"stepupauth not found for {fullnode}")
            g_testPassed[fullnode] = False
            return
        else:
            try:
                rawurl = drv.get_app_url(fullnode, "stepupauth")
                url = rawurl.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)
                r = session.post(url, headers=ocsheaders, timeout=g_requestTimeout)
            except Exception as error:
                logger.error(f"Error ensuring stepupauth active on {fullnode}: {error}")
                g_testPassed[fullnode] = False
                return

        g_testPassed[fullnode] = True
        logger.info(
            f"AppVersion thread done for node {self.name}, test passed: {g_testPassed[fullnode]}"
        )
        return


class NodeUsers(threading.Thread):
    """Thread that lists the users of a node. Passes if the reply contains a user list."""
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global logger
        global g_testPassed
        logger.info(f"NodeUsers thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f"Setting passed for {fullnode} to {g_testPassed.get(fullnode)}")

        rawurl = None
        try:
            rawurl = drv.get_users_url(fullnode)
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            logger.info(f"Get users from {rawurl}")
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception as error:
            logger.error(f"Error getting credentials for {rawurl}:{error}")
            return

        try:
            r = requests.get(
                url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify
            )
        except Exception as error:
            logger.error(f"Error getting {rawurl}:{error}")
            return
        try:
            j = json.loads(r.text)
            # logger.info(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
            logger.info(f"Received {len(users)} from {self.name}")
            # for user in users:
            #     rawurl = drv.get_user_url(fullnode, user)
            #     url = rawurl.replace("$USERNAME$", nodeuser)
            #     url = url.replace("$PASSWORD$", nodepwd)
            #     r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
            #     j = json.loads(r.text)
            #     logger.info(json.dumps(j, indent=4, sort_keys=True))

        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}:{error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            return

        g_testPassed[fullnode] = True
        logger.info(
            f"NodeUsers thread done for node {self.name}, test passed: {g_testPassed[fullnode]}"
        )
        return


class NodeGroups(threading.Thread):
    """Thread that checks that the forcemfa group exists on a node.

    Lists the groups with their details. kau is excluded from the check.
    """
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global logger
        global g_testPassed
        logger.info(f"NodeGroups thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f"Setting passed for {fullnode} to {g_testPassed.get(fullnode)}")

        rawurl = None
        try:
            # rawurl = drv.get_groups_url(fullnode)
            rawurl = drv.get_groups_details_url(fullnode)
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            logger.info(f"Add group through {rawurl}")
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception as error:
            logger.error(f"Error getting credentials for {rawurl}:{error}")
            return

        try:
            r = requests.get(
                url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify
            )
        except Exception as error:
            logger.error(f"Error getting {rawurl}:{error}")
            return
        try:
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))
            groups = j["ocs"]["data"]["groups"]
            logger.info(f"Received {len(groups)} groups from {self.name}")
            # for group in groups:
            #     groupid = group["id"]
            #     logger.info(f'Group id: {groupid}')
            #     groupid = quote(groupid)
            #     rawurl = drv.get_group_url(fullnode, groupid)
            #     url = rawurl.replace("$USERNAME$", nodeuser)
            #     url = url.replace("$PASSWORD$", nodepwd)
            #     r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
            #     logger.info(f'{r.text}')

        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}:{error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            return

        # Test for forcemfa group
        # logger.info(json.dumps(j, indent=4, sort_keys=True))
        forceMfaFound = False
        for group in j["ocs"]["data"]["groups"]:
            if group["displayname"].lower() == "forcemfa":
                forceMfaFound = True

        if forceMfaFound:
            logger.info(f"Found forcemfa on {fullnode}")
        else:
            logger.info(f"Group forcemfa does not exist on {fullnode}")
            if fullnode == "kau":
                logger.warning("Excluding kau from test")
                g_testPassed[fullnode] = True
            else:
                g_testPassed[fullnode] = False
                logger.info(r.text)
            return

        g_testPassed[fullnode] = True
        logger.info(
            f"NodeUsers thread done for node {self.name}, test passed: {g_testPassed[fullnode]}"
        )
        return


class CapabilitiesNoUser(threading.Thread):
    """Thread that checks the OCS capabilities of a node without logging in.

    Compares the OCS status, status code, message and Nextcloud version
    string with expected.yaml.
    """
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global g_testPassed
        global logger
        global expectedResults
        logger.info(f"Capabilities no user thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f"Setting passed for {fullnode} to {g_testPassed.get(fullnode)}")

        rawurl = drv.get_ocs_capabilities_url(fullnode)
        logger.info(f"{self.TestOcsCalls._testMethodName} {rawurl}")
        try:
            r = requests.get(
                rawurl, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify
            )
        except Exception as error:
            logger.error(f"Error getting {rawurl}: {error}")
            return
        try:
            j = json.loads(r.text)
        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}: {error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            return

        try:
            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["status"],
                expectedResults[drv.target]["ocs_capabilities"]["ocs_meta_status"],
            )
            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["statuscode"],
                expectedResults[drv.target]["ocs_capabilities"][
                    "ocs_meta_statuscode_2"
                ],
            )
            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["message"],
                expectedResults[drv.target]["ocs_capabilities"]["ocs_meta_message"],
            )
            self.TestOcsCalls.assertTrue(
                j["ocs"]["data"]["version"]["string"]
                in expectedResults[drv.target]["ocs_capabilities"][
                    "ocs_data_version_string"
                ]
            )
        except Exception as error:
            logger.error(f"Error with OCS capabilities assertion: {error} - {j}")
            g_testPassed[fullnode] = False
            return

        g_testPassed[fullnode] = True
        logger.info(
            f"Capabilities no user thread done for node {self.name}, test passed: {g_testPassed[fullnode]}"
        )
        return


class Capabilities(threading.Thread):
    """Thread that fetches and logs the OCS capabilities of a node. Passes if the reply is valid JSON."""
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global g_testPassed
        global logger
        logger.info(f"Capabilities thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f"Setting passed for {fullnode} to {g_testPassed.get(fullnode)}")

        rawurl = drv.get_ocs_capabilities_url(fullnode)
        logger.info(f"{self.TestOcsCalls._testMethodName} {rawurl}")

        try:
            r = requests.get(
                rawurl, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify
            )
        except Exception as error:
            logger.error(f"Error getting {rawurl}: {error}")
            return
        try:
            j = json.loads(r.text)
            logger.info(f"Node capabilities: {json.dumps(j, indent=4, sort_keys=True)}")

        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}: {error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            return

        g_testPassed[fullnode] = True
        logger.info(
            f"Capabilities thread done for node {self.name}, test passed: {g_testPassed[fullnode]}"
        )
        return


class UserLifeCycle(threading.Thread):
    """Thread that creates, disables and deletes a temporary user on a node.

    After a random start delay, the OCS admin user confirms its app
    password and creates the user __cli_user_<timestamp>_<node>. It then
    checks the user's groups (warns if forcemfa is missing), disables the
    user and deletes it. Each step is retried once on an OCS error, and the
    replies of disable and delete are compared with expected.yaml.
    """
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global g_testPassed
        global expectedResults

        start_delay = random.randint(0,g_maxRandSleep)
        logger.info(f"UserLifeCycle thread for node {self.name} starting in {start_delay} seconds")
        time.sleep(start_delay)

        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f"Setting passed for {fullnode} to {g_testPassed.get(fullnode)}")
        r = None
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # Confirm app password for session

        try:
            nodeuser = drv.get_ocsuser(fullnode)
            nodeapppwd = drv.get_ocsuserapppassword(fullnode)
            nodepwd = drv.get_ocsuserpassword(fullnode)
        except Exception as error:
            logger.error(f"Error getting credentials for {fullnode}:{error}")
            return

        cliuser = "__cli_user_" + g_userprefix + "_" + fullnode
        clipwd = sunetnextcloud.Helper().get_random_string(12)

        logger.info(f"Confirm app password for {nodeuser}")
        try:
            rawurl = drv.get_confirm_apppassword_url(fullnode)
            logger.info(f"Confirm app password using {rawurl}")
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodeapppwd)

            data = {
                "password": nodepwd  # Replace with the user's password
            }

            r = session.put(
                url,
                headers=ocsheaders,
                json=data,
                timeout=g_requestTimeout,
                verify=True,
            )
            logger.info(r.text)
        except Exception as error:
            logger.error(f"Error confirming app password: {error}")
            g_testPassed[fullnode] = False
            return

        logger.info(f"Create cli user {cliuser}")
        data = {"userid": cliuser, "password": clipwd}
        try:
            rawurl = drv.get_users_url(fullnode)
            logger.info(f"Add user through {rawurl}")
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodeapppwd)
            r = session.post(url, headers=ocsheaders, data=data, verify=self.verify, timeout=g_requestTimeout)
            logger.info(f"cli user created with status {r.status_code} - {r.text}")
            time.sleep(g_userCooldown)
        except Exception as error:
            logger.error(f"Error posting to create cli user: {error}")
            g_testPassed[fullnode] = False
            return

        try:
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if j["ocs"]["meta"]["statuscode"] == 102:
                logger.info(f"User already exists, skip retry creating the user")
            elif j["ocs"]["meta"]["statuscode"] != 200:
                logger.info(
                    f"Retry once to create cli user {cliuser} after error {j['ocs']['meta']['statuscode']}"
                )
                r = session.post(url, headers=ocsheaders, data=data, verify=self.verify, timeout=g_requestTimeout)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))
                time.sleep(g_userCooldown)
        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}: {error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            return

        logger.info(f"Get user info for {cliuser}")
        userinfourl = drv.get_user_url(fullnode, cliuser)
        userinfourl = userinfourl.replace("$USERNAME$", nodeuser)
        userinfourl = userinfourl.replace("$PASSWORD$", nodeapppwd)
        try:
            r = session.get(userinfourl, headers=ocsheaders, verify=self.verify, timeout=g_requestTimeout)
            j = json.loads(r.text)
            if "forcemfa" not in j["ocs"]["data"]["groups"]:
                logger.warning(
                    f"focemfa not in user groups (yet?), sleeping for a second"
                )
                time.sleep(1)
            time.sleep(g_userCooldown)
        except Exception as error:
            logger.error(f"No or invalid JSON reply received from {rawurl}: {error}")
            if r is not None:
                logger.error(f"Last response: {r.text}")
            else:
                logger.error(f"No last response received")
            g_testPassed[fullnode] = False
            return

        # self.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
        # self.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
        # self.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])

        logger.info(f"Disable cli user {cliuser}")
        disableuserurl = drv.get_disable_user_url(fullnode, cliuser)
        disableuserurl = disableuserurl.replace("$USERNAME$", nodeuser)
        disableuserurl = disableuserurl.replace("$PASSWORD$", nodeapppwd)
        try:
            r = session.put(disableuserurl, headers=ocsheaders, verify=self.verify, timeout=g_requestTimeout)
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))
            time.sleep(g_userCooldown)

            if j["ocs"]["meta"]["statuscode"] != 200:
                logger.info(
                    f"Retry to disable cli user {cliuser} after error {j['ocs']['meta']['statuscode']}"
                )
                r = session.put(disableuserurl, headers=ocsheaders, verify=self.verify, timeout=g_requestTimeout)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))
                time.sleep(g_userCooldown)

            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["status"],
                expectedResults[drv.target]["ocs_capabilities"]["ocs_meta_status"],
            )
            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["statuscode"],
                expectedResults[drv.target]["ocs_capabilities"][
                    "ocs_meta_statuscode_2"
                ],
            )
            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["message"],
                expectedResults[drv.target]["ocs_capabilities"]["ocs_meta_message"],
            )

            logger.info(f"Delete cli user {cliuser}")
            rawurl = drv.get_user_url(fullnode, cliuser)
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodeapppwd)
            r = session.delete(url, headers=ocsheaders, verify=drv.verify, timeout=g_requestTimeout)
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))
            time.sleep(g_userCooldown)

            if j["ocs"]["meta"]["statuscode"] != 200:
                logger.info(
                    f"Retry to delete cli user after {cliuser} after error {j['ocs']['meta']['statuscode']}"
                )
                r = session.delete(url, headers=ocsheaders, verify=self.verify, timeout=g_requestTimeout)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))
                time.sleep(g_userCooldown)

            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["status"],
                expectedResults[drv.target]["ocs_capabilities"]["ocs_meta_status"],
            )
            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["statuscode"],
                expectedResults[drv.target]["ocs_capabilities"][
                    "ocs_meta_statuscode_2"
                ],
            )
            self.TestOcsCalls.assertEqual(
                j["ocs"]["meta"]["message"],
                expectedResults[drv.target]["ocs_capabilities"]["ocs_meta_message"],
            )
        except Exception as error:
            logger.error(f"No or invalid JSON reply received from {rawurl}: {error}")
            if r is not None:
                logger.error(f"Last response: {r.text}")
            else:
                logger.error(f"No last response received")
            g_testPassed[fullnode] = False
            return

        g_testPassed[fullnode] = True
        logger.info(
            f"User lifecycle thread done for node {self.name}, test passed: {g_testPassed[fullnode]}"
        )
        return


class TestOcsCalls(unittest.TestCase):
    """OCS API tests for all nodes under test."""
    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_capabilities_nouser(self):
        """Check the OCS capabilities of all nodes without logging in."""
        drv = sunetnextcloud.TestTarget()
        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                capabilitiesNoUserThread = CapabilitiesNoUser(
                    fullnode, self, verify=drv.verify
                )
                capabilitiesNoUserThread.start()
                threads.append(capabilitiesNoUserThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_capabilities(self):
        """Check that all nodes return their OCS capabilities as valid JSON."""
        drv = sunetnextcloud.TestTarget()
        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                capabilitiesThread = Capabilities(fullnode, self, verify=drv.verify)
                capabilitiesThread.start()
                threads.append(capabilitiesThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_nodeusers(self):
        """Check that the users of all nodes can be listed."""
        drv = sunetnextcloud.TestTarget()
        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                nodeUsersThread = NodeUsers(fullnode, self, verify=drv.verify)
                nodeUsersThread.start()
                threads.append(nodeUsersThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_nodegroups(self):
        """Check that the forcemfa group exists on all nodes."""
        drv = sunetnextcloud.TestTarget()
        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                nodeGroupsThread = NodeGroups(fullnode, self, verify=drv.verify)
                nodeGroupsThread.start()
                threads.append(nodeGroupsThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_userlifecycle(self):
        """Create, disable and delete a temporary user on all nodes."""
        drv = sunetnextcloud.TestTarget()
        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                userLifecycleThread = UserLifeCycle(fullnode, self, verify=drv.verify)
                userLifecycleThread.start()
                threads.append(userLifecycleThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_app_versions(self):
        """Check the user_saml version and that auto_groups and stepupauth are installed on all nodes."""
        drv = sunetnextcloud.TestTarget()
        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                appVersionsThread = AppVersions(fullnode, self, verify=drv.verify)
                appVersionsThread.start()
                threads.append(appVersionsThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))


# if __name__ == "__main__":
#     drv.run_tests(os.path.basename(__file__))

if __name__ == "__main__":
    if drv.testrunner == "xml":
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output="test-reports"))
    elif drv.testrunner == "txt":
        unittest.main(
            testRunner=unittest.TextTestRunner(
                resultclass=sunetnextcloud.NumbersTestResult
            )
        )
    else:
        unittest.main(
            testRunner=HtmlTestRunner.HTMLTestRunner(
                output="test-reports-html",
                combine_reports=True,
                report_name=f"nextcloud-{drv.target}-{drv.expectedResults[drv.target]['status']['version'][-1]}-{os.path.basename(__file__)}",
                add_timestamp=False,
            )
        )
