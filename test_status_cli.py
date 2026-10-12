"""Status page and public endpoint tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>

Unauthenticated HTTP checks against every node under test:
- status.php, through the load balancer and on each frontend server
  (node1-3), compared with the expected values in expected.yaml
- the login page uses the SeamlessAccess discovery service
- /.well-known/ocm returns the expected Open Cloud Mesh configuration
- the SAML SP metadata has the expected entity ID and certificate
- the Collabora servers return the expected status

Each node is checked in its own thread. The test method waits for all
threads and reports each failed node as a subtest.
"""

import hashlib
import json
import logging
import os
import threading
import time
import unittest
from xml.etree.ElementTree import fromstring

import requests
from requests.exceptions import RequestException
import xmlrunner
import HtmlTestRunner

import xmltodict

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

g_failedNodes = []
g_requestTimeout = 3
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

def get(url, retries=3, session=None, **kwargs):
    """GET a URL, retrying on errors.

    Retries up to `retries` times, one second apart, on connection errors
    and HTTP error status codes. Uses `session` if given, otherwise
    requests.get. Extra keyword arguments are passed to the request.
    Raises the last exception when all retries fail.
    """
    try:
        # Use the provided session if available, otherwise use requests.get
        if session:
            response = session.get(url, **kwargs)
        else:
            response = requests.get(url, **kwargs)

        # Raise an HTTPError if the response contains an HTTP error status code
        response.raise_for_status()
        return response

    except RequestException as e:
        logger.warning(f'Retry {retries} getting {url}')
        time.sleep(1)
        if retries-1 > 0:
            # Retry the request recursively
            return get(url, retries - 1, session=session, **kwargs)
        else:
            # Raise the exception if no retries are left
            raise e

class NumbersTestResult(unittest.TextTestResult):
    """Text test result that counts every subtest as a test run."""
    def addSubTest(self, test, subtest, outcome):
        """Record the subtest outcome and count it as a test run."""
        # handle failures calling base class
        super(NumbersTestResult, self).addSubTest(test, subtest, outcome)
        # add to total number of tests run
        self.testsRun += 1


class FrontendStatusInfo(threading.Thread):
    """Thread that checks the content of a status.php URL.

    Compares maintenance, needsDbUpgrade, version, versionstring, edition
    and extendedSupport with expected.yaml. With useHttps=False the URL is
    requested over plain HTTP. Failed URLs are added to g_failedNodes.
    """
    def __init__(self, url, TestStatus, verify=True, useHttps=True):
        threading.Thread.__init__(self)
        if useHttps:
            self.url = url
        else:
            # self.url = url.replace('https://', 'http://')
            self.url = url.replace("https://", "http://")
        self.TestStatus = TestStatus
        self.verify = verify
        self.useHttps = useHttps

    def run(self):
        global logger
        global expectedResults
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        logger.info(
            f"FrontendStatusInfo thread started for node {self.url}"
        )

        try:
            r = get(self.url, timeout=g_requestTimeout, verify=self.verify)
        except Exception as error:
            logger.error(f"Error getting frontend status data from {self.url}: {error}")
            g_failedNodes.append(self.url)
            return

        try:
            j = json.loads(r.text)
            self.TestStatus.assertEqual(
                j["maintenance"], expectedResults[drv.target]["status"]["maintenance"]
            )
            self.TestStatus.assertEqual(
                j["needsDbUpgrade"],
                expectedResults[drv.target]["status"]["needsDbUpgrade"],
            )
            self.TestStatus.assertTrue(
                j["version"] in expectedResults[drv.target]["status"]["version"]
            )
            self.TestStatus.assertTrue(
                j["versionstring"]
                in expectedResults[drv.target]["status"]["versionstring"]
            )
            self.TestStatus.assertEqual(
                j["edition"], expectedResults[drv.target]["status"]["edition"]
            )
            # self.assertEqual(j["productname"], statusResult.productname)
            self.TestStatus.assertEqual(
                j["extendedSupport"],
                expectedResults[drv.target]["status"]["extendedSupport"],
            )
            logger.info(f"Status information tested: {self.url}")
        except Exception as error:
            g_failedNodes.append(self.url)
            logger.info(f"No valid JSON reply received for {self.url}: {error}")
            logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f"Status thread done for node {self.url}")


