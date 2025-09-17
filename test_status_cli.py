""" Command line unit tests for Sunet Drive, testing status pages and information
Author: Richard Freitag <freitag@sunet.se>
Simple test for retrieving all status.php pages from Sunet Drive nodes and comparing the output to the expected result.
"""

import unittest
import requests
import json
import logging
import hashlib
from xml.etree.ElementTree import fromstring
import xmltodict
import threading
import time
import os

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

testThreadsRunning = 0
g_failedNodes = []
g_requestTimeout=30
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class FrontendStatusInfo(threading.Thread):
    def __init__(self, url, TestStatus, verify=True, useHttps=True):
        threading.Thread.__init__(self)
        if useHttps:
            self.url = url
        else:
            # self.url = url.replace('https://', 'http://')
            self.url = url.replace('https://', 'http://')
        self.TestStatus = TestStatus
        self.verify = verify
        self.useHttps = useHttps

    def run(self):
        global testThreadsRunning
        global logger
        global expectedResults
        global g_failedNodes
        testThreadsRunning += 1
        drv = sunetnextcloud.TestTarget()
        logger.info(f'FrontendStatusInfo thread {testThreadsRunning} started for node {self.url}')

        try:
            r =requests.get(self.url, timeout=g_requestTimeout, verify=self.verify)
        except Exception as error:
            logger.error(f'Error getting frontend status data from {self.url}: {error}')
            g_failedNodes.append(self.url)
            testThreadsRunning -= 1
            return
        
        try:
            j = json.loads(r.text)
            self.TestStatus.assertEqual(j["maintenance"], expectedResults[drv.target]['status']['maintenance'])
            self.TestStatus.assertEqual(j["needsDbUpgrade"], expectedResults[drv.target]['status']['needsDbUpgrade'])
            self.TestStatus.assertEqual(j["version"], expectedResults[drv.target]['status']['version'])
            self.TestStatus.assertEqual(j["versionstring"], expectedResults[drv.target]['status']['versionstring'])
            self.TestStatus.assertEqual(j["edition"], expectedResults[drv.target]['status']['edition'])
            # self.assertEqual(j["productname"], statusResult.productname)
            self.TestStatus.assertEqual(j["extendedSupport"], expectedResults[drv.target]['status']['extendedSupport'])
            logger.info(f'Status information tested: {self.url}')
        except Exception as error:
            g_failedNodes.append(self.url)
            logger.info(f'No valid JSON reply received for {self.url}: {error}')
            testThreadsRunning -= 1
            logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f'Status thread done for node {self.url}')
        testThreadsRunning -= 1
        logger.info(f'FrontendStatusInfo threads remaining: {testThreadsRunning}')

