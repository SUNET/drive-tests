""" Testing WebDavPerformance functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import tempfile
import requests
from requests.auth import HTTPBasicAuth
import json
import os
from webdav3.client import Client
from webdav3.exceptions import WebDavException
import logging
import threading
import time
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

def decreaseUploadCount():
    global g_testThreadsRunning
    g_testThreadsRunning -= 1

def webdavUpload(client, local_path, remote_path):
    global logger, g_testThreadsRunning
    logger.info(f'Upload {local_path}')
    if client == None:
        logger.error(f'No client provided')
        return
    if local_path == None:
        logger.error(f'No filename provided')
        return
    if remote_path == None:
        logger.error(f'No target filename provided')
        return
    client.upload_sync(remote_path=remote_path,local_path=local_path)
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

class TestWebDavPerformance(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_basic_performance(self):
        global logger, g_testThreadsRunning, g_davPerformanceResults
        numFiles = 100
        maxUploads=8
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
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
                logger.info(client.list())
                client.mkdir('performance')

                logger.info(f'Generate local files')
                files = []
                for i in range(0,numFiles):
                    filename = f'{fullnode}{str(i)}.bin'
                    pathname = f'{tempfile.gettempdir()}/{filename}'
                    fileSizeInBytes = 102400
                    with open(pathname, 'wb') as fout:
                        fout.write(os.urandom(fileSizeInBytes))
                    files.append(filename)

                startTime = datetime.now()
                logger.info(f'Async upload of {maxUploads} files concurrently')
                try:
                    for i in range(0,numFiles,maxUploads):
                        x = i
                        logger.info(f'Batch upload {files[x:x+maxUploads]}')
                        for file in files[x:x+maxUploads]:
                            try:
                                g_testThreadsRunning += 1
                                client.upload_async(remote_path=f'performance/{file}',local_path=f'{tempfile.gettempdir()}/{file}', callback=decreaseUploadCount)
                            except WebDavException as exception:
                                logger.info(f'Error uploading {filename}: {exception}')
                                g_testThreadsRunning -= 1
                        while g_testThreadsRunning > 0:
                            time.sleep(0.01)
                    endTime = datetime.now()
                except:
                    logger.error(f'Error during async upload')

                # Calculate time to upload
                uploadTime = (endTime - startTime).total_seconds()

                # Remove the temporary files
                logger.info(f'Remove temporary files')
                for i in range(0,numFiles):
                    filename = f'{tempfile.gettempdir()}/{fullnode}{str(i)}.bin'
                    os.remove(filename)

                davElements = client.list('performance')
                logger.info(f'{davElements}')
                davElements.pop(0)
                startTime = datetime.now()

                start = 0
                end = len(davElements)
                maxDeletes = 8
                for i in range(start,end,maxDeletes):
                    x = i
                    logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                    for element in davElements[x:x+maxDeletes]:
                        t = threading.Thread(target=client.clean, args=['performance/' + element])
                        t.start()
                    while threading.active_count() > 1:
                        time.sleep(0.01)

                # This works for single threaded delete
                # for element in davElements:
                #     logger.info(f'Delete {element}')
                #     try:
                #         client.clean('performance/' + element)
                #     except:
                #         logger.info(f'Error deleting {element}')
                
                deleteTime = (datetime.now() - startTime).total_seconds()

                message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
                logger.info(f'{message}')
                g_davPerformanceResults.append(message)

        for message in g_davPerformanceResults:
            logger.info(f'{message}')

        logger.info(f'Done')
        pass


if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
