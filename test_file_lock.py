""" Testing file locking for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
import json
import os
from webdav3.client import Client
import logging
import sunetdrive
from xml.dom import minidom

g_maxCheck = 10
g_testFolder = 'SeleniumCollaboraTest'
g_stressTestFolder = 'SeleniumCollaboraStressTest'
g_sharedTestFolder = 'SharedFolder'
g_personalBucket = 'selenium-personal'
g_systemBucket = 'selenium-system'
g_filename=datetime.now().strftime("test_file_lock-%Y-%m-%d_%H-%M-%S.txt")
g_localFile = "temp/" + g_filename
ocsheaders = { "OCS-APIRequest" : "true" } 

HTTP_MULTI_STATUS = 207
PROPFIND_REQUEST = '''<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:">
<d:prop xmlns:oc="http://owncloud.org/ns">
  <oc:fileid/>
</d:prop>
</d:propfind>'''

class TestFileLock(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.warning(f'self.logger.info test_logger')
        pass

    def test_lock_unlock_curl_webdav(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                with open(g_localFile, "w") as text_file:
                    text_file.write(f'WebDAV Test File: {fullnode} - {drv.target}\n{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
                
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
                result = client.upload_sync(remote_path=g_filename, local_path=g_localFile)

                curlLock = drv.get_file_lock_curl(fullnode, nodeuser, g_filename)
                self.logger.info(f'File lock url: {curlLock}')
                curlLock = curlLock.replace("$PASSWORD$", nodepwd)
                os.system(curlLock)

                curlUnlock = drv.get_file_unlock_curl(fullnode, nodeuser, g_filename)
                self.logger.info(f'File unlock url: {curlUnlock}')
                curlUnlock = curlUnlock.replace("$PASSWORD$", nodepwd)
                os.system(curlUnlock)

    def test_lock_unlock_ocs(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                with open(g_localFile, "w") as text_file:
                    text_file.write(f'WebDAV Test File: {fullnode} - {drv.target}\n{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
                
                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)
                url = drv.get_webdav_url(fullnode, nodeuser)
                self.logger.info(f'URL: {url}')
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }
                data = { 'userid': nodeuser, 'password': nodepwd}
                client = Client(options)
                result = client.upload_sync(remote_path=g_filename, local_path=g_localFile)

                nodeuser = drv.get_seleniumuser(fullnode)
                nodepwd = drv.get_seleniumuserpassword(fullnode)

                url = drv.get_webdav_url(fullnode, nodeuser) + g_filename
                session = requests.Session()
                session.auth = (nodeuser, nodepwd)
                r = session.request(method='PROPFIND', url=url, data=PROPFIND_REQUEST)
                if r.status_code == HTTP_MULTI_STATUS:
                    dom = minidom.parseString(r.text.encode('ascii', 'xmlcharrefreplace'))
                    response = dom.getElementsByTagName('d:response')[0]
                    href = response.getElementsByTagName('d:href')[0].firstChild.data
                    prop_stat = response.getElementsByTagName('d:propstat')[0]
                    prop = prop_stat.getElementsByTagName('d:prop')[0]
                    fileid = prop.getElementsByTagName('oc:fileid')[0].firstChild.data
                    lockUrl = drv.get_file_lock_url(fullnode, fileid)
                    r = session.post(lockUrl, headers=ocsheaders, auth = HTTPBasicAuth(nodeuser, nodepwd))
                    self.logger.info(f'Lock status code: {r.status_code}')
                    self.logger.info(f'Lock request response: {r.text}')

if __name__ == '__main__':
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
