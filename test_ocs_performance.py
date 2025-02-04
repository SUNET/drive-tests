""" Testing OCS functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import HtmlTestRunner
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import time
import yaml
import logging
import threading
import xmlrunner
from datetime import datetime

import sunetnextcloud

ocsheaders = { "OCS-APIRequest" : "true" } 

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

g_testPassed = {}
g_testThreadsRunning = 0
g_requestTimeout = 10

logger = logging.getLogger('TestLogger')
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class NodeOcsUserPerformance(threading.Thread):
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        g_testThreadsRunning += 1
        logger.info(f'NodeOcsUserPerformance thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

        try:
            url = drv.get_status_url(fullnode)
            s = requests.Session()
            s.headers.update(ocsheaders)
            s.get(url)

            nodebaseurl = drv.get_node_base_url(fullnode)
            url = drv.get_add_user_url(fullnode)
            print(url)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)      

            for fe in range(1,4):
                serverid = f'node{fe}.{nodebaseurl}'
                s.cookies.set('SERVERID', serverid)
                startTime = datetime.now()
                r = s.get(url, headers=ocsheaders)
                totalTime = (datetime.now() - startTime).total_seconds()
                logger.info(f'Request to {serverid} took {totalTime:.1f}s')
        except Exception as error:
            logger.error(f'{error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'NodeOcsUserPerformance thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class TestOcsPerformance(unittest.TestCase):
    def test_logger(self):
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_nodeusers(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                nodeUsersThread = NodeOcsUserPerformance(fullnode, self, verify=drv.verify)
                nodeUsersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])


if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name="nextcloud-acceptance", add_timestamp=False))
