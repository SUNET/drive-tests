"""App tests for Sunet Drive via the OCS API
Author: Richard Freitag <freitag@sunet.se>

Checks the Nextcloud apps on every node under test against
expected.yaml: the number of apps on each frontend server, that the
configured apps are installed, that the installed apps support the
running Nextcloud major version, and that the required apps
announcementcenter, security_guard and stepupauth are installed.

Each node is tested in its own thread.
"""

import json
import logging
import os
import threading
import time
import unittest

import requests
import xmlrunner
import HtmlTestRunner
import yaml

import sunetnextcloud

expectedResultsFile = "expected.yaml"
testThreadRunning = False
g_testPassed = {}
g_requestTimeout = 10

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

drv = sunetnextcloud.TestTarget()
ocsheaders = drv.ocsheaders

with open(expectedResultsFile, "r") as stream:
    expectedResults = yaml.safe_load(stream)


class ConfiguredAppsInstalled(threading.Thread):
    """Thread that checks that the apps listed in expected.yaml are installed on a node.

    Missing apps are logged as warnings. The node passes as soon as one of
    the configured apps is found.
    """
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global testThreadRunning, logger, g_testPassed
        logger.info(f"ConfiguredAppsInstalled thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False

        try:
            session = requests.Session()
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = drv.get_all_apps_url(fullnode)

            logger.info(f"{url}")
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)

            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserpassword(fullnode)
        except Exception:
            logger.error(f"Credentials error for {self.name}")
            return

        try:
            r = session.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except Exception:
            logger.error(f"Error getting {url}")
            return
        nodeApps = []
        try:
            j = json.loads(r.text)
            nodeApps = j["ocs"]["data"]["apps"]
            # print(json.dumps(j, indent=4, sort_keys=True))
        except Exception:
            logger.warning(f"No JSON reply received on node {fullnode}")
            # self.logger.warning(r.text)
            return

        logger.info(
            f"Check if all apps configured in {expectedResultsFile} are installed on {fullnode}"
        )

        for expectedApp in expectedResults["apps"]:
            logger.info(f"Check if {expectedApp} is installed on {fullnode}")
            print()
            try:
                pos = nodeApps.index(expectedApp)
                logger.info(f"Found app at {pos}")
                g_testPassed[fullnode] = True
            except Exception:
                logger.warning(f"App {expectedApp} NOT found on {fullnode}")

        logger.info(f"ConfiguredAppsInstalled thread done for node {self.name}")


