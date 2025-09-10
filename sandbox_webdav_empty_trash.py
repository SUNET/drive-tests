""" Nextcloud WebDAV stress test against a locally deployed instance. 
Author: Richard Freitag <freitag@sunet.se>
"""

from webdav3.client import Client
import logging
import threading
import time
import sys
from datetime import datetime
import sunetnextcloud

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

drv =sunetnextcloud.TestTarget()

if len(drv.nodestotest) != 1:
    logger.error('Please set a single node to test')
    sys.exit()

fullnode = drv.nodestotest[0]
nodeuser = drv.get_seleniumuser(fullnode)
nodepwd = drv.get_seleniumuserpassword(fullnode)
url = drv.get_webdav_url(fullnode, nodeuser)
url = url.replace('files','trashbin')

maxDeletes = 13                                           # Number of files to delete simultaneously

WebDavPerformance_timeout = 30
davPerformanceResults = []
testThreadsRunning = 0

def excepthook(args):
    logger.error(f'Threading exception: {args}')
    sys.excepthook(*sys.exc_info())

threading.excepthook = excepthook

logger.info(f'TestID: {fullnode}')
logger.info(f'URL: {url}')

options = {
'webdav_hostname': url,
'webdav_login' : nodeuser,
'webdav_password' : nodepwd,
'webdav_timeout': WebDavPerformance_timeout
}

client = Client(options)
# logger.info(client.list())
# client.mkdir('performance')

davElements = client.list('trash')
numFiles = len(davElements)
logger.info(f'Remove {numFiles} elements from trash for {fullnode}')
davElements.pop(0)
startTime = datetime.now()

for i in range(0,numFiles,maxDeletes):
    x = i
    logger.info(f'Batch delete {len(davElements[x:x+maxDeletes])} elements on {fullnode}')
    for element in davElements[x:x+maxDeletes]:
        targetdeletefile = f'trash/{element}'
        # logger.info(f'Delete {targetdeletefile}')
        t = threading.Thread(target=client.clean, args=[targetdeletefile])
        t.start()
    while threading.active_count() > 1:
        time.sleep(0.01)

deleteTime = (datetime.now() - startTime).total_seconds()

lText = f'{fullnode} '
rText = f'Delete: {deleteTime:.1f}s at {deleteTime/numFiles:.2f} s/file - {numFiles/deleteTime:.2f} files/s' 

message = f'{lText : <16}{rText : <40}'
logger.info(f'{message}')
davPerformanceResults.append(message)

logger.info(f'Results for {numFiles} with max {maxDeletes} concurrent deletes')
for message in davPerformanceResults:
    logger.info(f'{message}')

logger.info('Done')