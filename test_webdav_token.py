""" Testing WebDAV functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
from webdav3.client import Client
import logging
from datetime import datetime

import sunetdrive

g_maxCheck = 10
g_testFolder = 'SeleniumCollaboraTest'
g_stressTestFolder = 'SeleniumCollaboraStressTest'
g_sharedTestFolder = 'SharedFolder'
g_personalBucket = 'selenium-personal'
g_systemBucket = 'selenium-system'
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
ocsheaders = { "OCS-APIRequest" : "true" } 
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class TestWebDAV(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info('logger.info test_logger')
        pass

    def test_webdav_list(self):
        global logger
        logger.info('test_webdav_list')
        drv = sunetdrive.TestTarget()

        logger.info('WebDAVList')
        drv = sunetdrive.TestTarget()

        nodeuser = 'tene3253@su.se'
        nodepwd = 'xYtG32ydX9ybt6ub3zdoCmdygjW5UBk7AQXsawU0eVfNwN8KLoy8mfIIBMci9tT6Wg8dWThn'

        logger.info(f'Usernames: {nodeuser}')

        logger.warning(f'Testing user: {nodeuser}')
        url = drv.get_webdav_url('su', nodeuser)
        logger.info(f'URL: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }
        client = Client(options)
        logger.info(client.list())


if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
