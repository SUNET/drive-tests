""" Testing WebDAV functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import HtmlTestRunner
import tempfile
import os
from webdav3.client import Client
import logging
import threading
import time
from datetime import datetime
import xmlrunner

import sunetnextcloud

g_maxCheck = 10
g_webdav_timeout = 30
g_testFolder = 'WebDAVTest'
g_stressTestFolder = 'WebDAVStressTest'
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

drv = sunetnextcloud.TestTarget()

class WebDAVDneCheck(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVDneCheck thread started for node {self.name}')
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')
        
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
        dneName = 'THISFOLDERDOESNOTEXIST'

        for i in range(1,g_maxCheck):
            try:
                checkResult = client.check(dneName)
                if checkResult:
                    logger.warning(f'File {dneName} exists: {checkResult}')
            except Exception as error:
                logger.error(f'Error during client.check for {self.name}: {error}')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

            if (checkResult):
                logger.error(f'DNE check {i} for {dneName} should not return true')
            try:
                self.TestWebDAV.assertFalse(checkResult)
            except Exception as error:
                logger.error(f'Error in WebDAVDneCheck thread done for node {self.name}: {error}')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        logger.info(f'WebDAVDneCheck thread done for node {self.name}')
        g_testPassed[fullnode] = True
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')
        g_testThreadsRunning -= 1

class WebDAVList(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVList thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()

        nodeuser = []
        nodepwd = []
        if self.basicAuth:
            nodeuser.append(drv.get_ocsuser(fullnode))
            nodepwd.append(drv.get_ocsuserpassword(fullnode))

            nodeuser.append(drv.get_seleniumuser(fullnode))
            nodepwd.append(drv.get_seleniumuserpassword(fullnode))

            nodeuser.append(drv.get_seleniummfauser(fullnode))
            nodepwd.append(drv.get_seleniummfauserpassword(fullnode))
        else:
            nodeuser.append(drv.get_ocsuser(fullnode))
            nodepwd.append(drv.get_ocsuserapppassword(fullnode))

            nodeuser.append(drv.get_seleniumuser(fullnode))
            nodepwd.append(drv.get_seleniumuserapppassword(fullnode))

            nodeuser.append(drv.get_seleniummfauser(fullnode))
            nodepwd.append(drv.get_seleniummfauserapppassword(fullnode))

        logger.info(f'Usernames: {nodeuser}')

        try:
            for user in range(3):
                logger.info(f'Testing user: {nodeuser[user]}')
                url = drv.get_webdav_url(fullnode, nodeuser[user])
                logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser[user],
                'webdav_password' : nodepwd[user], 
                'webdav_timeout': g_webdav_timeout
                }
                client = Client(options)
                client.verify = drv.verify

                logger.info(client.list())
        except Exception as error:
            logger.error(f'Error in webdav listing: {error}')
            g_testThreadsRunning -= 1
            g_testPassed[fullnode] = False
            return

        logger.info(f'WebDAVList thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVMultiCheckAndRemove(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_threadResults
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVMultiCheckAndRemove thread started for node {self.name}')
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
        
        count = 0
        try:
            while count <= g_maxCheck:
                count += 1
                logger.info(f'Check for folder {g_testFolder}')
                if (not client.check(g_testFolder)):
                    logger.info(f'Folder does not exist: {g_testFolder}')
                    break
                else:
                    logger.info(f'Removing folder {g_testFolder}')
                    if (client.clean(g_testFolder)):
                        logger.info(f'Folder removed {g_testFolder}')    
                logger.warning(f'Multiple tries to remove folder: {count}')
        except Exception as error:
            logger.warning(f'Error during iteration {count} of removing {g_testFolder}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        
        try:
            self.TestWebDAV.assertFalse(client.check(g_testFolder))
        except Exception as error:
            logger.error(f'Error in WebDAVMultiCheckAndRemove for node {self.name} on check {count}: {error}.')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVMultiCheckAndRemove thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVCleanSeleniumFolders(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name    
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVCleanSeleniumFolders thread started for node {self.name}')
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
        except Exception as error:
            logger.error(f'Error in WebDAVCleanSeleniumFolders thread done for node {self.name}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVCleanSeleniumFolders thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVCleanTrashbin(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name    
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVCleanTrashbin thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()

        nodeuser = drv.get_seleniumuser(fullnode)
        if self.basicAuth:
            logger.info('Testing with basic authentication')
            nodepwd = drv.get_seleniumuserpassword(fullnode)
        else:
            logger.info('Testing with application password')
            nodepwd = drv.get_seleniumuserapppassword(fullnode)
        url = drv.get_webdav_url(fullnode, nodeuser)
        url = url.replace('files','trashbin')
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd,
        'webdav_timeout': g_webdav_timeout
        }

        try:
            client = Client(options)
            client.verify = drv.verify
            files = client.list('trash')
            files.pop(0)    # Remove first that is just the folder name
            for file in files:
                try:
                    targetdeletefile = f'trash/{file}'
                    logger.info(f'Deleting file {targetdeletefile}')
                    client.clean(targetdeletefile)
                except Exception as error:
                    logger.warning(f'Unable to delete {targetdeletefile} on {fullnode} due to: {error}')
        except Exception as error:
            logger.error(f'Error in WebDAVCleanTrashbin thread for node {self.name}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        logger.info(f'WebDAVCleanTrashbin thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVMakeSharingFolder(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVMakeSharingFolder thread started for node {self.name}')
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
        
        try:
            self.TestWebDAV.assertEqual(client.list().count(f'{g_sharedTestFolder}/'), 1)
        except Exception as error:
            logger.error(f'Error in WebDAVMakeSharingFolder thread done for node {self.name}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVMakeSharingFolder thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVPersonalBucketFolders(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVPersonalBucketFolders thread started for node {self.name}')
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
            folders = ''
            cnt = -1
            folder = 'test_webdav'
            self.TestWebDAV.assertEqual(client.list().count(f'{g_personalBucket}/'), 1)
            path = g_personalBucket + '/' + folder
            client.mkdir(path)
            logger.info(client.list(path))
            self.TestWebDAV.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 1)
            client.clean(path)
            folders = client.list(g_personalBucket)
            cnt = folders.count(f'{folder}/')
            # self.TestWebDAV.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 0)
            self.TestWebDAV.assertEqual(cnt, 0)
        except Exception as error:
            logger.info(f'Error in WebDAVPersonalBucketFolders thread done for node {self.name}: {error}')
            logger.info(f'Folders: {folder}; Count: {cnt}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVPersonalBucketFolders thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVSystemBucketFolders(threading.Thread):
    def __init__(self, name, basicAuth, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVSystemBucketFolders thread started for node {self.name}')
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

        folders = ''
        folder = 'test_webdav'

        try:
            cnt = -1
            self.TestWebDAV.assertEqual(client.list().count(f'{g_systemBucket}/'), 1)
            path = g_systemBucket + '/' + folder
            logger.info(f'Making path: {path}')
            client.mkdir(path)
            logger.info(client.list(path))
            self.TestWebDAV.assertEqual(client.list(g_systemBucket).count(f'{folder}/'), 1)
            logger.info(f'Cleaning path: {path}')
            client.clean(path)
            folders = client.list(g_personalBucket)
            cnt = folders.count(f'{folder}/')
            self.TestWebDAV.assertEqual(cnt, 0)
            # print(client.list(g_personalBucket))
        except Exception as error:
            logger.error(f'Error in WebDAVSystemBucketFolders thread done for node {self.name}: {error}')
            logger.info(f'Folders: {folder}; Count: {cnt}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        logger.info(f'WebDAVSystemBucketFolders thread done for node {self.name}')
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class WebDAVCreateMoveDelete(threading.Thread):
    def __init__(self, name, basicAuth, target, TestWebDAV):
        threading.Thread.__init__(self)
        self.name = name
        self.target = target
        self.TestWebDAV = TestWebDAV
        self.basicAuth = basicAuth

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        fullnode = self.name
        g_testPassed[fullnode] = False
        g_testThreadsRunning += 1
        logger.info(f'WebDAVCreateMoveDelete thread started for node {self.name}')
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

        filename = fullnode + '_' + g_filename + '.txt'
        mvfilename = 'mv_' + filename

        try:
            tmpfilename = tempfile.gettempdir() + '/' + fullnode + '_' + g_filename + '.txt'
        except Exception as error:
            logger.error(f'Getting temp dir for {fullnode}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        
        with open(tmpfilename, 'w') as f:
            f.write('Lorem ipsum')
            f.close()
        
        try:
            client = Client(options)
            client.verify = drv.verify
            client.mkdir(self.target)
            targetfile=self.target + '/' + filename
            targetmvfile=self.target + '/' + mvfilename
            # deleteoriginal=False # TODO: Implement delete original file
        except Exception as error:
            logger.error(f'Error preparing webdav client for {fullnode}: {error}')
            g_testThreadsRunning -= 1
            return
        
        try:
            logger.info(f'Uploading {tmpfilename} to {targetfile}')
            client.upload_sync(remote_path=targetfile, local_path=tmpfilename)
        except Exception as error:
            logger.error(f'Error uploading file to {fullnode}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        
        fileMoved = False
        moveCount = 0
        while  not fileMoved:
            try:
                logger.info(f'moving {targetfile} to {targetmvfile}')
                client.move(remote_path_from=targetfile, remote_path_to=targetmvfile)
                fileMoved = True
                break
            except Exception as error:
                logger.warning(f'Retry to move the file on {fullnode} due to: {error}')
                moveCount += 1

            if moveCount >= 3:
                logger.error(f'Error moving file {targetfile} after {moveCount} tries')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        fileDeleted = False
        deleteCount = 0
        while not fileDeleted:
            try:
                logger.info(f'Removing file {targetmvfile}')
                client.clean(targetmvfile)
                fileDeleted = True
            except Exception as error:
                logger.warning(f'Retry to delete the file on {fullnode} due to: {error}')
                deleteCount += 1

            if deleteCount >= 3:
                logger.error(f'Error deleting file {targetmvfile} on {fullnode} after {deleteCount} tries')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        try:
            logger.info(f'Removing local temp file: {tmpfilename}')
            os.remove(tmpfilename)
        except Exception as error:
            logger.error(f'Error removing the local temp file on {fullnode}: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1

class TestWebDAV(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_webdav_dne_check_basic_auth(self):
        global logger
        global g_testThreadsRunning
        logger.info('test_webdav_dne_check')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVDneCheckThread = WebDAVDneCheck(name=fullnode, basicAuth=True, TestWebDAV=self)
                WebDAVDneCheckThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_webdav_dne_check_app_token(self):
        global logger
        global g_testThreadsRunning
        logger.info('test_webdav_dne_check')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVDneCheckThread = WebDAVDneCheck(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVDneCheckThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_webdav_list(self):
        global logger
        logger.info('test_webdav_list')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVListThread = WebDAVList(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVListThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_webdav_multicheckandremove(self):
        global logger
        global g_testPassed
        logger.info('test_webdav_multicheckandremove')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            logger.info(f'WebDAV multicheck for {fullnode}')
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVMultiCheckAndRemoveThread = WebDAVMultiCheckAndRemove(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVMultiCheckAndRemoveThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_clean_seleniumuserfolders(self):
        global logger
        logger.info('test_clean_seleniumuserfolders')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVCleanSeleniumFoldersThread = WebDAVCleanSeleniumFolders(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVCleanSeleniumFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_sharing_folders(self):
        global logger
        logger.info('test_sharing_folders')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVMakeSharingFolderThread = WebDAVMakeSharingFolder(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVMakeSharingFolderThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_personal_bucket_folders(self):
        global logger
        logger.info('test_personal_bucket_folders')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVPersonalBucketFoldersThread = WebDAVPersonalBucketFolders(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVPersonalBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_system_bucket_folders(self):
        global logger
        logger.info('test_system_bucket_folders')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVSystemBucketFoldersThread = WebDAVSystemBucketFolders(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_cmd_in_home_folder(self):
        global logger
        logger.info('test_cmd_in_home_folder')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVSystemBucketFoldersThread = WebDAVCreateMoveDelete(name=fullnode, target='selenium-home', basicAuth=False, TestWebDAV=self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_cmd_in_personal_bucket(self):
        global logger
        logger.info('test_cmd_in_personal_bucket')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVSystemBucketFoldersThread = WebDAVCreateMoveDelete(name=fullnode, target=g_personalBucket, basicAuth=False, TestWebDAV=self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_cmd_in_system_bucket(self):
        global logger
        logger.info('test_cmd_in_system_bucket')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVSystemBucketFoldersThread = WebDAVCreateMoveDelete(name=fullnode, target=g_systemBucket, basicAuth=False, TestWebDAV=self)
                WebDAVSystemBucketFoldersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_empty_trashbin(self):
        global logger
        logger.info('test_empty_trashbin')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVCleanTrashbinThread = WebDAVCleanTrashbin(name=fullnode, basicAuth=False, TestWebDAV=self)
                WebDAVCleanTrashbinThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    elif drv.testrunner == 'txt':
        unittest.main(testRunner=unittest.TextTestRunner(resultclass=sunetnextcloud.NumbersTestResult))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-acceptance", add_timestamp=False))
