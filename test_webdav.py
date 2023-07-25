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

import sunetdrive

g_maxCheck = 10
g_testFolder = 'SeleniumCollaboraTest'
g_stressTestFolder = 'SeleniumCollaboraStressTest'
g_sharedTestFolder = 'SharedFolder'
g_personalBucket = 'selenium-personal'
g_systemBucket = 'selenium-system'
ocsheaders = { "OCS-APIRequest" : "true" } 

class TestWebDAV(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.warning(f'self.logger.info test_logger')
        pass

    def test_webdav_dne_check(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)
                url = drv.get_webdav_url(fullnode, nodeuser)
                self.logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)
                dneName = 'THISFOLDERDOESNOTEXIST'

                for i in range(1,g_maxCheck):
                    result = client.check(dneName)
                    if (result):
                        self.logger.error(f'DNE check {i} for {dneName} should not return true')
                    self.assertFalse(result)

    def test_webdav_list(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                nodeuser = []
                nodepwd = []
                nodeuser.append(drv.get_ocsuser(fullnode))
                nodepwd.append(drv.get_ocsuserapppassword(fullnode))

                nodeuser.append(drv.get_seleniumuser(fullnode))
                nodepwd.append(drv.get_seleniumuserapppassword(fullnode))

                nodeuser.append(drv.get_seleniummfauser(fullnode))
                nodepwd.append(drv.get_seleniummfauserapppassword(fullnode))

                self.logger.info(f'Usernames: {nodeuser}')

                for user in range(3):
                    self.logger.warning(f'Testing user: {nodeuser[user]}')
                    url = drv.get_webdav_url(fullnode, nodeuser[user])
                    self.logger.info(f'URL: {url}')
                    options = {
                    'webdav_hostname': url,
                    'webdav_login' : nodeuser[user],
                    'webdav_password' : nodepwd[user] 
                    }
                    client = Client(options)
                    self.logger.info(client.list())

    def test_webdav_multicheckandremove(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            self.logger.info(f'WebDAV multicheck for {fullnode}')
            with self.subTest(mynode=fullnode):
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)
                url = drv.get_webdav_url(fullnode, nodeuser)
                self.logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)
                
                count = 0
                while count <= g_maxCheck:
                    count += 1
                    self.logger.info(f'Check for folder {g_testFolder}')
                    if (client.check(g_testFolder) == False):
                        self.logger.info(f'Folder does not exist: {g_testFolder}')
                        break
                    else:
                        self.logger.warning(f'Removing folder {g_testFolder}')
                        if (client.clean(g_testFolder)):
                            self.logger.info(f'Folder removed {g_testFolder}')    
                    self.logger.warning(f'Multiple tries to remove folder: {count}')
                self.assertFalse(client.check(g_testFolder))


    def test_webdav_clean_seleniumuserfolders(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)
                url = drv.get_webdav_url(fullnode, nodeuser)
                self.logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)

                # for i in range(1,g_maxCheck):
                #     if (client.check(g_testFolder)):
                #         self.logger.error(f'Check for {g_testFolder} should not return true')

                self.logger.info('Listing folder contents before removing the Selenium folders')
                self.logger.info(client.list())
                self.logger.info('Removing Selenium user folders')
                if client.check(g_testFolder):
                    client.clean(g_testFolder)
                if client.check(g_stressTestFolder):
                    client.clean(g_stressTestFolder)
                self.logger.info('Listing folder contents after removing the Selenium folders')
                self.logger.info(client.list())

    def make_sharing_folder(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)
                url = drv.get_webdav_url(fullnode, nodeuser)
                self.logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)

                client.mkdir(g_sharedTestFolder)
                self.assertEqual(client.list().count(f'{g_sharedTestFolder}/'), 1)

    def personal_bucket_folders(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)
                url = drv.get_webdav_url(fullnode, nodeuser)
                self.logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)

                self.assertEqual(client.list().count(f'{g_personalBucket}/'), 1)

                folder = 'test_webdav'
                path = g_personalBucket + '/' + folder
                client.mkdir(path)
                self.logger.info(client.list(path))
                self.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 1)
                client.clean(path)
                self.assertEqual(client.list(g_personalBucket).count(f'{folder}/'), 0)
                # print(client.list(g_personalBucket))

    def system_bucket_folders(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)
                url = drv.get_webdav_url(fullnode, nodeuser)
                self.logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)

                self.assertEqual(client.list().count(f'{g_systemBucket}/'), 1)

                folder = 'test_webdav'
                path = g_systemBucket + '/' + folder
                client.mkdir(path)
                self.logger.info(client.list(path))
                self.assertEqual(client.list(g_systemBucket).count(f'{folder}/'), 1)
                client.clean(path)
                self.assertEqual(client.list(g_systemBucket).count(f'{folder}/'), 0)
                # print(client.list(g_personalBucket))

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
