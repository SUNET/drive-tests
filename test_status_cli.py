""" Command line unit tests for Sunet Drive, testing status pages and information
Author: Richard Freitag <freitag@sunet.se>
Simple test for retrieving all status.php pages from Sunet Drive nodes and comparing the output to the expected result.
"""

import unittest
import requests
import json
import logging
import hashlib
from xml.etree.ElementTree import XML, fromstring
import xmltodict
import yaml
import threading
import time
import xmlrunner

import sunetnextcloud
import os

expectedResultsFile = 'expected.yaml'
testThreadsRunning = 0
g_failedNodes = []
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

class StatusInfo(threading.Thread):
    def __init__(self, url, TestStatus):
        threading.Thread.__init__(self)
        self.url = url
        self.TestStatus = TestStatus

    def run(self):
        global testThreadsRunning
        global logger
        global expectedResults
        global g_failedNodes
        testThreadsRunning += 1
        drv = sunetnextcloud.TestTarget()
        logger.info(f'StatusInfo thread {testThreadsRunning} started for node {self.url}')

        try:
            r =requests.get(self.url)
        except:
            logger.info.error(f'Error getting data from {self.url}')
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
        except:
            g_failedNodes.append(self.url)
            logger.info(f'No valid JSON reply received for {self.url}')
            testThreadsRunning -= 1
            logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f'Status thread done for node {self.url}')
        testThreadsRunning -= 1
        logger.info(f'StatusInfo threads remaining: {testThreadsRunning}')

class Status(threading.Thread):
    def __init__(self, url, TestStatus):
        threading.Thread.__init__(self)
        self.url = url
        self.TestStatus = TestStatus

    def run(self):
        global testThreadsRunning
        global logger
        global expectedResults
        testThreadsRunning += 1
        logger.info(f'Status thread {testThreadsRunning} started for node {self.url}')

        try:
            r=requests.get(self.url)
            self.TestStatus.assertEqual(r.status_code, 200)
            logger.info(f'Status tested: {self.url}')
        except:
            g_failedNodes.append(self.url)
            logger.info('Status test failed')
            testThreadsRunning -= 1
            logger.info(r.text)
            self.TestStatus.assertTrue(False)
            return

        logger.info(f'Status thread done for node {self.url}')
        testThreadsRunning -= 1

class TestStatus(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_status_gss(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        if drv.testgss == False:
            logger.info('Not testing gss')
            return

        url = drv.get_gss_url()
        print(self._testMethodName, url)
        r=requests.get(url)
        self.assertEqual(r.status_code, 200)
        logger.info(f'GSS Status tested')

    def test_statusinfo_gss(self):
        global logger
        global expectedResults
        logger.info(f'TestID: {self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        if drv.testgss == False:
            logger.info('Not testing gss')
            return

        url=drv.get_gss_url() + "/status.php"
        print(self._testMethodName, url)
        r =requests.get(url)
        j = json.loads(r.text)

        self.assertEqual(j["maintenance"], expectedResults[drv.target]['status_gss']['maintenance']) 
        self.assertEqual(j["needsDbUpgrade"], expectedResults[drv.target]['status_gss']['needsDbUpgrade'])
        self.assertEqual(j["version"], expectedResults[drv.target]['status_gss']['version'])
        self.assertEqual(j["versionstring"], expectedResults[drv.target]['status_gss']['versionstring'])
        self.assertEqual(j["edition"], expectedResults[drv.target]['status_gss']['edition'])
        self.assertEqual(j["extendedSupport"], expectedResults[drv.target]['status_gss']['extendedSupport'])
        logger.info(f'GSS Status information tested')

    def test_status(self):
        drv = sunetnextcloud.TestTarget()
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                logger.info(f'TestID: {url}')
                statusThread = Status(url, self)
                statusThread.start()

        while(testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'Status test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            self.assertTrue(False)
        

    def test_statusinfo(self):
        drv = sunetnextcloud.TestTarget()
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                logger.info(f'TestID: {url}')
                statusInfoThread = StatusInfo(url, self)
                statusInfoThread.start()

        while(testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'StatusInfo test failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            self.assertTrue(False)

    def test_metadata_gss(self):
        global logger
        global expectedResults
        logger.info(f'TestID: {self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        if drv.testgss == False:
            logger.info('Not testing gss')
            return

        url = drv.get_gss_metadata_url()
        expectedEntityId = ''
        certMd5 = ''
        logger.info(f'Verify metadata for {url}')
        r = requests.get(url)

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
        except:
            logger.error(f'Metadata is not valid XML')

        self.assertEqual(expectedEntityId, drv.get_gss_entity_id())
        self.assertEqual(certMd5, expectedResults[drv.target]['cert_md5'])
        logger.info(f'GSS metadata test done')

    def test_collabora_nodes(self):
        global logger
        global expectedResults
        logger.info(f'TestID: {self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        numCollaboraNodes = expectedResults[drv.target]['collabora']['nodes']
        logger.info(f'Collabora nodes: {numCollaboraNodes}')
        for i in range(1,numCollaboraNodes+1):
            url = drv.get_collabora_node_url(i)
            logger.info(f'Testing Collabora Node: {url}')
            r = requests.get(url)
            logger.info(f'Status: {r.text}')
            self.assertEqual(expectedResults[drv.target]['collabora']['status'], r.text)

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
