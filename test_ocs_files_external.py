"""
Test OCS Files External endpoints
Author: Richard Freitag <freitag@sunet.se>
"""

import sunetnextcloud

import unittest
import logging
import xmlrunner
import HtmlTestRunner

import threading
import time
import requests
import json

drv = sunetnextcloud.TestTarget()
ocsheaders = drv.ocsheaders
expectedResults = drv.expectedResults

g_testPassed = {}
g_requestTimeout = 10

logger = logging.getLogger("TestLogger")
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

class ExternalMounts(threading.Thread):
    def __init__(self, name, TestOcsFilesExternal, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsFilesExternal = TestOcsFilesExternal
        self.verify = verify

    def run(self):
        global logger
        global expectedResults
        global g_testPassed
        logger.info(f"External mounts thread started for node {self.name}")
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f"Setting passed for {fullnode} to {g_testPassed.get(fullnode)}")

        rawurl = None
        try:
            rawurl = drv.get_ocs_external_mounts_url(fullnode)
            logger.info(f"{self.TestOcsFilesExternal._testMethodName} {rawurl}")
            nodeuser = drv.get_ocsuser(fullnode)
            logger.info(f"Getting credentials for {nodeuser} on {fullnode}")
            nodepwd = drv.get_ocsuserapppassword(fullnode)
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

class TestOcsFilesExternal(unittest.TestCase):
    def test_logger(self):
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_external_mounts(self):
        drv = sunetnextcloud.TestTarget()
        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                externalMountsThread = ExternalMounts(fullnode, self, verify=drv.verify)
                externalMountsThread.start()
                threads.append(externalMountsThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
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
