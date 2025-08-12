""" Nextcloud WebDAV stress test against a locally deployed instance. 
Author: Richard Freitag <freitag@sunet.se>
"""

import tempfile
import os
from webdav3.client import Client
from webdav3.exceptions import WebDavException
import logging
import threading
import time
import sys
from datetime import datetime

nodeuser = 'admin'                                          # replace with your username
nodepwd = 'adminpassword'                                   # replace with your password
url = 'http://localhost:8080/remote.php/dav/files/admin/'   # webdav url for the user

numFiles = 10000                                            # Total number of files to upload and delete
maxUploads = 1000                                           # Number of files to upload simultaneously
maxDeletes = 1000                                           # Number of files to delete simultaneously
fileSizeInBytes = 1024                                      # File size will be filled with randomly generated content

WebDavPerformance_timeout = 30
davPerformanceResults = []
testThreadsRunning = 0
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

def excepthook(args):
    logger.error(f'Threading exception: {args}')
    decreaseUploadCount()
    sys.excepthook(*sys.exc_info())

threading.excepthook = excepthook

def decreaseUploadCount():
    global testThreadsRunning
    testThreadsRunning -= 1

fullnode = 'localhost'
logger.info(f'TestID: {fullnode}')
logger.info(f'URL: {url}')

options = {
'webdav_hostname': url,
'webdav_login' : nodeuser,
'webdav_password' : nodepwd,
'webdav_timeout': WebDavPerformance_timeout
}

client = Client(options)
client.verify = False
logger.info(client.list())
client.mkdir('performance')

logger.info('Generate local files')
files = []
for i in range(0,numFiles):
    filename = f'{fullnode}{str(i)}.bin'
    pathname = f'{tempfile.gettempdir()}/{filename}'
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
                testThreadsRunning += 1
                client.upload_async(remote_path=f'performance/{file}',local_path=f'{tempfile.gettempdir()}/{file}', callback=decreaseUploadCount)
            except WebDavException as exception:
                logger.info(f'Error uploading {filename}: {exception}')
                testThreadsRunning -= 1
        while testThreadsRunning > 0:
            time.sleep(0.01)
    endTime = datetime.now()
except:
    logger.error('Error during async upload')

# Calculate time to upload
uploadTime = (endTime - startTime).total_seconds()

# Remove the temporary files
logger.info('Remove temporary files')
for i in range(0,numFiles):
    filename = f'{tempfile.gettempdir()}/{fullnode}{str(i)}.bin'
    os.remove(filename)

davElements = client.list('performance')
logger.info(f'{davElements}')
# davElements.pop(0)
startTime = datetime.now()

for i in range(0,len(davElements),maxDeletes):
    x = i
    logger.info(f'Batch delete {davElements[x:x+maxDeletes]}')
    for element in davElements[x:x+maxDeletes]:
        t = threading.Thread(target=client.clean, args=['performance/' + element])
        t.start()
    while threading.active_count() > 1:
        time.sleep(0.01)

deleteTime = (datetime.now() - startTime).total_seconds()

lText = f'{fullnode} '
mText = f'Upload: {uploadTime:.1f}s at {uploadTime/numFiles:.2f} s/file - {numFiles/uploadTime:.2f} files/s'
rText = f'Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file - {numFiles/deleteTime:.2f} files/s' 

message = f'{lText : <16}{mText : <40}{rText : <40}'
logger.info(f'{message}')
davPerformanceResults.append(message)

logger.info(f'Results for {numFiles} with max {maxUploads} concurrent uploads and max {maxDeletes} concurrent deletes')
for message in davPerformanceResults:
    logger.info(f'{message}')

logger.info('Done')