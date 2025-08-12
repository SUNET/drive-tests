""" Testing WebDAV functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import os
from webdav3.client import Client
import logging
from datetime import datetime
import time
import threading

import sunetnextcloud

g_testtarget = os.environ.get('NextcloudTestTarget')
g_excludeList = ['selenium-system/', 'selenium-personal/', 'projectbucket/']
g_davPerformanceResults = []

# os.environ.set()
ocsheaders = { "OCS-APIRequest" : "true" }
davThreadRunning = 0

class CleanWebDAV(threading.Thread):
    logger = logging.getLogger('ThreadLogger')
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global davThreadRunning, g_davPerformanceResults
        self.logger.info(f'DAV cleaning thread started: {self.name}')
        drv = sunetnextcloud.TestTarget(g_testtarget)
        davThreadRunning += 1
        fullnode = self.name

        nodeuser = drv.get_seleniumuser(fullnode)
        # nodepwd = drv.get_seleniumuserpassword(fullnode)
        nodepwd = drv.get_seleniumuserapppassword(fullnode)
        nodepwd 
        url = drv.get_webdav_url(fullnode, nodeuser)
        self.logger.info(url)
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }

        try:
            client = Client(options)
            client.list()
            davElements = client.list()
            self.logger.info(f'DAV elements: {davElements}')
            davElements.pop(0)
            self.logger.info(f'After removing first element: {davElements}')

            startTime = datetime.now()
            count = 0
            for rootElem in davElements:
                if rootElem in g_excludeList:
                    self.logger.info(f'Cleaning subfolders in : {rootElem}')
                    subElements = client.list(rootElem)
                    subElements.pop(0)
                    for subElement in subElements:
                        self.logger.info(f'Removing {fullnode} - {drv.target} - {subElement}')
                        try:
                            client.clean(rootElem + subElement)
                            count += 1
                        except:
                            self.logger.error(f'Could not delete sub element - {fullnode} - {rootElem}\\{subElement}')
                else:
                    self.logger.info(f'Removing {fullnode} - {drv.target} - {rootElem}')
                    try:
                        client.clean(rootElem)
                    except:
                        self.logger.error(f'Could not delete {fullnode} - {drv.target} - {rootElem}')

            totalTime = (datetime.now() - startTime).total_seconds()
            if count == 0:
                message = f'{self.name} - no elements deleted'
                g_davPerformanceResults.append(message)
                self.logger.info(f'DAV cleaning thread done: {message}')
            else:
                message = f'{self.name} - {count} elements in {totalTime:.1f}s at {count/totalTime:.2f} elements/s or {totalTime/count:.2f} s/element'
                g_davPerformanceResults.append(message)
                self.logger.info(f'DAV cleaning thread done: {message}')
        except Exception as e:
            self.logger.error(f'Unable to delete files for {fullnode}: {e}')
            davThreadRunning -= 1
            return

        davThreadRunning -= 1

class TestCleanAllWebDAV(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info('self.logger.info test_logger')
        pass

    def test_cleanallwebdav(self):
        global g_davPerformanceResults
        self.logger.info(f'Target: {g_testtarget}')
        drv = sunetnextcloud.TestTarget(g_testtarget)
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                davCleanThread = CleanWebDAV(fullnode)
                davCleanThread.start()

        while (davThreadRunning > 0):
            time.sleep(1)

        for message in g_davPerformanceResults:
            self.logger.info(f'{message}')
        
        self.logger.info('Done...')

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
