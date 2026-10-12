"""MFA4ALL tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>

When MFA is enforced for all users (MFA4ALL), WebDAV must reject a
user's normal password; only app passwords may work. For every node
under test, this test lists the Selenium user's home folder with the
user's password and expects HTTP 401, then lists it with the app
password and expects it to work.
"""
import unittest
import sunetnextcloud
import threading
import time
import os
import logging
import xmlrunner
import HtmlTestRunner

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

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

use_driver_service = False
if os.environ.get('SELENIUM_DRIVER_SERVICE') == 'True':
    use_driver_service = True

class WebDAVList(threading.Thread):
    """Thread that checks WebDAV logins of the Selenium user under MFA4ALL.

    Listing the home folder with the user's password must fail with
    HTTP 401, and listing it with the app password must work. The node
    fails if the password listing works or fails with any other error,
    or if the app password listing fails.
    """

    def __init__(self, name, TestMfa4All):
        threading.Thread.__init__(self)
        self.name = name
        self.TestMfa4All = TestMfa4All

    def run(self):
        global logger
        global g_failedNodes

        fullnode = self.name
        logger.info(f'WebDAVDneCheck thread started for node {self.name}')

        try:
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
        except Exception as error:
            logger.error(f'Error setting up WebDAV clients for {fullnode}: {error}')
            g_failedNodes.append(fullnode)
            return

        try:
            logger.error(f'Client list should not be possible for {fullnode} - {passwordClient.list()}')
            g_failedNodes.append(fullnode)
            return
        except Exception as error:
            if hasattr(error, 'code'):
                if error.code == 401:
                    logger.info(f'{fullnode} - Expected fail: {error.code}')
                else:
                    logger.error(f'Unknown error code: {error.code}')
                    g_failedNodes.append(fullnode)
                    return
            else:
                logger.error(f'Unknown exception: {error}')
                g_failedNodes.append(fullnode)
                return

        # The app password must still work after the password login is rejected
        try:
            appPasswordClient.list()
            logger.info(f'{fullnode} - Client list with app password works')
        except Exception as error:
            logger.error(f'Client list with app password failed for {fullnode}: {error}')
            g_failedNodes.append(fullnode)


class TestMfa4All(unittest.TestCase):
    """MFA4ALL checks for all nodes under test."""
    def deleteCookies(self, driver):
        """Delete all cookies of a Selenium WebDriver session."""
        cookies = driver.get_cookies()
        logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_webdav_passwords(self):
        """Check that WebDAV rejects password logins (HTTP 401) and accepts app passwords on all nodes."""
        global g_failedNodes
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        # if drv.target == 'prod':
        #     logger.warning('We are not testing mfa4all in production yet')
        #     return

        version = drv.expectedResults[drv.target]['status']['version']
        logger.info(f'Expected Nextcloud version: {version}')

        threads = []
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                WebDAVListThread = WebDAVList(name=fullnode, TestMfa4All=self)
                WebDAVListThread.start()
                threads.append(WebDAVListThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        if len(g_failedNodes) > 0:
            logger.error(f'Webdav mfa4all list failed for {len(g_failedNodes)} of {len(drv.allnodes)} nodes:')
            for node in g_failedNodes:
                with self.subTest(mynode=node):
                    logger.error(f'   {node}')
                    self.assertTrue(False)
            g_failedNodes = []

if __name__ == '__main__':
    if drv.testrunner == "xml":
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output="test-reports"))
    elif drv.testrunner == "txt":
        unittest.main(
            testRunner=unittest.TextTestRunner(
                resultclass=sunetnextcloud.NumbersTestResult
            )
        )
    else:
        unittest.main(
            testRunner=HtmlTestRunner.HTMLTestRunner(
                output="test-reports-html",
                combine_reports=True,
                report_name=f"nextcloud-{drv.target}-{drv.expectedResults[drv.target]['status']['version'][-1]}-{os.path.basename(__file__)}",
                add_timestamp=False,
            )
        )
