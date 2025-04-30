""" Testing WebDavPerformance functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import tempfile
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import glob
from pathlib import Path
import subprocess
import shutil
from webdav3.client import Client
from webdav3.exceptions import WebDavException
import logging
import threading
import time
import sys
from datetime import datetime
import xmlrunner

import sunetnextcloud

g_maxCheck = 10
g_WebDavPerformance_timeout = 30
g_testFolder = 'WebDavPerformanceTest'
g_stressTestFolder = 'WebDavPerformanceStressTest'
g_sharedTestFolder = 'SharedFolder'
g_personalBucket = 'selenium-personal'
g_systemBucket = 'selenium-system'
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_davPerformanceResults = []
g_testPassed = {}
g_testThreadsRunning = 0
ocsheaders = { "OCS-APIRequest" : "true" } 
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

KB = 1024
MB = 1024 * KB
GB = 1024 * MB
# fileSizes=[1,4,8,12] # Only GB, larger than 1
fileSizes=[1,2] # Only GB, larger than 1
fileNames=[] # Array with the files 
targetDirectory=f'{tempfile.gettempdir()}/largefiles'

expectedSize = 0
for size in fileSizes:
    expectedSize += size

def threading_exception(args):
    logger.error(f'Threading exception: {args}')
    decreaseUploadCount()
    sys.excepthook(*sys.exc_info())

threading.excepthook = threading_exception

def system_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("System exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = system_exception

def deleteTestData():
    logpath = f'{targetDirectory}/*'
    for full_path in glob.glob(logpath):
        logger.info(f'Removing file {full_path}')
        os.remove(full_path)

def checkTestData():
    Path(targetDirectory).mkdir(parents=True, exist_ok=True)
    logpath = f'{targetDirectory}/*G.bin'
    totalSize = 0

    for full_path in glob.glob(logpath):
        totalSize += Path(full_path).stat().st_size / GB
    if totalSize == 0:
        logger.info(f'No test data found in {targetDirectory}')
        return False
    
    if totalSize != expectedSize:
        logger.warning(f'Total size of existing files does not match, {totalSize} != {expectedSize}')
        return False

    for fileSize in fileSizes:
        filename = f'{str(fileSize)}G.bin'
        pathname = f'{targetDirectory}/{filename}'            # Check if the file exists in the temp directory
        logger.info(f'Checking file {pathname}')
        if Path(pathname).exists():
            existingFileSize = Path(pathname).stat().st_size / GB
            if existingFileSize == fileSize:
                logger.info(f'File {pathname} exists with correct file size {fileSize}')
            else:
                logger.warning(f'File size for {pathname} does not match {existingFileSize} != {fileSize}')
                return False
    return True

def generateTestData():
    # Check if we have enought space in the temp directory; we assume that check and/or delete was executed before this
    Path(targetDirectory).mkdir(parents=True, exist_ok=True)
    tmpFree = shutil.disk_usage(targetDirectory).free / GB
    logger.info(f'{targetDirectory} has {tmpFree:.2f} GB free')
    if tmpFree > expectedSize:
        logger.info(f'Using {targetDirectory} for temporary files')
    else:
        logger.error(f'Not enough space in {targetDirectory}')

    for fileSize in fileSizes:
        filename = f'{str(fileSize)}G.bin'
        pathname = f'{targetDirectory}/{filename}'
        logger.info(f'Generating file {pathname}')
        cmd=f'head -c {fileSize}G /dev/urandom > {pathname}'
        logger.info(f'Running subprocess {cmd}')
        os.system(cmd)

def decreaseUploadCount():
    global g_testThreadsRunning
    g_testThreadsRunning -= 1

def webdavUpload(client, local_path, remote_path):
    global logger, g_testThreadsRunning
    logger.info(f'Upload {local_path}')
    if client == None:
        logger.error(f'No client provided')
        decreaseUploadCount()
        return
    if local_path == None:
        logger.error(f'No filename provided')
        decreaseUploadCount()
        return
    if remote_path == None:
        logger.error(f'No target filename provided')
        decreaseUploadCount()
        return
    try:
        client.upload_sync(remote_path=remote_path,local_path=local_path)
    except Exception as error:
        logger.error(f'Error uploading {remote_path}:{error}')
        decreaseUploadCount()
        return

    decreaseUploadCount()

def webdavClean(client, filename):
    global logger, g_testThreadsRunning
    if client == None:
        logger.error(f'No client provided')
        return
    if filename == None:
        logger.error(f'No filename provided')
        return
    logger.info(f'Cleaning {filename}')
    client.clean(filename)

class TestLargeFilePerformance(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_testdata(self):        
        if checkTestData() == False:
            logger.warning(f'File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

        self.assertTrue(checkTestData())
        pass

    def test_webdav_home(self):
        serverTargetFolder = 'selenium-home/largefiles'
        global logger, g_testThreadsRunning, g_davPerformanceResults
        g_davPerformanceResults.clear()

        if checkTestData() == False:
            logger.warning(f'File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

        numFiles = 4
        maxUploads = 1
        maxDeletes = 1
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                for fe in range(1,2):
                    nodebaseurl = drv.get_node_base_url(fullnode)
                    serverid = f'node{fe}.{nodebaseurl}'

                    logger.info(f'TestID: {fullnode}')

                    nodeuser = drv.get_seleniumuser(fullnode)
                    nodepwd = drv.get_seleniumuserpassword(fullnode)
                    url = drv.get_webdav_url(fullnode, nodeuser)
                    logger.info(f'URL: {url}')
                    options = {
                    'webdav_hostname': url,
                    'webdav_login' : nodeuser,
                    'webdav_password' : nodepwd,
                    'webdav_timeout': g_WebDavPerformance_timeout
                    }

                    client = Client(options)
                    client.session.cookies.set('SERVERID', serverid)

                    logger.info(client.list())
                    client.mkdir(serverTargetFolder)
                    files = []

                    for fileSize in fileSizes:
                        filename = f'{str(fileSize)}G.bin'
                        files.append(filename)

                    logger.info(f'List of local files {files}')

                    startTime = datetime.now()
                    logger.info(f'Async upload of {maxUploads} files concurrently')
                    try:
                        for i in range(0,numFiles,maxUploads):
                            x = i
                            logger.info(f'Batch upload node{fe} {files[x:x+maxUploads]}')
                            for file in files[x:x+maxUploads]:
                                try:
                                    g_testThreadsRunning += 1
                                    client.upload_async(remote_path=f'{serverTargetFolder}/{file}',local_path=f'{targetDirectory}/{file}', callback=decreaseUploadCount)
                                except Exception as exception:
                                    logger.info(f'Error uploading {filename}: {exception}')
                                    g_testThreadsRunning -= 1
                                    self.assertTrue(False)
                            while g_testThreadsRunning > 0:
                                time.sleep(0.01)
                        endTime = datetime.now()
                    except:
                        logger.error(f'Error during async upload')
                        self.assertTrue(False)

                    # Calculate time to upload
                    uploadTime = (endTime - startTime).total_seconds()

                    davElements = client.list(serverTargetFolder)
                    logger.info(f'{davElements}')
                    davElements.pop(0)
                    startTime = datetime.now()

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)
                    
                    deleteTime = (datetime.now() - startTime).total_seconds()

                    lText = f'{fullnode} '
                    mText = f'Node {fe} - Up: {uploadTime:.1f}s at {expectedSize*1024/uploadTime:.1f} MB/s'
                    rText = f'Node {fe} - Del: {deleteTime:.1f}s at {expectedSize*1024/deleteTime:.1f} MB/s' 

                    message = f'{lText : <16}{mText : <40}{rText : <40}'
                    # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
                    logger.info(f'{message}')
                    g_davPerformanceResults.append(message)

        logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
        for message in g_davPerformanceResults:
            logger.info(f'{message}')

        logger.info(f'Done')
        pass

    def test_webdav_system(self):
        serverTargetFolder = 'selenium-system/largefiles'
        global logger, g_testThreadsRunning, g_davPerformanceResults
        g_davPerformanceResults.clear()

        if checkTestData() == False:
            logger.warning(f'File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

        numFiles = 4
        maxUploads = 1
        maxDeletes = 1
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                for fe in range(1,2):
                    nodebaseurl = drv.get_node_base_url(fullnode)
                    serverid = f'node{fe}.{nodebaseurl}'

                    logger.info(f'TestID: {fullnode}')

                    nodeuser = drv.get_seleniumuser(fullnode)
                    nodepwd = drv.get_seleniumuserpassword(fullnode)
                    url = drv.get_webdav_url(fullnode, nodeuser)
                    logger.info(f'URL: {url}')
                    options = {
                    'webdav_hostname': url,
                    'webdav_login' : nodeuser,
                    'webdav_password' : nodepwd,
                    'webdav_timeout': g_WebDavPerformance_timeout
                    }

                    client = Client(options)
                    client.session.cookies.set('SERVERID', serverid)

                    logger.info(client.list())
                    client.mkdir(serverTargetFolder)
                    files = []

                    for fileSize in fileSizes:
                        filename = f'{str(fileSize)}G.bin'
                        files.append(filename)

                    logger.info(f'List of local files {files}')

                    startTime = datetime.now()
                    logger.info(f'Async upload of {maxUploads} files concurrently')
                    try:
                        for i in range(0,numFiles,maxUploads):
                            x = i
                            logger.info(f'Batch upload node{fe} {files[x:x+maxUploads]}')
                            for file in files[x:x+maxUploads]:
                                try:
                                    g_testThreadsRunning += 1
                                    client.upload_async(remote_path=f'{serverTargetFolder}/{file}',local_path=f'{targetDirectory}/{file}', callback=decreaseUploadCount)
                                except Exception as exception:
                                    logger.info(f'Error uploading {filename}: {exception}')
                                    g_testThreadsRunning -= 1
                                    self.assertTrue(False)
                            while g_testThreadsRunning > 0:
                                time.sleep(0.01)
                        endTime = datetime.now()
                    except:
                        logger.error(f'Error during async upload')
                        self.assertTrue(False)

                    # Calculate time to upload
                    uploadTime = (endTime - startTime).total_seconds()

                    davElements = client.list(serverTargetFolder)
                    logger.info(f'{davElements}')
                    davElements.pop(0)
                    startTime = datetime.now()

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)
                    
                    deleteTime = (datetime.now() - startTime).total_seconds()

                    lText = f'{fullnode} '
                    mText = f'Node {fe} - Up: {uploadTime:.1f}s at {expectedSize*1024/uploadTime:.1f} MB/s'
                    rText = f'Node {fe} - Del: {deleteTime:.1f}s at {expectedSize*1024/deleteTime:.1f} MB/s' 

                    message = f'{lText : <16}{mText : <40}{rText : <40}'
                    # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
                    logger.info(f'{message}')
                    g_davPerformanceResults.append(message)

        logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
        for message in g_davPerformanceResults:
            logger.info(f'{message}')

        logger.info(f'Done')
        pass

    def test_webdav_personal(self):
        serverTargetFolder = 'selenium-personal/largefiles'
        global logger, g_testThreadsRunning, g_davPerformanceResults
        g_davPerformanceResults.clear()

        if checkTestData() == False:
            logger.warning(f'File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

        numFiles = 4
        maxUploads = 1
        maxDeletes = 1
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                for fe in range(1,2):
                    nodebaseurl = drv.get_node_base_url(fullnode)
                    serverid = f'node{fe}.{nodebaseurl}'

                    logger.info(f'TestID: {fullnode}')

                    nodeuser = drv.get_seleniumuser(fullnode)
                    nodepwd = drv.get_seleniumuserpassword(fullnode)
                    url = drv.get_webdav_url(fullnode, nodeuser)
                    logger.info(f'URL: {url}')
                    options = {
                    'webdav_hostname': url,
                    'webdav_login' : nodeuser,
                    'webdav_password' : nodepwd,
                    'webdav_timeout': g_WebDavPerformance_timeout
                    }

                    client = Client(options)
                    client.session.cookies.set('SERVERID', serverid)

                    logger.info(client.list())
                    client.mkdir(serverTargetFolder)
                    files = []

                    for fileSize in fileSizes:
                        filename = f'{str(fileSize)}G.bin'
                        files.append(filename)

                    logger.info(f'List of local files {files}')

                    startTime = datetime.now()
                    logger.info(f'Async upload of {maxUploads} files concurrently')
                    try:
                        for i in range(0,numFiles,maxUploads):
                            x = i
                            logger.info(f'Batch upload node{fe} {files[x:x+maxUploads]}')
                            for file in files[x:x+maxUploads]:
                                try:
                                    g_testThreadsRunning += 1
                                    client.upload_async(remote_path=f'{serverTargetFolder}/{file}',local_path=f'{targetDirectory}/{file}', callback=decreaseUploadCount)
                                except Exception as exception:
                                    logger.info(f'Error uploading {filename}: {exception}')
                                    g_testThreadsRunning -= 1
                                    self.assertTrue(False)
                            while g_testThreadsRunning > 0:
                                time.sleep(0.01)
                        endTime = datetime.now()
                    except:
                        logger.error(f'Error during async upload')
                        self.assertTrue(False)

                    # Calculate time to upload
                    uploadTime = (endTime - startTime).total_seconds()

                    davElements = client.list(serverTargetFolder)
                    logger.info(f'{davElements}')
                    davElements.pop(0)
                    startTime = datetime.now()

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)
                    
                    deleteTime = (datetime.now() - startTime).total_seconds()

                    lText = f'{fullnode} '
                    mText = f'Node {fe} - Up: {uploadTime:.1f}s at {expectedSize*1024/uploadTime:.1f} MB/s'
                    rText = f'Node {fe} - Del: {deleteTime:.1f}s at {expectedSize*1024/deleteTime:.1f} MB/s' 

                    message = f'{lText : <16}{mText : <40}{rText : <40}'
                    # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
                    logger.info(f'{message}')
                    g_davPerformanceResults.append(message)

        logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
        for message in g_davPerformanceResults:
            logger.info(f'{message}')

        logger.info(f'Done')
        pass

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