class InstalledAppsCompatibility(threading.Thread):
    """Thread that checks that the installed apps support the expected Nextcloud version.

    Compares each app's Nextcloud max-version with status.major_version in
    expected.yaml. Incompatible apps fail the node, except apps in
    ocsapps.excluded_apps, which are only logged as warnings.
    """
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global testThreadRunning, logger, g_testPassed
        logger.info(f"InstalledAppsCompatibility thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = True

        try:
            session = requests.Session()
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = drv.get_all_apps_url(fullnode)

            logger.info(f"{url}")
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception:
            logger.error(f"Credentials error for {self.name}")
            g_testPassed[fullnode] = False
            return

        try:
            r = session.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except Exception:
            logger.error(f"Error getting {url}")
            g_testPassed[fullnode] = False
            return
        nodeApps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            nodeApps = j["ocs"]["data"]["apps"]
            logger.info(
                f"Apps found on node {fullnode}: {json.dumps(j, indent=4, sort_keys=True)}"
            )
        except Exception:
            logger.warning(f"No JSON reply received on {fullnode}")
            # self.logger.warning(r.text)
            g_testPassed[fullnode] = False
            return

        # We check against this manual exception list until the deployment is clean
        excludeList = expectedResults[drv.target]["ocsapps"]["excluded_apps"]
        expectedVersion = expectedResults[drv.target]["status"]["major_version"]
        allPassed = True
        for nodeApp in nodeApps:
            try:
                # appInfo = expectedResults['apps'][nodeApp]
                clean_url = drv.get_app_url(fullnode, nodeApp)
                secret_url = clean_url
                secret_url = secret_url.replace("$USERNAME$", nodeuser)
                secret_url = secret_url.replace("$PASSWORD$", nodepwd)

                try:
                    r = session.get(secret_url, headers=ocsheaders, timeout=g_requestTimeout)
                except Exception:
                    logger.error(f"Error getting {clean_url}")
                    g_testPassed[fullnode] = False
                    return

                try:
                    j = json.loads(r.text)
                    # print(json.dumps(j, indent=4, sort_keys=True))
                    maxVersion = j["ocs"]["data"]["dependencies"]["nextcloud"][
                        "@attributes"
                    ]["max-version"]
                    logger.info(f"App {nodeApp} has max version {maxVersion}")
                    if int(maxVersion) < expectedVersion:
                        if nodeApp in excludeList:
                            logger.warning(
                                f"{fullnode} - App {nodeApp} is not supported by Nextcloud {expectedVersion} (max {maxVersion})"
                            )
                        else:
                            logger.error(
                                f"{fullnode} - App {nodeApp} is not supported by Nextcloud {expectedVersion} (max {maxVersion})"
                            )
                            g_testPassed[fullnode] = False
                            allPassed = False

                except Exception as error:
                    logger.warning(f"No JSON reply received on {fullnode}: {error}")
                    # self.logger.warning(r.text)
                    g_testPassed[fullnode] = False
                    return
            except Exception:
                logger.warning(f"{nodeApp} NOT found on {fullnode}")

        if allPassed == False:
            logger.error(f"Not all apps compatible with {fullnode}")
            g_testPassed[fullnode] = False

        logger.info(f"InstalledAppsCompatibility thread done for node {self.name}")


class InstalledAppsConfigured(threading.Thread):
    """Thread that checks the installed apps of a node.

    With app="all", the installed apps are only listed; comparing them with
    expected.yaml is not implemented yet. With an app name, the node passes
    if that app is installed. checkEnabled is currently not used.
    """
    def __init__(self, name, app="all", checkEnabled=False):
        threading.Thread.__init__(self)
        self.name = name
        self.app = app
        self.checkEnabled = checkEnabled

    def run(self):
        global testThreadRunning, logger, g_testPassed
        logger.info(f"InstalledAppsConfigured thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False

        try:
            session = requests.Session()
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = drv.get_all_apps_url(fullnode)

            logger.info(f"{url}")
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception:
            logger.error(f"Credentials error for {self.name}")
            return

        try:
            r = session.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except Exception:
            logger.error(f"Error getting {url}")
            return
        nodeApps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            nodeApps = j["ocs"]["data"]["apps"]
            logger.info(
                f"Apps found on node {fullnode}: {json.dumps(j, indent=4, sort_keys=True)}"
            )
        except Exception:
            logger.warning(f"No JSON reply received on {fullnode}")
            # self.logger.warning(r.text)
            return

        if self.app == "all":
            logger.info(
                f"Check if all installed apps on {fullnode} are found in {expectedResultsFile}"
            )
            # TODO: Compare application information with expected result
            for nodeApp in nodeApps:
                try:
                    # appInfo = expectedResults['apps'][nodeApp]
                    g_testPassed[fullnode] = True
                except Exception:
                    logger.warning(f"{nodeApp} NOT found on {fullnode}")

        else:  # Check if specific app is installed/active
            try:
                installed = self.app in nodeApps
                logger.info(f"App {self.app} is installed: {installed} on {fullnode}")
                g_testPassed[fullnode] = self.app in nodeApps
            except Exception:
                logger.error(f"{self.app} NOT found on {fullnode}")
                logger.info(f"Apps found are: {nodeApps}")
                return

        logger.info(f"InstalledAppsConfigured thread done for node {self.name}")


class NumberOfAppsOnNodes(threading.Thread):
    """Thread that counts the installed apps on each frontend server (node1-3) of a node.

    Compares the count with ocsapps in expected.yaml (per node, or the
    default). A different count is logged as a warning and does not fail
    the test.
    """
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global testThreadRunning, logger, g_testPassed
        logger.info(f"NumberOfAppsOnNode thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False

        try:
            session = requests.Session()
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = drv.get_all_apps_url(fullnode)

            logger.info(f"{url}")
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)

            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserpassword(fullnode)
        except Exception:
            logger.error(f"Credentials error for {self.name}")
            return

        for fe in range(1, 4):
            nodebaseurl = drv.get_node_base_url(fullnode)
            serverid = f"node{fe}.{nodebaseurl}"
            session.cookies.set("SERVERID", serverid)

            try:
                r = session.get(url, headers=ocsheaders, timeout=g_requestTimeout)
            except Exception:
                logger.error(f"Error getting {url}")
                return
            nodeApps = []
            try:
                j = json.loads(r.text)
                # print(json.dumps(j, indent=4, sort_keys=True))
                nodeApps = j["ocs"]["data"]["apps"]
                logger.info(f"Number of apps on {fullnode}: {len(nodeApps)}")
            except Exception:
                logger.warning(f"No JSON reply received on {fullnode}")
                logger.warning(r.text)
                return

            try:
                numExpectedApps = expectedResults[drv.target]["ocsapps"][fullnode]
                logger.info(
                    f"Expected number of apps differs from default for {fullnode}: {numExpectedApps}"
                )
            except Exception:
                numExpectedApps = expectedResults[drv.target]["ocsapps"]["default"]
                logger.info(f"Expected number of apps: {numExpectedApps}")

            if len(nodeApps) != numExpectedApps:
                logger.warning(
                    f"Warn: Number of apps {len(nodeApps)} != {numExpectedApps} for {self.name} on node {fe}"
                )
                logger.warning(f"Apps found on node: {nodeApps}")
                g_testPassed[f"node{fe}.{fullnode}"] = True
            else:
                logger.info(
                    f"Pass: Number of apps {len(nodeApps)} == {numExpectedApps} for {self.name}"
                )
                g_testPassed[f"node{fe}.{fullnode}"] = True

        logger.info(f"Test number of apps done for node {self.name}")


class TestAppsOcs(unittest.TestCase):
    """App checks for all nodes under test."""
    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        global logger
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_number_of_apps_on_nodes(self):
        """Compare the number of installed apps on each frontend server with expected.yaml."""
        drv = sunetnextcloud.TestTarget()

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                numberOfAppsOnNodeThread = NumberOfAppsOnNodes(fullnode)
                numberOfAppsOnNodeThread.start()
                threads.append(numberOfAppsOnNodeThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                for fe in range(1, 4):
                    self.assertTrue(g_testPassed.get(f"node{fe}.{fullnode}", False))

    def test_installed_apps_configured(self):
        """Check that the installed apps of all nodes can be listed."""
        drv = sunetnextcloud.TestTarget()

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                InstalledAppsConfiguredThread = InstalledAppsConfigured(fullnode)
                InstalledAppsConfiguredThread.start()
                threads.append(InstalledAppsConfiguredThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_configured_apps_installed(self):
        """Check that the apps listed in expected.yaml are installed on all nodes."""
        drv = sunetnextcloud.TestTarget()

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                ConfiguredAppsInstalledThread = ConfiguredAppsInstalled(fullnode)
                ConfiguredAppsInstalledThread.start()
                threads.append(ConfiguredAppsInstalledThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_apps_compatibility(self):
        """Check that the installed apps on all nodes support the expected Nextcloud major version."""
        drv = sunetnextcloud.TestTarget()

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                InstalledAppsConfiguredThread = InstalledAppsCompatibility(fullnode)
                InstalledAppsConfiguredThread.start()
                threads.append(InstalledAppsConfiguredThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                if g_testPassed.get(fullnode, False):
                    logger.info(f"Passed: {g_testPassed.get(fullnode, False)} for {fullnode}")
                else:
                    logger.error(f"Failed: {g_testPassed.get(fullnode, False)} for {fullnode}")
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_app_announcementcenter(self):
        """Check that announcementcenter is installed on all nodes."""
        drv = sunetnextcloud.TestTarget()

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                InstalledAppsConfiguredThread = InstalledAppsConfigured(
                    fullnode, app="announcementcenter", checkEnabled=True
                )
                InstalledAppsConfiguredThread.start()
                threads.append(InstalledAppsConfiguredThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"Passed: {g_testPassed.get(fullnode, False)} for {fullnode}")
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_app_security_guard(self):
        """Check that security_guard is installed on all nodes."""
        drv = sunetnextcloud.TestTarget()

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                InstalledAppsConfiguredThread = InstalledAppsConfigured(
                    fullnode, app="security_guard", checkEnabled=True
                )
                InstalledAppsConfiguredThread.start()
                threads.append(InstalledAppsConfiguredThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"Passed: {g_testPassed.get(fullnode, False)} for {fullnode}")
                self.assertTrue(g_testPassed.get(fullnode, False))

    def test_app_stepupauth(self):
        """Check that stepupauth is installed on all nodes."""
        drv = sunetnextcloud.TestTarget()

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                InstalledAppsConfiguredThread = InstalledAppsConfigured(
                    fullnode, app="stepupauth", checkEnabled=True
                )
                InstalledAppsConfiguredThread.start()
                threads.append(InstalledAppsConfiguredThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"Passed: {g_testPassed.get(fullnode, False)} for {fullnode}")
                self.assertTrue(g_testPassed.get(fullnode, False))


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