class NodeStatusInfo(threading.Thread):
    def __init__(self, node, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.node = node
        self.TestStatus = TestStatus
        self.verify = verify

    def run(self):
        global testThreadsRunning
        global logger
        global expectedResults
        global g_failedNodes
        testThreadsRunning += 1
        drv = sunetnextcloud.TestTarget()
        logger.info(f'NodeStatusInfo thread {testThreadsRunning} started for node {self.node}')

        x = range(1,4)
        for i in x:
            url = drv.get_node_status_url(self.node, i)
            try:
                logger.info(f'Getting status from: {url}')
                r =requests.get(url, timeout=g_requestTimeout, verify=False)
            except Exception as error:
                logger.error(f'Error getting node status data from {self.node}: {error}')
                g_failedNodes.append(url)
                testThreadsRunning -= 1
                return
            
            try:
                j = json.loads(r.text)
                self.TestStatus.assertEqual(j["maintenance"], expectedResults[drv.target]['status']['maintenance'])
                self.TestStatus.assertEqual(j["needsDbUpgrade"], expectedResults[drv.target]['status']['needsDbUpgrade'])
                self.TestStatus.assertEqual(j["version"], expectedResults[drv.target]['status']['version'])
                self.TestStatus.assertEqual(j["versionstring"], expectedResults[drv.target]['status']['versionstring'])
                self.TestStatus.assertEqual(j["edition"], expectedResults[drv.target]['status']['edition'])
                # self.assertEqual(j["productname"], statusResult.productname)
                self.TestStatus.assertEqual(j["extendedSupport"], expectedResults[drv.target]['status']['extendedSupport'])
                logger.info(f'Status information tested: {url}')
            except Exception as error:
                g_failedNodes.append(url)
                logger.info(f'No valid JSON reply received for {url}: {error}')
                testThreadsRunning -= 1
                logger.info(r.text)
                self.TestStatus.assertTrue(False)
                return

        logger.info(f'Status thread done for node {url}')
        testThreadsRunning -= 1
        logger.info(f'NodeStatusInfo threads remaining: {testThreadsRunning}')

class StatusInfo(threading.Thread):
    def __init__(self, node, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.node = node
        self.TestStatus = TestStatus
        self.verify = verify

    def run(self):
        global testThreadsRunning
        global logger
        global expectedResults
        global g_failedNodes
        testThreadsRunning += 1
        drv = sunetnextcloud.TestTarget()
        logger.info(f'StatusInfo thread {testThreadsRunning} started for node {self.node}')

        url = drv.get_status_url(self.node)
        try:
            logger.info(f'Getting status from: {url}')
            r =requests.get(url, timeout=g_requestTimeout, verify=self.verify)
        except Exception as error:
            logger.error(f'Error getting status info data from {self.node}: {error}')
            g_failedNodes.append(url)
            testThreadsRunning -= 1
            return
        
        try:
            j = json.loads(r.text)
            self.TestStatus.assertEqual(j["maintenance"], expectedResults[drv.target]['status']['maintenance'])
            self.TestStatus.assertEqual(j["needsDbUpgrade"], expectedResults[drv.target]['status']['needsDbUpgrade'])
            self.TestStatus.assertEqual(j["version"], expectedResults[drv.target]['status']['version'])
            self.TestStatus.assertEqual(j["versionstring"], expectedResults[drv.target]['status']['versionstring'])
            self.TestStatus.assertEqual(j["edition"], expectedResults[drv.target]['status']['edition'])
            # self.assertEqual(j["productname"], statusResult.productname)
            self.TestStatus.assertEqual(j["extendedSupport"], expectedResults[drv.target]['status']['extendedSupport'])
            logger.info(f'Status information tested: {url}')
        except Exception as error:
            g_failedNodes.append(url)
            logger.info(f'No valid JSON reply received for {url}: {error}')
            testThreadsRunning -= 1
            logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f'Status thread done for node {url}')
        testThreadsRunning -= 1
        logger.info(f'NodeStatusInfo threads remaining: {testThreadsRunning}')

class SeamlessAccessInfo(threading.Thread):
    def __init__(self, node, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.node = node
        self.TestStatus = TestStatus
        self.verify = verify

    def run(self):
        global testThreadsRunning
        global logger
        global expectedResults
        global g_failedNodes
        testThreadsRunning += 1
        drv = sunetnextcloud.TestTarget()
        logger.info(f'SeamlessAccessInfo thread {testThreadsRunning} started for node {self.node}')

        url = drv.get_node_login_url(self.node, direct=False)
        fe = None
        try:
            nodebaseurl = drv.get_node_base_url(self.node)
            failed = False
            for fe in range(1,4):
                logger.info(f'Getting node login url from: {url} node {fe}')
                s = requests.Session()
                serverid = f'node{fe}.{nodebaseurl}'
                s.cookies.set('SERVERID', serverid)
                r =s.get(url, timeout=g_requestTimeout, verify=self.verify)

                if "seamlessaccess.org" not in r.text and self.node not in expectedResults[drv.target]['loginexceptions']:
                    logger.error(f'Error getting seamless access info from: {self.node}. Received text: {r.text}')
                    g_failedNodes.append(f'{url} - Node {fe}')
                    failed = True
            if failed:
                testThreadsRunning-=1
                return

        except Exception as error:
            logger.error(f'Error getting seamless access info from {self.node} node {fe}: {error}')
            g_failedNodes.append(url)
            testThreadsRunning -= 1
            return
        
        logger.info(f'SeamlessAccessInfo thread done for node {url}')
        testThreadsRunning -= 1
        logger.info(f'SeamlessAccessInfo threads remaining: {testThreadsRunning}')

# Test frontend status for code 200, no content check
class FrontentStatus(threading.Thread):
    def __init__(self, url, TestStatus, verify=True):
        threading.Thread.__init__(self)
        self.url = url
        self.verify = verify
        self.TestStatus = TestStatus

    def run(self):
        global testThreadsRunning
        global logger
        global expectedResults
        global g_failedNodes
        testThreadsRunning += 1
        logger.info(f'Status thread {testThreadsRunning} started for node {self.url}')

        try:
            r=requests.get(self.url, timeout=g_requestTimeout, verify=self.verify)
            self.TestStatus.assertEqual(r.status_code, 200)
            logger.info(f'Status tested: {self.url}')
        except Exception as error:
            logger.error(f'An error occurred for {self.url}: {error}')
            g_failedNodes.append(self.url)
            logger.info('Status test failed')
            testThreadsRunning -= 1
            # logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f'Status thread done for node {self.url}')
        testThreadsRunning -= 1

class TestStatus(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_frontend_status(self):
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                logger.info(f'TestID: {url}')
                statusThread = FrontentStatus(url, self, verify=drv.verify)
                statusThread.start()

        while(testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'Frontend status test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            g_failedNodes = []
            self.assertTrue(False)

    def test_frontend_statusinfo(self):
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                logger.info(f'TestID: {url}')
                statusInfoThread = FrontendStatusInfo(url, self, verify=drv.verify)
                statusInfoThread.start()

        while(testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'FrontendStatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            g_failedNodes = []
            self.assertTrue(False)

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

# Test status infor content for all individual loadbalanced nodes
    def test_node_statusinfo(self):
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        for node in expectedResults['global']['redundantnodes']:
            if node in drv.allnodes:
                with self.subTest(myurl=node):
                    logger.info(f'TestID: {node}')
                    statusInfoThread = NodeStatusInfo(node, self, verify=drv.verify)
                    statusInfoThread.start()

        while(testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'NodeStatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            g_failedNodes = []
            self.assertTrue(False)

# Test status.php for all nodes
    def test_statusinfo(self):
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()
        for node in expectedResults['global']['allnodes']:
            if node in drv.allnodes:
                with self.subTest(myurl=node):
                    logger.info(f'TestID: {node}')
                    statusInfoThread = StatusInfo(node, self, verify=drv.verify)
                    statusInfoThread.start()

        while(testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'NodeStatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            g_failedNodes = []
            self.assertTrue(False)

    def test_seamlessaccessinfo(self):
        global g_failedNodes
        drv = sunetnextcloud.TestTarget()

        if drv.target == 'localhost':
            logger.warning('We are not testing SeamlessAccess for localhost')
            return

        for node in expectedResults['global']['allnodes']:
            if node in drv.allnodes:
                with self.subTest(myurl=node):
                    logger.info(f'TestID: {node}')
                    saInfoThread = SeamlessAccessInfo(node, self)
                    saInfoThread.start()

        while(testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'SeamlessAccessInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            g_failedNodes = []
            self.assertTrue(False)

    def test_saml_metadata(self):
        global logger
        global expectedResults
        logger.info(f'TestID: {self._testMethodName}')
        drv = sunetnextcloud.TestTarget()

        if drv.target == 'localhost':
            logger.warning('We are not testing Saml metadata locally (yet)')
            return

        for node in drv.allnodes:           
            with self.subTest(mynode=node):
                if node in expectedResults[drv.target]['loginexceptions']:
                    logger.info(f'Not testing metadata for {node}')
                else:
                    url = drv.get_metadata_url(node)
                    expectedEntityId = ''
                    certMd5 = ''
                    logger.info(f'Verify metadata for {url}')
                    r = requests.get(url, timeout=g_requestTimeout)

                    try:
                        metadataXml = fromstring(r.text)
                        items = metadataXml.items()
                        for item in items:
                            name = item[0]
                            if name == 'entityID':
                                expectedEntityId = item[1]
                                logger.info("entityID checked")

                        metadataDict = xmltodict.parse(r.text)
                        jsonString = json.dumps(metadataDict)
                        j = json.loads(jsonString)
                        certString = j["md:EntityDescriptor"]["md:SPSSODescriptor"]["md:KeyDescriptor"]["ds:KeyInfo"]["ds:X509Data"]["ds:X509Certificate"]
                        certMd5 = hashlib.md5(certString.encode('utf-8')).hexdigest()
                    except Exception as error:
                        logger.error(f'Metadata is not valid XML for {node}: {error}')
                        logger.error(f'Metadata: {r.text}')

                    self.assertEqual(expectedEntityId, drv.get_node_entity_id(node))
                    self.assertEqual(certMd5, expectedResults[drv.target]['cert_md5'])
        logger.info('Saml metadata test done')

    def test_collabora_nodes(self):
        global logger
        global expectedResults
        logger.info(f'TestID: {self._testMethodName}')
        drv = sunetnextcloud.TestTarget()

        if drv.target == 'localhost':
            logger.warning('We are not testing Collabora locally (yet)')
            return

        numCollaboraNodes = expectedResults[drv.target]['collabora']['nodes']
        logger.info(f'Collabora nodes: {numCollaboraNodes}')
        for i in range(1,numCollaboraNodes+1):
            with self.subTest(mynode=i):
                url = drv.get_collabora_node_url(i)
                logger.info(f'Testing Collabora Node: {url}')
                r = requests.get(url, timeout=g_requestTimeout)
                logger.info(f'Status: {r.text}')
                self.assertEqual(expectedResults[drv.target]['collabora']['status'], r.text)

if __name__ == '__main__':
    drv.run_tests(os.path.basename(__file__))
