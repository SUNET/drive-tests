""" Command line unit tests for the Sunet Drive Collabora servers
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import HtmlTestRunner
import xmlrunner
import requests
import json
import logging
import hashlib
import xmltodict
import yaml
import threading
import time

import sunetnextcloud
import os

g_requestTimeout=10
expectedResultsFile = 'expected.yaml'
testThreadRunning = False
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

drv = sunetnextcloud.TestTarget()

class TestCollabora(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_collabora_capabilities(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        drv = sunetnextcloud.TestTarget()

        numCollaboraNodes = expectedResults[drv.target]['collabora']['nodes']
        logger.info(f'Collabora nodes: {numCollaboraNodes}')
        for i in range(1,numCollaboraNodes+1):
            url=drv.get_collabora_capabilities_url(i)
            logger.info(f'Testing collabora server url: {url}')

            r =requests.get(url, timeout=g_requestTimeout)
            j = json.loads(r.text)

            self.assertEqual(j['hasMobileSupport'], expectedResults[drv.target]['collabora']['capabilities']['hasMobileSupport']) 
            self.assertEqual(j['hasProxyPrefix'], expectedResults[drv.target]['collabora']['capabilities']['hasProxyPrefix'])
            self.assertEqual(j['hasTemplateSaveAs'], expectedResults[drv.target]['collabora']['capabilities']['hasTemplateSaveAs'])
            self.assertEqual(j['hasTemplateSource'], expectedResults[drv.target]['collabora']['capabilities']['hasTemplateSource'])
            self.assertEqual(j['hasZoteroSupport'], expectedResults[drv.target]['collabora']['capabilities']['hasZoteroSupport'])
            self.assertEqual(j['productName'], expectedResults[drv.target]['collabora']['capabilities']['productName'])
            self.assertEqual(j['productVersion'], expectedResults[drv.target]['collabora']['capabilities']['productVersion'])
            self.assertEqual(j['productVersionHash'], expectedResults[drv.target]['collabora']['capabilities']['productVersionHash'])

        logger.info(f'Collabora capabilities tested')

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-acceptance", add_timestamp=False))