class NodeStatusInfo(threading.Thread):
    """Thread that checks status.php on each frontend server (node1-3) of a node.

    Runs the same checks as FrontendStatusInfo directly against
    node<N>.<node URL>, bypassing the load balancer. TLS certificates are
    not verified for these requests.
    """
    def __init__(self, node, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.node = node
        self.TestStatus = TestStatus
        self.verify = verify

    def run(self):
        global logger
        global expectedResults
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        logger.info(
            f"NodeStatusInfo thread started for node {self.node}"
        )

        x = range(1, 4)
        for i in x:
            url = drv.get_node_status_url(self.node, i)
            try:
                logger.info(f"Getting status from: {url}")
                r = get(url, timeout=g_requestTimeout, verify=False)
            except Exception as error:
                logger.error(
                    f"Error getting node status data from {self.node}: {error}"
                )
                g_failedNodes.append(url)
                return

            try:
                j = json.loads(r.text)
            except Exception as error:
                g_failedNodes.append(url)
                logger.info(f"No valid JSON reply received for {url}: {error}")
                logger.info(r.text)
                self.TestStatus.assertTrue(False)
                return

            try:
                self.TestStatus.assertEqual(
                    j["maintenance"],
                    expectedResults[drv.target]["status"]["maintenance"],
                )
                self.TestStatus.assertEqual(
                    j["needsDbUpgrade"],
                    expectedResults[drv.target]["status"]["needsDbUpgrade"],
                )
                self.TestStatus.assertTrue(
                    j["version"] in expectedResults[drv.target]["status"]["version"]
                )
                self.TestStatus.assertTrue(
                    j["versionstring"]
                    in expectedResults[drv.target]["status"]["versionstring"]
                )
                self.TestStatus.assertEqual(
                    j["edition"], expectedResults[drv.target]["status"]["edition"]
                )
                # self.assertEqual(j["productname"], statusResult.productname)
                self.TestStatus.assertEqual(
                    j["extendedSupport"],
                    expectedResults[drv.target]["status"]["extendedSupport"],
                )
                logger.info(f"Status information tested: {url}")
            except Exception as error:
                g_failedNodes.append(url)
                logger.info(f"Assertion error for {url}: {error}")
                logger.info(r.text)
                self.TestStatus.assertTrue(False)
                return

        logger.info(f"Status thread done for node {url}")


class StatusInfo(threading.Thread):
    """Thread that checks the content of status.php for a node.

    Same checks as FrontendStatusInfo, with the URL looked up by node name.
    """
    def __init__(self, node, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.node = node
        self.TestStatus = TestStatus
        self.verify = verify

    def run(self):
        global logger
        global expectedResults
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        logger.info(
            f"StatusInfo thread started for node {self.node}"
        )

        url = drv.get_status_url(self.node)
        try:
            logger.info(f"Getting status from: {url}")
            r = get(url, timeout=g_requestTimeout, verify=self.verify)

        except Exception as error:
            logger.error(f"Error getting status info data from {self.node}: {error}")
            g_failedNodes.append(url)
            return

        try:
            j = json.loads(r.text)
            self.TestStatus.assertEqual(
                j["maintenance"], expectedResults[drv.target]["status"]["maintenance"]
            )
            self.TestStatus.assertEqual(
                j["needsDbUpgrade"],
                expectedResults[drv.target]["status"]["needsDbUpgrade"],
            )
            self.TestStatus.assertTrue(
                j["version"] in expectedResults[drv.target]["status"]["version"]
            )
            self.TestStatus.assertTrue(
                j["versionstring"]
                in expectedResults[drv.target]["status"]["versionstring"]
            )
            self.TestStatus.assertEqual(
                j["edition"], expectedResults[drv.target]["status"]["edition"]
            )
            # self.assertEqual(j["productname"], statusResult.productname)
            self.TestStatus.assertEqual(
                j["extendedSupport"],
                expectedResults[drv.target]["status"]["extendedSupport"],
            )
            logger.info(f"Status information tested: {url}")
        except Exception as error:
            g_failedNodes.append(url)
            logger.info(f"No valid JSON reply received for {url}: {error}")
            logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f"Status thread done for node {url}")


class SeamlessAccessInfo(threading.Thread):
    """Thread that checks that the login page of a node uses SeamlessAccess.

    Loads the login page through each frontend server (node1-3, selected
    with the SERVERID cookie) and checks that it references
    seamlessaccess.org. Nodes in loginexceptions are allowed to omit it.
    """
    def __init__(self, node, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.node = node
        self.TestStatus = TestStatus
        self.verify = verify

    def run(self):
        global logger
        global expectedResults
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        logger.info(
            f"SeamlessAccessInfo thread started for node {self.node}"
        )

        url = drv.get_node_login_url(self.node, direct=False)
        fe = None
        try:
            nodebaseurl = drv.get_node_base_url(self.node)
            failed = False
            for fe in range(1, 4):
                logger.info(f"Getting seamless access info from: {url} node {fe}")
                s = requests.Session()
                serverid = f"node{fe}.{nodebaseurl}"
                s.cookies.set("SERVERID", serverid)
                r = get(url, session=s, timeout=g_requestTimeout, verify=self.verify)

                if (
                    "seamlessaccess.org" not in r.text
                    and self.node not in expectedResults[drv.target]["loginexceptions"]
                ):
                    logger.error(
                        f"Error getting seamless access info from: {self.node}. Received text: {r.text}"
                    )
                    g_failedNodes.append(f"{url} - Node {fe}")
                    failed = True
            if failed:
                return
        except Exception as error:
            logger.error(
                f"Error getting seamless access info from {self.node} node {fe}: {error}"
            )
            g_failedNodes.append(url)
            return

        logger.info(f"SeamlessAccessInfo thread done for node {nodebaseurl}")
        return

class OcmInfo(threading.Thread):
    """Thread that checks the Open Cloud Mesh discovery endpoint of a node.

    Fetches /.well-known/ocm through each frontend server (node1-3,
    selected with the SERVERID cookie) and compares enabled, apiVersion,
    version and endPoint with the ocm section of expected.yaml.
    """
    def __init__(self, node, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.node = node
        self.TestStatus = TestStatus
        self.verify = verify

    def run(self):
        global logger
        global expectedResults
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        logger.info(
            f"OcmInfo thread started for node {self.node}"
        )

        fe = None
        serverid = None
        well_known_ocm_url = None
        try:
            nodebaseurl = drv.get_node_base_url(self.node)
            nodeurl = drv.get_node_url(self.node)
            well_known_ocm_url = drv.get_well_known_ocm_url(self.node)
            failed = False
            for fe in range(1, 4):
                logger.info(f"Getting ocm info from: {well_known_ocm_url} through node {fe}")
                s = requests.Session()
                serverid = f"node{fe}.{nodebaseurl}"
                s.cookies.set("SERVERID", serverid)
                r = get(well_known_ocm_url, session=s, timeout=g_requestTimeout, verify=self.verify)
                j = json.loads(r.text)
                # print(json.dumps(j, indent=4))

                if j['enabled'] != expectedResults[drv.target]["ocm"]["enabled"]:
                    failed = True
                    logger.error(f'{j['enabled']} is not {expectedResults[drv.target]["ocm"]["enabled"]}')
                if j['apiVersion'] != expectedResults[drv.target]["ocm"]["apiVersion"]:
                    failed = True
                    logger.error(f'{j['apiVersion']} is not {expectedResults[drv.target]["ocm"]["apiVersion"]}')
                if j['version'] != expectedResults[drv.target]["ocm"]["version"]:
                    failed = True
                    logger.error(f'{j['version']} is not {expectedResults[drv.target]["ocm"]["version"]}')
                if j['endPoint'] != f'{nodeurl}{expectedResults[drv.target]["ocm"]["endPoint"]}':
                    failed = True
                    logger.error(f'{j['endPoint']} is not {nodeurl}{expectedResults[drv.target]["ocm"]["endPoint"]}')

                # print(j['apiVersion'])
                # print(j['version'])
                # print(j['endPoint'])

                # if (
                #     "seamlessaccess.org" not in r.text
                #     and self.node not in expectedResults[drv.target]["loginexceptions"]
                # ):
                #     logger.error(
                #         f"Error getting seamless access info from: {self.node}. Received text: {r.text}"
                #     )
                #     g_failedNodes.append(f"{url} - Node {fe}")
                #     failed = True

                if failed:
                    g_failedNodes.append(f"{well_known_ocm_url} - Node {fe}")
                    return

        except Exception as error:
            logger.error(
                f"Error getting seamless access info from {self.node} node {fe}: {error}"
            )
            g_failedNodes.append(well_known_ocm_url)
            return

        logger.info(f"OcmInfo thread done for node {well_known_ocm_url}")
        return

class FrontentStatus(threading.Thread):
    """Thread that checks that a status URL answers with HTTP 200, without checking the content."""
    def __init__(self, url, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.url = url
        self.verify = verify
        self.TestStatus = TestStatus

    def run(self):
        global logger
        global expectedResults
        global g_failedNodes
        logger.info(f"Status thread started for node {self.url}")

        try:
            r = get(self.url, timeout=g_requestTimeout, verify=self.verify)
            self.TestStatus.assertEqual(r.status_code, 200)
            logger.info(f"Status tested: {self.url}")
        except Exception as error:
            logger.error(f"An error occurred for {self.url}: {error}")
            g_failedNodes.append(self.url)
            logger.info("Status test failed")
            # logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f"Status thread done for node {self.url}")


class TestStatus(unittest.TestCase):
    """Status page and public endpoint checks for all nodes under test."""
    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        global logger
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_frontend_status(self):
        """Check that status.php answers with HTTP 200 on all nodes."""
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        threads = []
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                logger.info(f"TestID: {url}")
                statusThread = FrontentStatus(url, self, verify=drv.verify)
                statusThread.start()
                threads.append(statusThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        if len(g_failedNodes) > 0:
            logger.error(
                f"Frontend status test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:"
            )
            for node in g_failedNodes:
                with self.subTest(mynode=node):
                    logger.error(f"   {node}")
                    self.assertTrue(False)
            g_failedNodes = []

    def test_frontend_statusinfo(self):
        """Check the status.php content of all nodes against expected.yaml."""
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        threads = []
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                logger.info(f"TestID: {url}")
                statusInfoThread = FrontendStatusInfo(url, self, verify=drv.verify)
                statusInfoThread.start()
                threads.append(statusInfoThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        if len(g_failedNodes) > 0:
            logger.error(
                f"FrontendStatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:"
            )
            for node in g_failedNodes:
                with self.subTest(mynode=node):
                    logger.error(f"   {node}")
                    self.assertTrue(False)
            g_failedNodes = []

    # def test_frontend_statusinfo_http(self):
    #     global g_failedNodes
    #     g_failedNodes = []
    #     drv = sunetnextcloud.TestTarget()

    #     for url in drv.get_allnode_status_urls():
    #         with self.subTest(myurl=url):
    #             logger.info(f'TestID: {url}')
    #             statusInfoThread = FrontendStatusInfo(url, self, verify=drv.verify, useHttps=False)
    #             statusInfoThread.start()

    #     while(testThreadsRunning > 0):
    #         time.sleep(1)

    #     if len(g_failedNodes) > 0:
    #         logger.error(f'FrontendStatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
    #         for node in g_failedNodes:
    #             logger.error(f'   {node}')
    #         g_failedNodes = []
    #         self.assertTrue(False)

    def test_node_statusinfo(self):
        """Check status.php on each frontend server (node1-3) of the redundant nodes.

        Only nodes listed in redundantnodes in expected.yaml are tested.
        """
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        threads = []
        for node in expectedResults["global"]["redundantnodes"]:
            if node in drv.allnodes:
                with self.subTest(myurl=node):
                    logger.info(f"TestID: {node}")
                    statusInfoThread = NodeStatusInfo(node, self, verify=drv.verify)
                    statusInfoThread.start()
                    threads.append(statusInfoThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        if len(g_failedNodes) > 0:
            logger.error(
                f"NodeStatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:"
            )
            for node in g_failedNodes:
                with self.subTest(mynode=node):
                    logger.error(f"   {node}")
                    self.assertTrue(False)
            g_failedNodes = []

    def test_statusinfo(self):
        """Check the status.php content of all tested nodes listed in allnodes in expected.yaml."""
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        threads = []
        for node in expectedResults["global"]["allnodes"]:
            if node in drv.allnodes:
                with self.subTest(myurl=node):
                    logger.info(f"TestID: {node}")
                    statusInfoThread = StatusInfo(node, self, verify=drv.verify)
                    statusInfoThread.start()
                    threads.append(statusInfoThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        if len(g_failedNodes) > 0:
            logger.error(
                f"NodeStatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:"
            )
            for node in g_failedNodes:
                with self.subTest(mynode=node):
                    logger.error(f"   {node}")
                    self.assertTrue(False)
            g_failedNodes = []

    def test_seamlessaccessinfo(self):
        """Check that the login page on every frontend server uses SeamlessAccess.

        Skipped for localhost and for nodes in loginexceptions.
        """
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()

        if drv.target == "localhost":
            logger.warning("We are not testing SeamlessAccess for localhost")
            return

        threads = []
        for node in expectedResults["global"]["allnodes"]:
            if node in drv.allnodes and node not in expectedResults[drv.target]['loginexceptions']:
                with self.subTest(myurl=node):
                    logger.info(f"TestID: {node}")
                    saInfoThread = SeamlessAccessInfo(node, self)
                    saInfoThread.start()
                    threads.append(saInfoThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        if len(g_failedNodes) > 0:
            logger.error(
                f"SeamlessAccessInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:"
            )
            for node in g_failedNodes:
                with self.subTest(mynode=node):
                    logger.error(f"   {node}")
                    self.assertTrue(False)
            g_failedNodes = []

    def test_ocminfo(self):
        """Check /.well-known/ocm on every frontend server against expected.yaml.

        Nodes in loginexceptions are skipped.
        """
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()

        threads = []
        for node in expectedResults["global"]["allnodes"]:
            if node in drv.allnodes and node not in expectedResults[drv.target]['loginexceptions']:
                with self.subTest(myurl=node):
                    logger.info(f"TestID: {node}")
                    ocmInfoThread = OcmInfo(node, self)
                    ocmInfoThread.start()
                    threads.append(ocmInfoThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        if len(g_failedNodes) > 0:
            logger.error(
                f"OCM test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:"
            )
            for node in g_failedNodes:
                with self.subTest(mynode=node):
                    logger.error(f"   {node}")
                    self.assertTrue(False)
            g_failedNodes = []

    def test_saml_metadata(self):
        """Check the SAML SP metadata of each node.

        The entity ID must match the node, and the MD5 of the certificate must
        match cert_md5 in expected.yaml. Skipped for localhost, custom and nodes
        in loginexceptions. Nodes whose metadata cannot be fetched or parsed
        are logged as errors and skipped.
        """
        global logger
        global expectedResults
        logger.info(f"TestID: {self._testMethodName}")
        drv = sunetnextcloud.TestTarget()

        if drv.target == "localhost" or drv.target == "custom":
            logger.warning(f"We are not testing Saml metadata for {drv.target} (yet)")
            return

        for node in drv.allnodes:
            with self.subTest(mynode=node):
                if node in expectedResults[drv.target]["loginexceptions"]:
                    logger.info(f"Not testing metadata for {node}")
                else:
                    url = drv.get_metadata_url(node)
                    expectedEntityId = ""
                    certMd5 = ""
                    logger.info(f"Verify metadata for {url}")
                    try:
                        r = get(url, timeout=g_requestTimeout)
                    except Exception as error:
                        logger.error(f"Error getting {url}: {error}")
                        continue

                    try:
                        metadataXml = fromstring(r.text)
                        items = metadataXml.items()
                        for item in items:
                            name = item[0]
                            if name == "entityID":
                                expectedEntityId = item[1]
                                logger.info("entityID checked")

                        metadataDict = xmltodict.parse(r.text)
                        jsonString = json.dumps(metadataDict)
                        j = json.loads(jsonString)
                        certString = j["md:EntityDescriptor"]["md:SPSSODescriptor"][
                            "md:KeyDescriptor"
                        ]["ds:KeyInfo"]["ds:X509Data"]["ds:X509Certificate"]
                        certMd5 = hashlib.md5(certString.encode("utf-8")).hexdigest()
                    except Exception as error:
                        logger.error(f"Metadata is not valid XML for {node}: {error}")
                        logger.error(f"Metadata: {r.text}")
                        continue

                    self.assertEqual(expectedEntityId, drv.get_node_entity_id(node))
                    self.assertEqual(certMd5, expectedResults[drv.target]["cert_md5"])
        logger.info("Saml metadata test done")

    def test_collabora_nodes(self):
        """Check that each Collabora server returns the expected status text.

        The number of servers is taken from collabora.nodes in expected.yaml.
        Skipped for localhost.
        """
        global logger
        global expectedResults
        logger.info(f"TestID: {self._testMethodName}")
        drv = sunetnextcloud.TestTarget()

        if drv.target == "localhost":
            logger.warning("We are not testing Collabora locally (yet)")
            return

        numCollaboraNodes = expectedResults[drv.target]["collabora"]["nodes"]
        logger.info(f"Collabora nodes: {numCollaboraNodes}")
        for i in range(1, numCollaboraNodes + 1):
            with self.subTest(mynode=i):
                url = drv.get_collabora_node_url(i)
                logger.info(f"Testing Collabora Node: {url}")
                r = get(url, timeout=g_requestTimeout)
                logger.info(f"Status: {r.text}")
                self.assertEqual(
                    expectedResults[drv.target]["collabora"]["status"], r.text
                )


# if __name__ == '__main__':
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
