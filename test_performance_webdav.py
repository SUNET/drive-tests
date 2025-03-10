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

class TestWebDavPerformance(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_basic_performance(self):
        global logger, g_testThreadsRunning, g_davPerformanceResults
        numFiles = 100
        maxUploads = 2
        maxDeletes = 4
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                for fe in range(1,4):
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

                    for i in range(0,len(davElements),maxDeletes):
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

                    lText = f'{fullnode} '
                    mText = f'Node {fe} - Up: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file'
                    rText = f'Node {fe} - Del: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file' 

                    message = f'{lText : <16}{mText : <40}{rText : <40}'
                    # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
                    logger.info(f'{message}')
                    g_davPerformanceResults.append(message)

        logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
        for message in g_davPerformanceResults:
            logger.info(f'{message}')

        logger.info(f'Done')
        pass

    def test_file_sizes(self):
        global logger, g_testThreadsRunning, g_davPerformanceResults
        numFiles = 1
        maxUploads = 1
        maxDeletes = 1
        # fileSizes=[1,10,100,1024,10240,102400,1024000,10240000,102400000,204800000,409600000]
        # fileSizes=[1024,2048,4096]
        fileSizes=[102400000,204800000,409600000]

        header = f'{"Size" : <16}'
        for size in fileSizes:
            header += f'{size : <10}'
        g_davPerformanceResults.append(header)


        logger.info(f'{header}')

        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            result = f'{fullnode : <16}'
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
                targetDir='selenium-system/TestWebDavPerformance_file_sizes'
                client.mkdir(targetDir)

                for fileSize in fileSizes:

                    logger.info(f'Generate local files')
                    files = []
                    for i in range(0,numFiles):
                        filename = f'{fullnode}{str(i)}_{str(fileSize)}.bin'
                        pathname = f'{tempfile.gettempdir()}/{filename}'
                        fileSizeInBytes = fileSize
                        with open(pathname, 'wb') as fout:
                            fout.write(os.urandom(fileSizeInBytes))
                        files.append(filename)

                    startTime = datetime.now()
                    logger.info(f'Async upload of {maxUploads} files concurrently')
                    try:
                        for i in range(0,numFiles,maxUploads):
                            x = i
                            logger.info(f'Batch upload {files[x:x+maxUploads]} to {targetDir}')
                            for file in files[x:x+maxUploads]:
                                try:
                                    g_testThreadsRunning += 1
                                    client.upload_async(remote_path=f'{targetDir}/{file}',local_path=f'{tempfile.gettempdir()}/{file}', callback=decreaseUploadCount)
                                    # client.upload_sync(remote_path=f'{targetDir}/{file}',local_path=f'{tempfile.gettempdir()}/{file}', callback=decreaseUploadCount)
                                except WebDavException as exception:
                                    logger.error(f'Error uploading {filename}: {exception}')
                                    g_testThreadsRunning -= 1
                            while g_testThreadsRunning > 0:
                                time.sleep(0.01)
                        endTime = datetime.now()
                    except Exception as error:
                        logger.error(f'Error during async upload: {error}')

                    # Calculate time to upload
                    uploadTime = (endTime - startTime).total_seconds()

                    # Remove the temporary files
                    try:
                        logger.info(f'Remove temporary files')
                        for i in range(0,numFiles):
                            filename = f'{tempfile.gettempdir()}/{fullnode}{str(i)}_{str(fileSize)}.bin'
                            os.remove(filename)
                    except Exception as error:
                        logger.error(f'Error deleting local file: {error}')

                    davElements = client.list(targetDir)
                    logger.info(f'{davElements}')
                    davElements.pop(0)
                    startTime = datetime.now()

                    # Batch delete files
                    # for i in range(0,len(davElements),maxDeletes):
                    #     x = i
                    #     logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                    #     for element in davElements[x:x+maxDeletes]:
                    #         t = threading.Thread(target=client.clean, args=[f'{targetDir}/{element}'])
                    #         t.start()
                    #     while threading.active_count() > 1:
                    #         time.sleep(0.01)

                    # This works for single threaded delete
                    # for element in davElements:
                    #     logger.info(f'Delete {element}')
                    #     try:
                    #         client.clean('performance/' + element)
                    #     except:
                    #         logger.info(f'Error deleting {element}')
                    
                    deleteTime = (datetime.now() - startTime).total_seconds()

                    result += f'{uploadTime:<10.1f}'

                    # lText = f'{fullnode} '
                    # mText = f'Size: {fileSize}'
                    # rText = f'Upload: {uploadTime:.1f}s' 

                    # message = f'{lText : <16}{mText : <40}{rText : <40}'
                    # # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
                    # logger.info(f'{message}')

                g_davPerformanceResults.append(result)

        logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
        for message in g_davPerformanceResults:
            logger.info(f'{message}')

        logger.info(f'Done')
        pass


if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
