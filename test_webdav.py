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
from datetime import datetime

import sunetdrive

g_maxCheck = 10
g_testFolder = 'SeleniumCollaboraTest'
g_stressTestFolder = 'SeleniumCollaboraStressTest'
g_sharedTestFolder = 'SharedFolder'
g_personalBucket = 'selenium-personal'
g_systemBucket = 'selenium-system'
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_testPassed = {}
g_testThreadsRunning = 0
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
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVDneCheck thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')
        
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
            try:
                self.TestWebDAV.assertFalse(result)
            except:
                logger.error(f'Error in WebDAVDneCheck thread done for node {self.name}')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        logger.info(f'WebDAVDneCheck thread done for node {self.name}')
        g_testPassed[fullnode] = True
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')
        g_testThreadsRunning -= 1

class WebDAVList(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVList thread started for node {self.name}')
        drv = sunetdrive.TestTarget()

        nodeuser = []
        nodepwd = []
        nodeuser.append(drv.get_ocsuser(fullnode))
        nodepwd.append(drv.get_ocsuserapppassword(fullnode))

        nodeuser.append(drv.get_seleniumuser(fullnode))
        nodepwd.append(drv.get_seleniumuserapppassword(fullnode))

        nodeuser.append(drv.get_seleniummfauser(fullnode))
        nodepwd.append(drv.get_seleniummfauserapppassword(fullnode))

        logger.info(f'Usernames: {nodeuser}')

        try:
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
        except:
            logger.error(f'Error in webdav listing')
            g_testThreadsRunning -= 1
            g_testPassed[fullnode] = False
            return

        logger.info(f'WebDAVList thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVMultiCheckAndRemove(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global logger
        global g_threadResults
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVMultiCheckAndRemove thread started for node {self.name}')
        drv = sunetdrive.TestTarget()

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
        try:
            self.TestWebDAV.assertFalse(client.check(g_testFolder))
        except:
            logger.warning(f'Error in WebDAVMultiCheckAndRemove for node {self.name}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVMultiCheckAndRemove thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVCleanSeleniumFolders(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name    
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVCleanSeleniumFolders thread started for node {self.name}')
        drv = sunetdrive.TestTarget()

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
        try:
            logger.info('Listing folder contents before removing the Selenium folders')
            logger.info(client.list())
            logger.info('Removing Selenium user folders')
            if client.check(g_testFolder):
                client.clean(g_testFolder)
            if client.check(g_stressTestFolder):
                client.clean(g_stressTestFolder)
            logger.info('Listing folder contents after removing the Selenium folders')
            logger.info(client.list())
        except:
            logger.error(f'Error in WebDAVCleanSeleniumFolders thread done for node {self.name}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVCleanSeleniumFolders thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVMakeSharingFolder(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVMakeSharingFolder thread started for node {self.name}')
        drv = sunetdrive.TestTarget()

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
        try:
            self.TestWebDAV.assertEqual(client.list().count(f'{g_sharedTestFolder}/'), 1)
        except:
            logger.error(f'Error in WebDAVMakeSharingFolder thread done for node {self.name}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1

        logger.info(f'WebDAVMakeSharingFolder thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVPersonalBucketFolders(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVPersonalBucketFolders thread started for node {self.name}')
        drv = sunetdrive.TestTarget()

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

        try:
            self.TestWebDAV.assertEqual(client.list().count(f'{g_personalBucket}/'), 1)
            folder = 'test_webdav'
            path = g_personalBucket + '/' + folder
            client.mkdir(path)
            logger.info(client.list(path))
            self.TestWebDAV.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 1)
            client.clean(path)
            self.TestWebDAV.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 0)
            # print(client.list(g_personalBucket))
        except:
            logger.info(f'Error in WebDAVPersonalBucketFolders thread done for node {self.name}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVPersonalBucketFolders thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVSystemBucketFolders(threading.Thread):
    def __init__(self, name, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVSystemBucketFolders thread started for node {self.name}')
        drv = sunetdrive.TestTarget()

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

        try:
            self.TestWebDAV.assertEqual(client.list().count(f'{g_systemBucket}/'), 1)
            folder = 'test_webdav'
            path = g_systemBucket + '/' + folder
            client.mkdir(path)
            logger.info(client.list(path))
            self.TestWebDAV.assertEqual(client.list(g_systemBucket).count(f'{folder}/'), 1)
            client.clean(path)
            self.TestWebDAV.assertEqual(client.list(g_systemBucket).count(f'{folder}/'), 0)
            # print(client.list(g_personalBucket))
        except:
            logger.error(f'Error in WebDAVSystemBucketFolders thread done for node {self.name}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVSystemBucketFolders thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVCreateMoveDelete(threading.Thread):
    def __init__(self, name, target, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.target = target
        self.TestWebDAV = TestWebDAV

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVCreateMoveDelete thread started for node {self.name}')
        drv = sunetdrive.TestTarget()

        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        filename = fullnode + '_' + g_filename + '.txt'
        mvfilename = 'mv_' + filename
        with open(filename, 'w') as f:
            f.write('Lorem ipsum')
            f.close()

        
        try:
            client = Client(options)
            client.mkdir(self.target)
            targetfile=self.target + '/' + filename
            targetmvfile=self.target + '/' + mvfilename
            deleteoriginal=False
        except:
            logger.error(f'Error preparing webdav client')
            return
        
        try:
            logger.info(f'Uploading {filename} to {targetfile}')
            client.upload_sync(remote_path=targetfile, local_path=filename)
        except:
            logger.error(f'Error uploading file')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        try:
            logger.info(f'moving {targetfile} to {targetmvfile}')
            client.move(remote_path_from=targetfile, remote_path_to=targetmvfile)
        except:
            logger.error(f'Error moving the file')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        try:
            logger.info(f'Removing file {targetmvfile}')
            client.clean(targetmvfile)
        except:
            logger.error(f'Error deleting the file')
            deleteoriginal=True
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        if deleteoriginal:
            try:
                logger.info(f'Removing original file {targetfile}')
                client.clean(targetfile)
            except:
                logger.error(f'Error deleting the original file')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        os.remove(filename)
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class TestWebDAV(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'logger.info test_logger')
        pass

    def test_webdav_dne_check(self):
        global logger
        global g_testThreadsRunning
        logger.info(f'test_webdav_dne_check')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVDneCheckThread = WebDAVDneCheck(fullnode, self)
                WebDAVDneCheckThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_webdav_list(self):
        global logger
        logger.info(f'test_webdav_list')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVListThread = WebDAVList(fullnode, self)
                WebDAVListThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_webdav_multicheckandremove(self):
        global logger
        global g_testPassed
        logger.info(f'test_webdav_multicheckandremove')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            logger.info(f'WebDAV multicheck for {fullnode}')
            with self.subTest(mynode=fullnode):
                WebDAVMultiCheckAndRemoveThread = WebDAVMultiCheckAndRemove(fullnode, self)
                WebDAVMultiCheckAndRemoveThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_clean_seleniumuserfolders(self):
        global logger
        logger.info(f'test_clean_seleniumuserfolders')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVCleanSeleniumFoldersThread = WebDAVCleanSeleniumFolders(fullnode, self)
                WebDAVCleanSeleniumFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_sharing_folders(self):
        global logger
        logger.info(f'test_sharing_folders')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVMakeSharingFolderThread = WebDAVMakeSharingFolder(fullnode, self)
                WebDAVMakeSharingFolderThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_personal_bucket_folders(self):
        global logger
        logger.info(f'test_personal_bucket_folders')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVPersonalBucketFoldersThread = WebDAVPersonalBucketFolders(fullnode, self)
                WebDAVPersonalBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_system_bucket_folders(self):
        global logger
        logger.info(f'test_system_bucket_folders')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVSystemBucketFoldersThread = WebDAVSystemBucketFolders(fullnode, self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_cmd_in_home_folder(self):
        global logger
        logger.info(f'test_cmd_in_home_folder')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVSystemBucketFoldersThread = WebDAVCreateMoveDelete(fullnode, 'selenium-home', self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_cmd_in_personal_bucket(self):
        global logger
        logger.info(f'test_cmd_in_personal_bucket')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVSystemBucketFoldersThread = WebDAVCreateMoveDelete(fullnode, 'selenium-personal', self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_cmd_in_system_bucket(self):
        global logger
        logger.info(f'test_cmd_in_system_bucket')
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                WebDAVSystemBucketFoldersThread = WebDAVCreateMoveDelete(fullnode, 'selenium-system', self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
