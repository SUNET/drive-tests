""" MFA4ALL Test for Sunet Drive/Nextcloud
Author: Richard Freitag <freitag@sunet.se>
Test if MFA4ALL is enforced
"""
import unittest
import sunetnextcloud
import threading
import time
import os
import logging

from webdav3.client import Client
from webdav3.exceptions import WebDavException
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions


drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

geckodriver_path = "/snap/bin/geckodriver"
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_driver_timeout = 20
g_failedNodes = []
g_testThreadsRunning = 0

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

use_driver_service = False
if os.environ.get('SELENIUM_DRIVER_SERVICE') == 'True':
    use_driver_service = True

class WebDAVList(threading.Thread):

    def __init__(self, name, TestMfa4All):
        threading.Thread.__init__(self)
        self.name = name
        self.TestMfa4All = TestMfa4All

    def run(self):
        global logger
        global g_failedNodes
        global g_testThreadsRunning

        fullnode = self.name
        g_testThreadsRunning += 1
        logger.info(f'WebDAVDneCheck thread started for node {self.name}')

        nodeuser = drv.get_seleniumuser(fullnode)
        logger.info(f'Username: {nodeuser}')
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        nodeapppwd = drv.get_seleniumuserapppassword(fullnode)

        # Webdav client with the regular user password
        url = drv.get_webdav_url(fullnode, nodeuser)
        passwordOptions = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd 
        }
        passwordClient = Client(passwordOptions)
        passwordClient.verify = drv.verify

        appPasswordOptions = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodeapppwd 
        }
        appPasswordClient = Client(appPasswordOptions)
        appPasswordClient.verify = drv.verify

        try:
            logger.error(f'Client list should not be possible for {fullnode} - {passwordClient.list()}')            
            g_failedNodes.append(fullnode)
            g_testThreadsRunning -= 1
            return
        except WebDavException as error:
            logger.info(f'{fullnode} - Expected fail: {error.code}')
            g_testThreadsRunning -= 1
            return
        except Exception as error:
            logger.error(f'Unknown exception: {error}')
            g_failedNodes.append(fullnode)
            g_testThreadsRunning -= 1
            return

class TestMfa4All(unittest.TestCase):
    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_webdav_passwords(self):
        global g_failedNodes
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        # if drv.target == 'prod':
        #     logger.warning('We are not testing mfa4all in production yet')
        #     return

        version = drv.expectedResults[drv.target]['status']['version']
        logger.info(f'Expected Nextcloud version: {version}')

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVListThread = WebDAVList(name=fullnode, TestMfa4All=self)
                WebDAVListThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        if len(g_failedNodes) > 0:
            logger.error(f'Webdav mfa4all list failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                logger.error(f'   {node}')
            g_failedNodes = []
            self.assertTrue(False)

if __name__ == '__main__':
    drv.run_tests(os.path.basename(__file__), 'acceptance')
