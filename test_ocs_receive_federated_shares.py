"""Testing OCS functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import json
import logging
import tempfile
import threading
import time
import unittest

import HtmlTestRunner
import requests
import xmlrunner
from webdav3.client import Client

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
ocsheaders = drv.ocsheaders
expectedResults = drv.expectedResults

g_testPassed = {}
g_testThreadsRunning = 0
g_requestTimeout = 10
g_webdav_timeout = 30
g_sharedTestFolder = "SharedFolder"
g_filename = "federated_share.txt"

logger = logging.getLogger("TestLogger")
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


class TestOcsFederatedShares(unittest.TestCase):
    def test_logger(self):
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_accept_federated_shares(self):
        drv = sunetnextcloud.TestTarget()
        # for fullnode in drv.nodestotest:
        for fullnode in ["bth"]:
            with self.subTest(mynode=fullnode):
                logger.info(f"Accept shares for {fullnode}")

                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserapppassword(fullnode)
                url = drv.get_pending_shares_url(fullnode)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)
                r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout)
                j = json.loads(r.text)
                # logger.info(json.dumps(j, indent=4, sort_keys=True))

                if len(j["ocs"]["data"]) == 0:
                    logger.info(f"No pending shares to accept for {fullnode}")
                    continue  # with next node

                for share in j["ocs"]["data"]:
                    filename = share["name"]
                    logger.info(f"Accepting share {filename}")
                    url = drv.get_pending_shares_id_url(fullnode, share["id"])
                    logger.info(f"Accept share: {share['id']} - {url}")
                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)
                    r = requests.post(url, headers=ocsheaders)
                    logger.info(f"Pending share accepted: {filename}")

    def test_list_federated_shares(self):
        drv = sunetnextcloud.TestTarget()
        # for fullnode in drv.nodestotest:
        for fullnode in ["bth"]:
            with self.subTest(mynode=fullnode):
                logger.info(f"List federated shares for {fullnode}")

                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserapppassword(fullnode)
                url = drv.get_remote_shares_url(fullnode)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)
                r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout)
                j = json.loads(r.text)
                # logger.info(json.dumps(j, indent=4, sort_keys=True))

                url = drv.get_webdav_url(fullnode, nodeuser)
                logger.info(f"URL: {url}")
                options = {
                    "webdav_hostname": url,
                    "webdav_login": nodeuser,
                    "webdav_password": nodepwd,
                    "webdav_timeout": g_webdav_timeout,
                }
                client = Client(options)
                client.verify = drv.verify

                for share in j["ocs"]["data"]:
                    try:
                        filename = share["name"]
                        logger.info(f"List share {filename}")
                        logger.info(client.list(filename))
                    except Exception as error:
                        logger.error(f"Unable to list share for {fullnode}: {error}")


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
                report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-ocs-federated-shares",
                add_timestamp=False,
            )
        )
