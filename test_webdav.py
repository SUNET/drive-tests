""" Testing WebDAV functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import requests
from requests.auth import HTTPBasicAuth
import json
import os
from webdav3.client import Client
import logging
import threading
import time

import sunetdrive

g_maxCheck = 10
g_testFolder = 'SeleniumCollaboraTest'
g_stressTestFolder = 'SeleniumCollaboraStressTest'
g_sharedTestFolder = 'SharedFolder'
g_personalBucket = 'selenium-personal'
g_systemBucket = 'selenium-system'
ocsheaders = { "OCS-APIRequest" : "true" } 
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class WebDAVDneCheck(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'WebDAVDneCheck thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    
        
        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        client = Client(options)
        dneName = 'THISFOLDERDOESNOTEXIST'

        for i in range(1,g_maxCheck):
            result = client.check(dneName)
            if (result):
                logger.error(f'DNE check {i} for {dneName} should not return true')
            self.TestWebDAV.assertFalse(result)

        logger.info(f'WebDAVDneCheck thread done for node {self.name}')
        testThreadRunning = False

class WebDAVList(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'WebDAVList thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    

        nodeuser = []
        nodepwd = []
        nodeuser.append(drv.get_ocsuser(fullnode))
        nodepwd.append(drv.get_ocsuserapppassword(fullnode))

        nodeuser.append(drv.get_seleniumuser(fullnode))
        nodepwd.append(drv.get_seleniumuserapppassword(fullnode))

        nodeuser.append(drv.get_seleniummfauser(fullnode))
        nodepwd.append(drv.get_seleniummfauserapppassword(fullnode))

        logger.info(f'Usernames: {nodeuser}')

        for user in range(3):
            logger.warning(f'Testing user: {nodeuser[user]}')
            url = drv.get_webdav_url(fullnode, nodeuser[user])
            logger.info(f'URL: {url}')
            options = {
            'webdav_hostname': url,
            'webdav_login' : nodeuser[user],
            'webdav_password' : nodepwd[user] 
            }
            client = Client(options)
            logger.info(client.list())

        logger.info(f'WebDAVList thread done for node {self.name}')
        testThreadRunning = False

class WebDAVMultiCheckAndRemove(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'WebDAVMultiCheckAndRemove thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    

        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        client = Client(options)
        
        count = 0
        while count <= g_maxCheck:
            count += 1
            logger.info(f'Check for folder {g_testFolder}')
            if (client.check(g_testFolder) == False):
                logger.info(f'Folder does not exist: {g_testFolder}')
                break
            else:
                logger.warning(f'Removing folder {g_testFolder}')
                if (client.clean(g_testFolder)):
                    logger.info(f'Folder removed {g_testFolder}')    
            logger.warning(f'Multiple tries to remove folder: {count}')
        self.TestWebDAV.assertFalse(client.check(g_testFolder))

        logger.info(f'WebDAVMultiCheckAndRemove thread done for node {self.name}')
        testThreadRunning = False

class WebDAVCleanSeleniumFolders(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'WebDAVCleanSeleniumFolders thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    

        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        client = Client(options)

        # for i in range(1,g_maxCheck):
        #     if (client.check(g_testFolder)):
        #         logger.error(f'Check for {g_testFolder} should not return true')

        logger.info('Listing folder contents before removing the Selenium folders')
        logger.info(client.list())
        logger.info('Removing Selenium user folders')
        if client.check(g_testFolder):
            client.clean(g_testFolder)
        if client.check(g_stressTestFolder):
            client.clean(g_stressTestFolder)
        logger.info('Listing folder contents after removing the Selenium folders')
        logger.info(client.list())

        logger.info(f'WebDAVCleanSeleniumFolders thread done for node {self.name}')
        testThreadRunning = False

class WebDAVMakeSharingFolder(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'WebDAVMakeSharingFolder thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    

        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        client = Client(options)

        client.mkdir(g_sharedTestFolder)
        self.TestWebDAV.assertEqual(client.list().count(f'{g_sharedTestFolder}/'), 1)

        logger.info(f'WebDAVMakeSharingFolder thread done for node {self.name}')
        testThreadRunning = False

class WebDAVPersonalBucketFolders(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'WebDAVPersonalBucketFolders thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    

        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        client = Client(options)

        self.TestWebDAV.assertEqual(client.list().count(f'{g_personalBucket}/'), 1)

        folder = 'test_webdav'
        path = g_personalBucket + '/' + folder
        client.mkdir(path)
        logger.info(client.list(path))
        self.TestWebDAV.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 1)
        client.clean(path)
        self.TestWebDAV.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 0)
        # print(client.list(g_personalBucket))

        logger.info(f'WebDAVPersonalBucketFolders thread done for node {self.name}')
        testThreadRunning = False

class WebDAVSystemBucketFolders(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'WebDAVSystemBucketFolders thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    

        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        client = Client(options)

        self.TestWebDAV.assertEqual(client.list().count(f'{g_systemBucket}/'), 1)

        folder = 'test_webdav'
        path = g_systemBucket + '/' + folder
        client.mkdir(path)
        logger.info(client.list(path))
        self.TestWebDAV.assertEqual(client.list(g_systemBucket).count(f'{folder}/'), 1)
        client.clean(path)
        self.TestWebDAV.assertEqual(client.list(g_systemBucket).count(f'{folder}/'), 0)
        # print(client.list(g_personalBucket))

        logger.info(f'WebDAVSystemBucketFolders thread done for node {self.name}')
        testThreadRunning = False

class TestWebDAV(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.warning(f'logger.info test_logger')
        pass

    def test_webdav_dne_check(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVDneCheckThread = WebDAVDneCheck(fullnode, self)
                WebDAVDneCheckThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def test_webdav_list(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVListThread = WebDAVList(fullnode, self)
                WebDAVListThread.start()

        while(testThreadRunning == True):
            time.sleep(1)


    def test_webdav_multicheckandremove(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            logger.info(f'WebDAV multicheck for {fullnode}')
            with self.subTest(mynode=fullnode):
                WebDAVMultiCheckAndRemoveThread = WebDAVMultiCheckAndRemove(fullnode, self)
                WebDAVMultiCheckAndRemoveThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def test_webdav_clean_seleniumuserfolders(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVCleanSeleniumFoldersThread = WebDAVCleanSeleniumFolders(fullnode, self)
                WebDAVCleanSeleniumFoldersThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def make_sharing_folder(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVMakeSharingFolderThread = WebDAVMakeSharingFolder(fullnode, self)
                WebDAVMakeSharingFolderThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def personal_bucket_folders(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVPersonalBucketFoldersThread = WebDAVPersonalBucketFolders(fullnode, self)
                WebDAVPersonalBucketFoldersThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def system_bucket_folders(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVSystemBucketFoldersThread = WebDAVSystemBucketFolders(fullnode, self)
                WebDAVSystemBucketFoldersThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
