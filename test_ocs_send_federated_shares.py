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

# nodestotest = ["sunet", "su", "extern", "vr"]
nodestotest = ["sunet"]

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults
ocsheaders = drv.ocsheaders

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


class OcsMakeFederatedShare(threading.Thread):
    def __init__(self, name, TestOcsFederatedShares, basicAuth, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsFederatedShares = TestOcsFederatedShares
        self.basicAuth = basicAuth
        self.verify = verify

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f"{self.name} - OcsMakeFederatedShare thread started")
        drv = sunetnextcloud.TestTarget()

        nodeuser = drv.get_seleniumuser(fullnode)
        if self.basicAuth:
            logger.info(f"{self.name} - Testing with basic authentication")
            nodepwd = drv.get_seleniumuserpassword(fullnode)
        else:
            logger.info(f"{self.name} - Testing with application password")
            nodepwd = drv.get_seleniumuserapppassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f"{self.name} - URL: {url}")
        options = {
            "webdav_hostname": url,
            "webdav_login": nodeuser,
            "webdav_password": nodepwd,
            "webdav_timeout": g_webdav_timeout,
        }

        client = Client(options)
        client.verify = drv.verify

        try:
            logger.info(f"{self.name} - Before mkdir: {client.list()}")
            client.mkdir(g_sharedTestFolder)
            logger.info(f"{self.name} - After mkdir: {client.list()}")
        except Exception as error:
            logger.error(
                f"{self.name} - Error making folder {g_sharedTestFolder} on {self.name}: {error}"
            )
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        filename = fullnode + "_" + g_filename

        try:
            tmpfilename = tempfile.gettempdir() + "/" + fullnode + "_" + g_filename
        except Exception as error:
            logger.error(f"{self.name} - Getting temp dir for {fullnode}: {error}")
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        with open(tmpfilename, "w") as f:
            f.write(f"{self.name} - Federated share for {fullnode}")
            f.close()

        try:
            client = Client(options)
            client.verify = drv.verify
            client.mkdir(g_sharedTestFolder)
            targetfile = f"{g_sharedTestFolder}/{filename}"
            # deleteoriginal=False # TODO: Implement delete original file
        except Exception as error:
            logger.error(
                f"{self.name} - Error preparing webdav client for {fullnode}: {error}"
            )
            g_testThreadsRunning -= 1
            return

        try:
            logger.info(f"{self.name} - Uploading {tmpfilename} to {targetfile}")
            client.upload_sync(remote_path=targetfile, local_path=tmpfilename)
        except Exception as error:
            logger.error(f"{self.name} - Error uploading file to {fullnode}: {error}")
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f"{self.name} - Get all shares for {fullnode}")
        clean_url = drv.get_share_url(fullnode)
        url = clean_url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        try:
            r = requests.get(
                url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify
            )
            j = json.loads(r.text)
            # logger.info(f'Found shares: {json.dumps(j, indent=4, sort_keys=True)}')

            for share in j["ocs"]["data"]:
                clean_url = drv.get_share_id_url(fullnode, share["id"])
                logger.info(f"{self.name} - Delete share: {share['id']} - {clean_url}")
                url = clean_url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)
                r = requests.delete(url, headers=ocsheaders, verify=self.verify)
                logger.info(f"{self.name} - Share deleted: {r.text}")
        except Exception as error:
            logger.error(f"{self.name} - Error getting {clean_url}: {error}")
            if r is not None:
                logger.error(r.text)
            g_testThreadsRunning -= 1
            return

        # for shareNode in drv.allnodes:
        for shareNode in ["bth"]:
            if shareNode == fullnode:
                logger.info(f"{self.name} - Do not share with self")
                continue  # with next node

            if drv.target == "test":
                delimiter = "test."
            else:
                delimiter = ""

            shareWith = f"_selenium_{shareNode}@{shareNode}.drive.{delimiter}sunet.se"
            # shareWith = '_selenium_bth@bth.drive.test.sunet.se'
            logger.info(f"Share with {shareWith}")

            url = drv.get_share_url(fullnode)
            logger.info(f"{self.name} - Share url: {url}")
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
            session = requests.Session()
            payload = {
                "path": f"{targetfile}",
                "shareWith": shareWith,
                "shareType": 6,
                "note": "Testautomation",
            }
            logger.info(f"{self.name} - Payload: {payload}")

            try:
                # logger.info(f'Share to {url}')
                r = session.post(
                    url, headers=ocsheaders, data=payload, verify=self.verify
                )

                j = json.loads(r.text)
                logger.info(
                    f"{self.name} - Result of sharing to {clean_url}: {j} - WebDAV List: {client.list(targetfile)} - Payload: {payload}"
                )
            except Exception as error:
                logger.warning(
                    f"{self.name} - Failed to share {targetfile} with {shareWith}: {error}"
                )
                # g_testThreadsRunning -= 1
                # return

            try:
                self.TestOcsFederatedShares.assertEqual(
                    j["ocs"]["meta"]["status"], "ok"
                )
                self.TestOcsFederatedShares.assertEqual(
                    j["ocs"]["meta"]["statuscode"], 100
                )
            except Exception as error:
                logger.warning(
                    f"{self.name} - Sharing result not okay {targetfile}:{error}"
                )
                logger.warning(f"{self.name} - {j}")
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        logger.info(f"{self.name} - OcsMakeFederatedShare thread done")
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1


class TestOcsFederatedShares(unittest.TestCase):
    def test_logger(self):
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_create_federated_share(self):
        global logger, nodestotest
        logger.info("test_sharing_folders")
        drv = sunetnextcloud.TestTarget()
        if len(drv.nodestotest) == 1:
            nodestotest = drv.nodestotest
        logger.info(f"Testing node(s) {nodestotest}")

        for fullnode in nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f"TestID: {fullnode}")
                OcsMakeFederatedShareThread = OcsMakeFederatedShare(
                    name=fullnode, TestOcsFederatedShares=self, basicAuth=False
                )
                OcsMakeFederatedShareThread.start()

        while g_testThreadsRunning > 0:
            time.sleep(1)

        for fullnode in nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])


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
