""" Testing OCS functions for Sunet Drive
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

import sunetnextcloud

ocsheaders = { "OCS-APIRequest" : "true" } 

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

g_testPassed = {}
g_testThreadsRunning = 0
g_requestTimeout = 10
g_webdav_timeout = 30
g_sharedTestFolder = 'SharedFolder'
g_filename = 'federated_share.txt'

logger = logging.getLogger('TestLogger')
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

# class OcsMakeFederatedShare(threading.Thread):
#     def __init__(self, name, TestOcsFederatedShares, basicAuth, verify=True):
#         threading.Thread.__init__(self)
#         self.name = name
#         self.TestOcsFederatedShares = TestOcsFederatedShares
#         self.basicAuth = basicAuth
#         self.verify = verify

#     def run(self):
#         global logger
#         global g_testPassed
#         global g_testThreadsRunning
#         fullnode = self.name
#         g_testPassed[fullnode] = False
#         g_testThreadsRunning += 1
#         logger.info(f'OcsMakeFederatedShare thread started for node {self.name}')
#         drv = sunetnextcloud.TestTarget()

#         nodeuser = drv.get_seleniumuser(fullnode)
#         if self.basicAuth:
#             logger.info('Testing with basic authentication')
#             nodepwd = drv.get_seleniumuserpassword(fullnode)
#         else:
#             logger.info('Testing with application password')
#             nodepwd = drv.get_seleniumuserapppassword(fullnode)
#         url = drv.get_webdav_url(fullnode, nodeuser)
#         logger.info(f'URL: {url}')
#         options = {
#         'webdav_hostname': url,
#         'webdav_login' : nodeuser,
#         'webdav_password' : nodepwd,
#         'webdav_timeout': g_webdav_timeout
#         }

#         client = Client(options)
#         client.verify = drv.verify

#         try:
#             logger.info(f'Before mkdir: {client.list()}')
#             client.mkdir(g_sharedTestFolder)
#             logger.info(f'After mkdir: {client.list()}')
#         except Exception as error:
#             logger.error(f'Error making folder {g_sharedTestFolder} on {self.name}: {error}')
#             g_testPassed[fullnode] = False
#             g_testThreadsRunning -= 1
#             return

#         filename = fullnode + '_' + g_filename

#         try:
#             tmpfilename = tempfile.gettempdir() + '/' + fullnode + '_' + g_filename
#         except Exception as error:
#             logger.error(f'Getting temp dir for {fullnode}: {error}')
#             g_testPassed[fullnode] = False
#             g_testThreadsRunning -= 1
#             return
        
#         with open(tmpfilename, 'w') as f:
#             f.write(f'Federated share for {fullnode}')
#             f.close()
        
#         try:
#             client = Client(options)
#             client.verify = drv.verify
#             client.mkdir(g_sharedTestFolder)
#             targetfile=g_sharedTestFolder + '/' + filename
#             # deleteoriginal=False # TODO: Implement delete original file
#         except Exception as error:
#             logger.error(f'Error preparing webdav client for {fullnode}: {error}')
#             g_testThreadsRunning -= 1
#             return
        
#         try:
#             logger.info(f'Uploading {tmpfilename} to {targetfile}')
#             client.upload_sync(remote_path=targetfile, local_path=tmpfilename)
#         except Exception as error:
#             logger.error(f'Error uploading file to {fullnode}: {error}')
#             g_testPassed[fullnode] = False
#             g_testThreadsRunning -= 1
#             return

#         logger.info(f'Get all shares for {fullnode}')
#         url = drv.get_share_url(fullnode)
#         url = url.replace("$USERNAME$", nodeuser)
#         url = url.replace("$PASSWORD$", nodepwd)

#         try:
#             r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
#             j = json.loads(r.text)
#             # logger.info(f'Found shares: {json.dumps(j, indent=4, sort_keys=True)}')

#             for share in j['ocs']['data']:
#                 url = drv.get_share_id_url(fullnode, share['id'])
#                 logger.info(f'Delete share: {share['id']} - {url}')
#                 url = url.replace("$USERNAME$", nodeuser)
#                 url = url.replace("$PASSWORD$", nodepwd)
#                 r = requests.delete(url, headers=ocsheaders, verify=self.verify)
#                 logger.info(f'Share deleted: {r.text}')
#         except Exception as error:
#             logger.error(f'Error getting {url}: {error}')
#             g_testThreadsRunning -= 1
#             return      

#         for shareNode in drv.nodelist:
#             if shareNode == fullnode:
#                 logger.info(f'Do not share with self')
#                 continue # with next node

#             if drv.target == 'test':
#                 delimiter = 'test.'
#             else:
#                 delimiter = ''

#             shareWith = f'_selenium_{shareNode}@{shareNode}.drive.{delimiter}sunet.se'
#             # shareWith = '_selenium_bth@bth.drive.test.sunet.se'
#             logger.info(f'Share with {shareWith}')

#             url = drv.get_share_url(fullnode)
#             logger.info(f'Share url: {url}')
#             url = url.replace("$USERNAME$", nodeuser)
#             url = url.replace("$PASSWORD$", nodepwd)
#             session = requests.Session()
#             data = { 'path': targetfile, 'shareWith': shareWith, 'shareType': 6, 'note': 'Testautomation'}
#             logger.info(f'Data: {data}')

#             try:
#                 # logger.info(f'Share to {url}')
#                 r = session.post(url, headers=ocsheaders, data=data, verify=self.verify)
#                 j = json.loads(r.text)
#                 logger.info(f'Result of sharing: {j["ocs"]["meta"]["status"]} - {j["ocs"]["meta"]["statuscode"]}')
#             except Exception as error:
#                 logger.warning(f'Failed to share {targetfile} with {shareWith}: {error}')
#                 # g_testThreadsRunning -= 1
#                 # return

#             try:
#                 self.TestOcsFederatedShares.assertEqual(j["ocs"]["meta"]["status"], 'ok')
#                 self.TestOcsFederatedShares.assertEqual(j["ocs"]["meta"]["statuscode"], 100)
#             except Exception as error:
#                 logger.warning(f'Sharing result not okay {targetfile}:{error}')
#                 # g_testThreadsRunning -= 1
#                 # return 
        
#         logger.info(f'OcsMakeFederatedShare thread done for node {self.name}')
#         g_testPassed[fullnode] = True
#         g_testThreadsRunning -= 1

class TestOcsFederatedShares(unittest.TestCase):
    def test_logger(self):
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_delete_federated_shares(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'Delete shares for {fullnode}')
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserapppassword(fullnode)
                url = drv.get_pending_shares_url(fullnode)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)
                r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))

                for share in j['ocs']['data']:
                    filename = share['name']
                    logger.info(f'Deleting share {filename}')
                    url = drv.get_pending_shares_id_url(fullnode, share['id'])
                    logger.info(f"Delete share: {share['id']} - {url}")
                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)
                    r = requests.delete(url, headers=ocsheaders)
                    # logger.info(f'Pending share accepted: {r.text}')

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    elif drv.testrunner == 'txt':
        unittest.main(testRunner=unittest.TextTestRunner(resultclass=sunetnextcloud.NumbersTestResult))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-ocs-federated-shares", add_timestamp=False))
