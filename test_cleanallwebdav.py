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
from datetime import datetime
import time

import sunetdrive

g_testtarget = os.environ.get('DriveTestTarget')
g_excludeList = ['selenium-system/', 'selenium-personal/', 'projectbucket/']

# os.environ.set()
ocsheaders = { "OCS-APIRequest" : "true" }



class TestCleanAllWebDAV(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_cleanallwebdav(self):
        self.logger.info(f'Target: {g_testtarget}')
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):                
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

                client = Client(options)

                client.list()
                davElements = client.list()
                self.logger.info(f'1. DAV elements: {davElements}')
                davElements.pop(0)
                self.logger.info(f'2. Remove first element: {davElements}')

                for rootElem in davElements:
                    if rootElem in g_excludeList:
                        self.logger.info(f'Cleaning subfolders in : {rootElem}')
                        subElements = client.list(rootElem)
                        subElements.pop(0)
                        for subElement in subElements:
                            self.logger.info(f'Removing {fullnode} - {drv.target} - {subElement}')
                            try:
                                client.clean(rootElem + subElement)
                            except:
                                self.logger.error(f'Could not delete sub element {rootElem}\{subElement}')
                    else:
                        self.logger.info(f'Removing {fullnode} - {drv.target} - {rootElem}')
                        try:
                            client.clean(rootElem)
                        except:
                            self.logger.error(f'Could not delete {fullnode} - {drv.target} - {rootElem}')

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
