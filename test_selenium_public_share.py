""" Test creating a public share and uploading data to it
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import HtmlTestRunner
import requests
import json
import time
import logging
import threading
import xmlrunner
from webdav3.client import Client
import tempfile
import urllib.parse

import sunetnextcloud

ocsheaders = { "OCS-APIRequest" : "true" } 
nodestotest = ['sunet', 'su', 'extern']
g_requestTimeout = 30
g_webdav_timeout = 30
g_sharedTestFolder = 'PublicFileRequestFolder'
g_filename = 'public_share.txt'
g_testPassed = {}
g_testThreadsRunning = 0

logger = logging.getLogger('TestLogger')
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

class OcsMakePublicShare(threading.Thread):
    def __init__(self, name, TestOcsPublicShares, basicAuth, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsPublicShares = TestOcsPublicShares
        self.basicAuth = basicAuth
        self.verify = verify

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'OcsMakePublicShare thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()

        nodeuser = drv.get_seleniumuser(fullnode)
        if self.basicAuth:
            logger.info('Testing with basic authentication')
            nodepwd = drv.get_seleniumuserpassword(fullnode)
        else:
            logger.info('Testing with application password')
            nodepwd = drv.get_seleniumuserapppassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd,
        'webdav_timeout': g_webdav_timeout
        }

        client = Client(options)
        client.verify = drv.verify

        try:
            logger.info(f'Before mkdir: {client.list()}')
            client.mkdir(g_sharedTestFolder)
            logger.info(f'After mkdir: {client.list()}')
        except Exception as error:
            logger.error(f'Error making folder {g_sharedTestFolder} on {self.name}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        filename = fullnode + '_' + g_filename

        try:
            tmpfilename = tempfile.gettempdir() + '/' + fullnode + '_' + g_filename
        except Exception as error:
            logger.error(f'Getting temp dir for {fullnode}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        
        with open(tmpfilename, 'w') as f:
            f.write(f'Public share for {fullnode}')
            f.close()
        
        try:
            client = Client(options)
            client.verify = drv.verify
            client.mkdir(g_sharedTestFolder)
            targetfile = g_sharedTestFolder + '/' + filename
            targetfolder = g_sharedTestFolder
            # deleteoriginal=False # TODO: Implement delete original file
        except Exception as error:
            logger.error(f'Error preparing webdav client for {fullnode}: {error}')
            g_testThreadsRunning -= 1
            return
        
        deleteShares = True
        if deleteShares:
            logger.info(f'Get all shares for {fullnode}')
            url = drv.get_share_url(fullnode)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)

            try:
                r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
                j = json.loads(r.text)
                # logger.info(f'Found shares: {json.dumps(j, indent=4, sort_keys=True)}')

                for share in j['ocs']['data']:
                    url = drv.get_share_id_url(fullnode, share['id'])
                    logger.info(f"Delete share: {share['id']} - {url}")
                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)
                    r = requests.delete(url, headers=ocsheaders, verify=self.verify)
                    logger.info(f'Share deleted: {r.text}')
            except Exception as error:
                logger.error(f'Error getting {url}: {error}')
                g_testThreadsRunning -= 1
                return      

        logger.info(f'Create public share for {self.name}')
        url = drv.get_share_url(fullnode)
        logger.info(f'Share url: {url}')
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)
        session = requests.Session()
        data = { 'path': targetfolder, 'shareType': 3, 'note': 'Testautomation'}

        try:
            # logger.info(f'Share to {url}')
            r = session.post(url, headers=ocsheaders, data=data, verify=self.verify)
            j = json.loads(r.text)
            # logger.info(f'Result of sharing: {json.dumps(j, indent=4, sort_keys=True)}')
            logger.info(f'Share url: {j["ocs"]["data"]["url"]}')
            logger.info(f'Share permissions: {j["ocs"]["data"]["permissions"]}')
            shareId = j["ocs"]["data"]["id"]
            logger.info(f'Share ID: {shareId}')

            # logger.info(f'Result of sharing: {j["ocs"]["meta"]["status"]} - {j["ocs"]["meta"]["statuscode"]}')
        except Exception as error:
            logger.warning(f'Failed to share {targetfolder}: {error}')
            g_testThreadsRunning -= 1
            return

        # Update share id with new permissions
        url = drv.get_share_id_url(fullnode, shareId)
        logger.info(f"Update share: {shareId} - {url}")
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        attributes = [
            {
                "scope": "file-request",
                "key": "enabled",
                "value": True
            }
        ]

        # data = { 'permissions': 31, 'publicUpload': 'true', 'attributes:': urllib.parse.quote(json.dumps(attributes)) }
        # r = requests.put(url, headers=ocsheaders, data=data, verify=self.verify)
        # j = json.loads(r.text)
        # logger.info(f'Share updated: {json.dumps(j, indent=4, sort_keys=True)}')

        data = { 'permissions': 1 }
        r = requests.put(url, headers=ocsheaders, data=data, verify=self.verify)
        j = json.loads(r.text)
        logger.info(f'Updated permissions: {j["ocs"]["data"]["permissions"]}')
        # logger.info(f'Share updated: {json.dumps(j, indent=4, sort_keys=True)}')

        # data = { 'publicUpload': 'true' }
        # r = requests.put(url, headers=ocsheaders, data=data, verify=self.verify)
        # j = json.loads(r.text)
        # logger.info(f'Share updated: {json.dumps(j, indent=4, sort_keys=True)}')

        try:
            self.TestOcsPublicShares.assertEqual(j["ocs"]["meta"]["status"], 'ok')
            self.TestOcsPublicShares.assertEqual(j["ocs"]["meta"]["statuscode"], 100)
        except Exception as error:
            logger.warning(f'Sharing result not okay {targetfolder}:{error}')
            g_testThreadsRunning -= 1
            return 
        
        logger.info(f'OcsMakePublicShare thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1


class TestSeleniumPublicShares(unittest.TestCase):
    def test_logger(self):
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_create_public_share(self):
        logger.info(f'Create public share')
        if len(drv.nodestotest) == 1:
            nodestotest = drv.nodestotest

        for fullnode in nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')

        for fullnode in nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                OcsMakePublicShareThread = OcsMakePublicShare(name=fullnode, TestOcsPublicShares=self, basicAuth=False)
                OcsMakePublicShareThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)
    
        for fullnode in nodestotest:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    elif drv.testrunner == 'txt':
        unittest.main(testRunner=unittest.TextTestRunner(resultclass=sunetnextcloud.NumbersTestResult))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-ocs-federated-shares", add_timestamp=False))
