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
fileSizes=[1,4,8,28] # Only GB, larger than 1
fileNames=[] # Array with the files 
useTmpFolder = True # As a default, use the temp folder, alternatively use home folder of user that is testing

def deleteTestData():
    for fileSize in fileSizes:
        filename = f'{str(fileSize)}G.bin'
        pathname = f'{tempfile.gettempdir()}/{filename}'            # Check if the file exists in the temp directory
        if Path(pathname).exists():
            logger.info(f'Removing file {pathname}')
            os.remove(pathname)
        pathname = f'{Path.home()}/{filename}'                      # Check if the file exists in the home directory
        if Path(pathname).exists():
            logger.info(f'Removing file {pathname}')
            os.remove(pathname)

def checkTestData():
    logpath = f'{tempfile.gettempdir()}/*G.bin'
    totalSize = 0

    for full_path in glob.glob(logpath):
        totalSize += Path(full_path).stat().st_size / GB
    if totalSize == 0:
        logger.info(f'No test data found in /tmp')
        return False

    expectedSize = 0
    for size in fileSizes:
        expectedSize += size

    if totalSize != expectedSize:
        logger.warning(f'Total size of existing files does not match, {totalSize} != {expectedSize}')
        return False

    for fileSize in fileSizes:
        filename = f'{str(fileSize)}G.bin'
        pathname = f'{tempfile.gettempdir()}/{filename}'            # Check if the file exists in the temp directory
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
    tmpFree = shutil.disk_usage('/tmp').free / GB
    logger.info(f'/tmp has {tmpFree:.2f} GB free')
    if tmpFree > 42:
        useTmp = True
        logger.info(f'Using /tmp for temporary files')
    else:
        logger.error(f'Not enough space in /tmp')

    for fileSize in fileSizes:
        filename = f'{str(fileSize)}G.bin'
        pathname = f'{tempfile.gettempdir()}/{filename}'
        logger.info(f'Generating file {pathname}')
        cmd=f'head -c {fileSize}G /dev/urandom > {pathname}'
        logger.info(f'Running subprocess {cmd}')
        os.system(cmd)
        # subprocess.run(cmd, stdout = subprocess.DEVNULL)        

def excepthook(args):
    logger.error(f'Threading exception: {args}')
    decreaseUploadCount()
    sys.excepthook(*sys.exc_info())

threading.excepthook = excepthook

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

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
