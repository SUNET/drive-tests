""" Testing WebDavPerformance functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import tempfile
import os
import glob
from pathlib import Path
import shutil
from webdav3.client import Client
import logging
import threading
import time
import sys
from datetime import datetime
import xmlrunner

import sunetnextcloud

g_maxCheck = 10
g_WebDavPerformance_timeout = 3600
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

drv = sunetnextcloud.TestTarget()

KB = 1024
MB = 1024 * KB
GB = 1024 * MB
fileSizes=[1,2,4,8] # Defined by 
fileSizeSuffix=drv.testfilesize
fileNames=[] # Array with the files env NextcloudTestFileSize
targetDirectory=f'{tempfile.gettempdir()}/largefiles'
threadingException = False

expectedSize = 0
for size in fileSizes:
    expectedSize += size

def threading_exception(args):
    global threadingException
    logger.error(f'Threading exception: {args}')
    decreaseUploadCount()
    threadingException = True
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
    logpath = f'{targetDirectory}/*{fileSizeSuffix}.bin'
    totalSize = 0

    for full_path in glob.glob(logpath):
        totalSize += Path(full_path).stat().st_size / GB
    if totalSize == 0:
        logger.info(f'No test data found in {targetDirectory}')
        return False
    
    return True

    if totalSize != expectedSize:
        logger.warning(f'Total size of existing files does not match, {totalSize} != {expectedSize}')
        return False

    for fileSize in fileSizes:
        filename = f'{str(fileSize)}{fileSizeSuffix}.bin'
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
        filename = f'{str(fileSize)}{fileSizeSuffix}.bin'
        pathname = f'{targetDirectory}/{filename}'
        logger.info(f'Generating file {pathname}')
        cmd=f'head -c {fileSize}{fileSizeSuffix} /dev/urandom > {pathname}'
        logger.info(f'Running subprocess {cmd}')
        os.system(cmd)

def decreaseUploadCount():
    global g_testThreadsRunning
    g_testThreadsRunning -= 1

def webdavUpload(client, local_path, remote_path):
    global logger, g_testThreadsRunning
    logger.info(f'Upload {local_path}')
    if client == None:
        logger.error('No client provided')
        decreaseUploadCount()
        return
    if local_path == None:
        logger.error('No filename provided')
        decreaseUploadCount()
        return
    if remote_path == None:
        logger.error('No target filename provided')
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
        logger.error('No client provided')
        return
    if filename == None:
        logger.error('No filename provided')
        return
    logger.info(f'Cleaning {filename}')
    client.clean(filename)

class TestLargeFilePerformance(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_testdata(self):        
        if not checkTestData():
            logger.warning('File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

        self.assertTrue(checkTestData())
        pass

    # def test_webdav_home(self):
    #     serverTargetFolder = 'selenium-home/largefiles'
    #     global logger, g_testThreadsRunning, g_davPerformanceResults
    #     g_davPerformanceResults.clear()

    #     if checkTestData() == False:
    #         logger.warning(f'File size check failed, regenerating test data')
    #         deleteTestData()
    #         generateTestData()

    #     numFiles = 4
    #     maxUploads = 1
    #     maxDeletes = 1
    #     drv = sunetnextcloud.TestTarget()
    #     for fullnode in drv.fullnodes:
    #         with self.subTest(mynode=fullnode):
    #             for fe in range(1,2):
    #                 nodebaseurl = drv.get_node_base_url(fullnode)
    #                 serverid = f'node{fe}.{nodebaseurl}'
    #                 logger.info(f'TestID: {fullnode}')
    #                 nodeuser = drv.get_seleniumuser(fullnode)
    #                 nodepwd = drv.get_seleniumuserpassword(fullnode)
    #                 url = drv.get_webdav_url(fullnode, nodeuser)
    #                 logger.info(f'URL: {url}')
    #                 options = {
    #                 'webdav_hostname': url,
    #                 'webdav_login' : nodeuser,
    #                 'webdav_password' : nodepwd,
    #                 'webdav_timeout': g_WebDavPerformance_timeout
    #                 }

    #                 client = Client(options)
    #                 client.session.cookies.set('SERVERID', serverid)

    #                 logger.info(client.list())
    #                 client.mkdir(serverTargetFolder)
    #                 files = []

    #                 for fileSize in fileSizes:
    #                     filename = f'{str(fileSize)}{fileSizeSuffix}.bin'
    #                     files.append(filename)

    #                 logger.info(f'List of local files {files}')

    #                 startTime = datetime.now()
    #                 logger.info(f'Async upload of {maxUploads} files concurrently')
    #                 try:
    #                     for i in range(0,numFiles,maxUploads):
    #                         x = i
    #                         logger.info(f'Batch upload node{fe} {files[x:x+maxUploads]}')
    #                         for file in files[x:x+maxUploads]:
    #                             try:
    #                                 g_testThreadsRunning += 1
    #                                 client.upload_async(remote_path=f'{serverTargetFolder}/{file}',local_path=f'{targetDirectory}/{file}', callback=decreaseUploadCount)
    #                             except Exception as exception:
    #                                 logger.info(f'Error uploading {filename}: {exception}')
    #                                 g_testThreadsRunning -= 1
    #                                 self.assertTrue(False)
    #                         while g_testThreadsRunning > 0:
    #                             time.sleep(0.01)
    #                     endTime = datetime.now()
    #                 except:
    #                     logger.error(f'Error during async upload')
    #                     self.assertTrue(False)

    #                 # Calculate time to upload
    #                 uploadTime = (endTime - startTime).total_seconds()

    #                 davElements = client.list(serverTargetFolder)
    #                 logger.info(f'{davElements}')
    #                 davElements.pop(0)
    #                 startTime = datetime.now()

    #                 for i in range(0,len(davElements),maxDeletes):
    #                     x = i
    #                     logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
    #                     for element in davElements[x:x+maxDeletes]:
    #                         t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
    #                         t.start()
    #                     while threading.active_count() > 1:
    #                         time.sleep(0.01)
                    
    #                 deleteTime = (datetime.now() - startTime).total_seconds()

    #                 lText = f'{fullnode} '
    #                 mText = f'Node {fe} - Up: {uploadTime:.1f}s at {expectedSize*1024/uploadTime:.1f} MB/s'
    #                 rText = f'Node {fe} - Del: {deleteTime:.1f}s at {expectedSize*1024/deleteTime:.1f} MB/s' 

    #                 message = f'{lText : <16}{mText : <40}{rText : <40}'
    #                 # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
    #                 logger.info(f'{message}')
    #                 g_davPerformanceResults.append(message)

    #     logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
    #     for message in g_davPerformanceResults:
    #         logger.info(f'{message}')

    #     self.assertFalse(threadingException)

    #     logger.info(f'Done')
    #     pass

    # def test_webdav_system(self):
    #     serverTargetFolder = 'selenium-system/largefiles'
    #     global logger, g_testThreadsRunning, g_davPerformanceResults
    #     g_davPerformanceResults.clear()

    #     if checkTestData() == False:
    #         logger.warning(f'File size check failed, regenerating test data')
    #         deleteTestData()
    #         generateTestData()

    #     numFiles = 4
    #     maxUploads = 1
    #     maxDeletes = 1
    #     drv = sunetnextcloud.TestTarget()
    #     for fullnode in drv.fullnodes:
    #         with self.subTest(mynode=fullnode):
    #             for fe in range(1,2):
    #                 nodebaseurl = drv.get_node_base_url(fullnode)
    #                 serverid = f'node{fe}.{nodebaseurl}'

    #                 logger.info(f'TestID: {fullnode}')

    #                 nodeuser = drv.get_seleniumuser(fullnode)
    #                 nodepwd = drv.get_seleniumuserpassword(fullnode)
    #                 url = drv.get_webdav_url(fullnode, nodeuser)
    #                 logger.info(f'URL: {url}')
    #                 options = {
    #                 'webdav_hostname': url,
    #                 'webdav_login' : nodeuser,
    #                 'webdav_password' : nodepwd,
    #                 'webdav_timeout': g_WebDavPerformance_timeout
    #                 }

    #                 client = Client(options)
    #                 client.session.cookies.set('SERVERID', serverid)

    #                 logger.info(client.list())
    #                 client.mkdir(serverTargetFolder)
    #                 files = []

    #                 for fileSize in fileSizes:
    #                     filename = f'{str(fileSize)}{fileSizeSuffix}.bin'
    #                     files.append(filename)

    #                 logger.info(f'List of local files {files}')

    #                 startTime = datetime.now()
    #                 logger.info(f'Async upload of {maxUploads} files concurrently')
    #                 try:
    #                     for i in range(0,numFiles,maxUploads):
    #                         x = i
    #                         logger.info(f'Batch upload node{fe} {files[x:x+maxUploads]}')
    #                         for file in files[x:x+maxUploads]:
    #                             try:
    #                                 g_testThreadsRunning += 1
    #                                 client.upload_async(remote_path=f'{serverTargetFolder}/{file}',local_path=f'{targetDirectory}/{file}', callback=decreaseUploadCount)
    #                             except Exception as exception:
    #                                 logger.info(f'Error uploading {filename}: {exception}')
    #                                 g_testThreadsRunning -= 1
    #                                 self.assertTrue(False)
    #                         while g_testThreadsRunning > 0:
    #                             time.sleep(0.01)
    #                     endTime = datetime.now()
    #                 except:
    #                     logger.error(f'Error during async upload')
    #                     self.assertTrue(False)

    #                 # Calculate time to upload
    #                 uploadTime = (endTime - startTime).total_seconds()

    #                 davElements = client.list(serverTargetFolder)
    #                 logger.info(f'{davElements}')
    #                 davElements.pop(0)
    #                 startTime = datetime.now()

    #                 for i in range(0,len(davElements),maxDeletes):
    #                     x = i
    #                     logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
    #                     for element in davElements[x:x+maxDeletes]:
    #                         t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
    #                         t.start()
    #                     while threading.active_count() > 1:
    #                         time.sleep(0.01)
                    
    #                 deleteTime = (datetime.now() - startTime).total_seconds()

    #                 lText = f'{fullnode} '
    #                 mText = f'Node {fe} - Up: {uploadTime:.1f}s at {expectedSize*1024/uploadTime:.1f} MB/s'
    #                 rText = f'Node {fe} - Del: {deleteTime:.1f}s at {expectedSize*1024/deleteTime:.1f} MB/s' 

    #                 message = f'{lText : <16}{mText : <40}{rText : <40}'
    #                 # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
    #                 logger.info(f'{message}')
    #                 g_davPerformanceResults.append(message)

    #     logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
    #     for message in g_davPerformanceResults:
    #         logger.info(f'{message}')

    #     self.assertFalse(threadingException)

    #     logger.info(f'Done')
    #     pass

    # def test_webdav_personal(self):
    #     serverTargetFolder = 'selenium-personal/largefiles'
    #     global logger, g_testThreadsRunning, g_davPerformanceResults
    #     g_davPerformanceResults.clear()

    #     if checkTestData() == False:
    #         logger.warning(f'File size check failed, regenerating test data')
    #         deleteTestData()
    #         generateTestData()

    #     numFiles = 4
    #     maxUploads = 1
    #     maxDeletes = 1
    #     drv = sunetnextcloud.TestTarget()
    #     for fullnode in drv.fullnodes:
    #         with self.subTest(mynode=fullnode):
    #             for fe in range(1,2):
    #                 nodebaseurl = drv.get_node_base_url(fullnode)
    #                 serverid = f'node{fe}.{nodebaseurl}'

    #                 logger.info(f'TestID: {fullnode}')

    #                 nodeuser = drv.get_seleniumuser(fullnode)
    #                 nodepwd = drv.get_seleniumuserpassword(fullnode)
    #                 url = drv.get_webdav_url(fullnode, nodeuser)
    #                 logger.info(f'URL: {url}')
    #                 options = {
    #                 'webdav_hostname': url,
    #                 'webdav_login' : nodeuser,
    #                 'webdav_password' : nodepwd,
    #                 'webdav_timeout': g_WebDavPerformance_timeout
    #                 }

    #                 client = Client(options)
    #                 client.session.cookies.set('SERVERID', serverid)

    #                 logger.info(client.list())
    #                 client.mkdir(serverTargetFolder)
    #                 files = []

    #                 for fileSize in fileSizes:
    #                     filename = f'{str(fileSize)}{fileSizeSuffix}.bin'
    #                     files.append(filename)

    #                 logger.info(f'List of local files {files}')

    #                 startTime = datetime.now()
    #                 logger.info(f'Async upload of {maxUploads} files concurrently')
    #                 try:
    #                     for i in range(0,numFiles,maxUploads):
    #                         x = i
    #                         logger.info(f'Batch upload node{fe} {files[x:x+maxUploads]}')
    #                         for file in files[x:x+maxUploads]:
    #                             try:
    #                                 g_testThreadsRunning += 1
    #                                 client.upload_async(remote_path=f'{serverTargetFolder}/{file}',local_path=f'{targetDirectory}/{file}', callback=decreaseUploadCount)
    #                             except Exception as exception:
    #                                 logger.info(f'Error uploading {filename}: {exception}')
    #                                 g_testThreadsRunning -= 1
    #                                 self.assertTrue(False)
    #                         while g_testThreadsRunning > 0:
    #                             time.sleep(0.01)
    #                     endTime = datetime.now()
    #                 except:
    #                     logger.error(f'Error during async upload')
    #                     self.assertTrue(False)

    #                 # Calculate time to upload
    #                 uploadTime = (endTime - startTime).total_seconds()

    #                 davElements = client.list(serverTargetFolder)
    #                 logger.info(f'{davElements}')
    #                 davElements.pop(0)
    #                 startTime = datetime.now()

    #                 for i in range(0,len(davElements),maxDeletes):
    #                     x = i
    #                     logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
    #                     for element in davElements[x:x+maxDeletes]:
    #                         t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
    #                         t.start()
    #                     while threading.active_count() > 1:
    #                         time.sleep(0.01)
                    
    #                 deleteTime = (datetime.now() - startTime).total_seconds()

    #                 lText = f'{fullnode} '
    #                 mText = f'Node {fe} - Up: {uploadTime:.1f}s at {expectedSize*1024/uploadTime:.1f} MB/s'
    #                 rText = f'Node {fe} - Del: {deleteTime:.1f}s at {expectedSize*1024/deleteTime:.1f} MB/s' 

    #                 message = f'{lText : <16}{mText : <40}{rText : <40}'
    #                 # message = f'{fullnode} - Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file'
    #                 logger.info(f'{message}')
    #                 g_davPerformanceResults.append(message)

    #     logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
    #     for message in g_davPerformanceResults:
    #         logger.info(f'{message}')

    #     self.assertFalse(threadingException)

    #     logger.info(f'Done')
    #     pass

    # def test_rclone_home(self):
    #     serverTargetFolder = 'selenium-home/rclone'
    #     global logger, g_testThreadsRunning, g_davPerformanceResults
    #     g_davPerformanceResults.clear()

    #     if checkTestData() == False:
    #         logger.warning(f'File size check failed, regenerating test data')
    #         deleteTestData()
    #         generateTestData()

    #     # Commands to run for a basic sync
    #     # rclone copy /tmp/largefiles/ selenium-sunet-test:selenium-home/rclone --progress
    #     # rclone delete selenium-sunet-test:selenium-home/rclone
    #     # rclone rmdir selenium-sunet-test:selenium-home/rclone

    #     logger.info(f'Done')
    #     pass

    def test_nextcloudcmd_home(self):
        serverTargetFolder = 'selenium-home/nextcloudcmd'

        # Command to run for a basic sync
        # rm /tmp/largefiles/.sync_*
        # nextcloudcmd --non-interactive --silent --path selenium-home/nextcloudcmd -u ${NEXTCLOUD_SELENIUM_USER_SUNET_TEST} -p ${NEXTCLOUD_SELENIUM_PASSWORD_SUNET_TEST} /tmp/largefiles https://sunet.drive.test.sunet.se 
        global logger, g_testThreadsRunning, g_davPerformanceResults
        g_davPerformanceResults.clear()

        if not checkTestData():
            logger.warning('File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

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

                    client.mkdir(serverTargetFolder)
                    davElements = client.list(serverTargetFolder)
                    davElements.pop(0)

                    logger.info(f'Precleaning target folder {davElements}')

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)

                    logger.info(f'Deleting local temp files in {targetDirectory} before sync')
                    cmd = f'rm {targetDirectory}/.*'
                    os.system(cmd)

                    logger.info(f'Deleting local conflicted copies in {targetDirectory} before sync')
                    cmd = f'rm {targetDirectory}/*conflicted*'
                    os.system(cmd)

                    cmd = f'nextcloudcmd --non-interactive --path {serverTargetFolder} -u ${{NEXTCLOUD_SELENIUM_USER_{fullnode.upper()}_{drv.target.upper()}}} -p ${{NEXTCLOUD_SELENIUM_PASSWORD_{fullnode.upper()}_{drv.target.upper()}}} {targetDirectory} https://{drv.get_node_base_url(fullnode)}'
                    logger.info(f'Executing {cmd}')
                    os.system(cmd)

                    logger.info(f'Deleting local temp files in {targetDirectory} after sync')
                    cmd = f'rm {targetDirectory}/.*'
                    os.system(cmd)

                    logger.info(f'Deleting local conflicted copies in {targetDirectory} after sync')
                    cmd = f'rm {targetDirectory}/*conflicted*'
                    os.system(cmd)

                    # cmd = ['nextcloudcmd','--non-interactive','--path',serverTargetFolder,'-u',nodeuser,'-p',nodepwd,targetDirectory,f'https://{drv.get_node_base_url(fullnode)}']

                    # print(cmd)

                    # process = subprocess.Popen(
                    #     cmd,
                    #     encoding='utf-8',
                    #     stdin=subprocess.PIPE,
                    #     stdout=subprocess.PIPE,
                    # )

                    # while(True):
                    #     returncode = process.poll()
                    #     if returncode is None:
                    #         # You describe what is going on.
                    #         # You can describe the process every time the time elapses as needed.
                    #         # print("running process")
                    #         time.sleep(0.01)
                    #         data = process.stdout
                    #         if data:
                    #             # If there is any response, describe it here.
                    #             # You need to use readline () or readlines () properly, depending on how the process responds.
                    #             msg_line = data.readline()
                    #             print(msg_line)
                    #         err = process.stderr
                    #         if err:
                    #             # If there is any error response, describe it here.
                    #             msg_line = err.readline()
                    #             print(msg_line)
                    #     else:
                    #         print(returncode)
                    #         break

                    # # Describes the processing after the process ends.
                    # logger.info("Nextcloudcmd terminated")

                    davElements = client.list(serverTargetFolder)
                    davElements.pop(0)
                    davElements.sort()
                    
                    localElements = os.listdir(targetDirectory)
                    localElements.sort()
                    logger.info(f'Checking davElements and localElements: {davElements} - {localElements}')
                    self.assertEqual(len(davElements), len(localElements))
                    # Compare the elements
                    for index in range(0,len(davElements)):
                        self.assertEqual(davElements[index], localElements[index])

                    logger.info(f'Local and remote directories contain the same files {davElements} and {os.listdir(targetDirectory)}')
                    logger.info(f'Deleting remote files: {davElements}')

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)

                    logger.info('Done')

    def test_nextcloudcmd_system(self):
        serverTargetFolder = 'selenium-system/nextcloudcmd'

        # Command to run for a basic sync
        # rm /tmp/largefiles/.sync_*
        # nextcloudcmd --non-interactive --silent --path selenium-home/nextcloudcmd -u ${NEXTCLOUD_SELENIUM_USER_SUNET_TEST} -p ${NEXTCLOUD_SELENIUM_PASSWORD_SUNET_TEST} /tmp/largefiles https://sunet.drive.test.sunet.se 
        global logger, g_testThreadsRunning, g_davPerformanceResults
        g_davPerformanceResults.clear()

        if not checkTestData():
            logger.warning('File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

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

                    client.mkdir(serverTargetFolder)
                    davElements = client.list(serverTargetFolder)
                    davElements.pop(0)

                    logger.info(f'Precleaning target folder {davElements}')

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)

                    logger.info(f'Deleting local temp files in {targetDirectory} before sync')
                    cmd = f'rm {targetDirectory}/.*'
                    os.system(cmd)

                    logger.info(f'Deleting local conflicted copies in {targetDirectory} before sync')
                    cmd = f'rm {targetDirectory}/*conflicted*'
                    os.system(cmd)

                    cmd = f'nextcloudcmd --non-interactive --path {serverTargetFolder} -u ${{NEXTCLOUD_SELENIUM_USER_{fullnode.upper()}_{drv.target.upper()}}} -p ${{NEXTCLOUD_SELENIUM_PASSWORD_{fullnode.upper()}_{drv.target.upper()}}} {targetDirectory} https://{drv.get_node_base_url(fullnode)}'
                    logger.info(f'Executing {cmd}')
                    os.system(cmd)

                    logger.info(f'Deleting local temp files in {targetDirectory} after sync')
                    cmd = f'rm {targetDirectory}/.*'
                    os.system(cmd)

                    logger.info(f'Deleting local conflicted copies in {targetDirectory} after sync')
                    cmd = f'rm {targetDirectory}/*conflicted*'
                    os.system(cmd)

                    # cmd = ['nextcloudcmd','--non-interactive','--path',serverTargetFolder,'-u',nodeuser,'-p',nodepwd,targetDirectory,f'https://{drv.get_node_base_url(fullnode)}']

                    # print(cmd)

                    # process = subprocess.Popen(
                    #     cmd,
                    #     encoding='utf-8',
                    #     stdin=subprocess.PIPE,
                    #     stdout=subprocess.PIPE,
                    # )

                    # while(True):
                    #     returncode = process.poll()
                    #     if returncode is None:
                    #         # You describe what is going on.
                    #         # You can describe the process every time the time elapses as needed.
                    #         # print("running process")
                    #         time.sleep(0.01)
                    #         data = process.stdout
                    #         if data:
                    #             # If there is any response, describe it here.
                    #             # You need to use readline () or readlines () properly, depending on how the process responds.
                    #             msg_line = data.readline()
                    #             print(msg_line)
                    #         err = process.stderr
                    #         if err:
                    #             # If there is any error response, describe it here.
                    #             msg_line = err.readline()
                    #             print(msg_line)
                    #     else:
                    #         print(returncode)
                    #         break

                    # # Describes the processing after the process ends.
                    # logger.info("Nextcloudcmd terminated")

                    davElements = client.list(serverTargetFolder)
                    davElements.pop(0)
                    davElements.sort()
                    
                    localElements = os.listdir(targetDirectory)
                    localElements.sort()
                    self.assertEqual(len(davElements), len(localElements))
                    # Compare the elements
                    for index in range(0,len(davElements)):
                        self.assertEqual(davElements[index], localElements[index])

                    logger.info(f'Local and remote directories contain the same files {davElements} and {os.listdir(targetDirectory)}')
                    logger.info(f'Deleting remote files: {davElements}')

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)

                    logger.info('Done')

    def test_nextcloudcmd_personal(self):
        serverTargetFolder = 'selenium-home/nextcloudcmd'

        # Command to run for a basic sync
        # rm /tmp/largefiles/.sync_*
        # nextcloudcmd --non-interactive --silent --path selenium-home/nextcloudcmd -u ${NEXTCLOUD_SELENIUM_USER_SUNET_TEST} -p ${NEXTCLOUD_SELENIUM_PASSWORD_SUNET_TEST} /tmp/largefiles https://sunet.drive.test.sunet.se 
        global logger, g_testThreadsRunning, g_davPerformanceResults
        g_davPerformanceResults.clear()

        if not checkTestData():
            logger.warning('File size check failed, regenerating test data')
            deleteTestData()
            generateTestData()

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

                    client.mkdir(serverTargetFolder)
                    davElements = client.list(serverTargetFolder)
                    davElements.pop(0)

                    logger.info(f'Precleaning target folder {davElements}')

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)

                    logger.info(f'Deleting local temp files in {targetDirectory} before sync')
                    cmd = f'rm {targetDirectory}/.*'
                    os.system(cmd)

                    logger.info(f'Deleting local conflicted copies in {targetDirectory} before sync')
                    cmd = f'rm {targetDirectory}/*conflicted*'
                    os.system(cmd)

                    cmd = f'nextcloudcmd --non-interactive --path {serverTargetFolder} -u ${{NEXTCLOUD_SELENIUM_USER_{fullnode.upper()}_{drv.target.upper()}}} -p ${{NEXTCLOUD_SELENIUM_PASSWORD_{fullnode.upper()}_{drv.target.upper()}}} {targetDirectory} https://{drv.get_node_base_url(fullnode)}'
                    logger.info(f'Executing {cmd}')
                    os.system(cmd)

                    logger.info(f'Deleting local temp files in {targetDirectory} after sync')
                    cmd = f'rm {targetDirectory}/.*'
                    os.system(cmd)

                    logger.info(f'Deleting local conflicted copies in {targetDirectory} after sync')
                    cmd = f'rm {targetDirectory}/*conflicted*'
                    os.system(cmd)

                    # cmd = ['nextcloudcmd','--non-interactive','--path',serverTargetFolder,'-u',nodeuser,'-p',nodepwd,targetDirectory,f'https://{drv.get_node_base_url(fullnode)}']

                    # print(cmd)

                    # process = subprocess.Popen(
                    #     cmd,
                    #     encoding='utf-8',
                    #     stdin=subprocess.PIPE,
                    #     stdout=subprocess.PIPE,
                    # )

                    # while(True):
                    #     returncode = process.poll()
                    #     if returncode is None:
                    #         # You describe what is going on.
                    #         # You can describe the process every time the time elapses as needed.
                    #         # print("running process")
                    #         time.sleep(0.01)
                    #         data = process.stdout
                    #         if data:
                    #             # If there is any response, describe it here.
                    #             # You need to use readline () or readlines () properly, depending on how the process responds.
                    #             msg_line = data.readline()
                    #             print(msg_line)
                    #         err = process.stderr
                    #         if err:
                    #             # If there is any error response, describe it here.
                    #             msg_line = err.readline()
                    #             print(msg_line)
                    #     else:
                    #         print(returncode)
                    #         break

                    # # Describes the processing after the process ends.
                    # logger.info("Nextcloudcmd terminated")

                    davElements = client.list(serverTargetFolder)
                    davElements.pop(0)
                    davElements.sort()
                    
                    localElements = os.listdir(targetDirectory)
                    localElements.sort()
                    self.assertEqual(len(davElements), len(localElements))
                    # Compare the elements
                    for index in range(0,len(davElements)):
                        self.assertEqual(davElements[index], localElements[index])

                    logger.info(f'Local and remote directories contain the same files {davElements} and {os.listdir(targetDirectory)}')
                    logger.info(f'Deleting remote files: {davElements}')

                    for i in range(0,len(davElements),maxDeletes):
                        x = i
                        logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
                        for element in davElements[x:x+maxDeletes]:
                            t = threading.Thread(target=client.clean, args=[f'{serverTargetFolder}/' + element])
                            t.start()
                        while threading.active_count() > 1:
                            time.sleep(0.01)

                    logger.info('Done')

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
