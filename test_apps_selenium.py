""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import unittest
import sunetnextcloud

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import os
import yaml
import logging
from datetime import datetime

expectedResultsFile = 'expected.yaml'
geckodriver_path = "/snap/bin/geckodriver"
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_expectedResultsFile = 'expected.yaml'
g_testtarget = os.environ.get('NextcloudTestTarget')
g_driver_timeout = 20
g_wait={}
g_driver={}
g_logger={}
g_drv={}
g_loggedInNodes={}

use_driver_service = False
if os.environ.get('SELENIUM_DRIVER_SERVICE') == 'True':
    use_driver_service = True


def deleteCookies():
    g_driver.get_cookies()
    # g_logger.info(f'Deleting all cookies: {cookies}')
    g_logger.info('Deleting all cookies.')
    g_driver.delete_all_cookies()
    g_driver.get_cookies()
    # g_logger.info(f'Cookies deleted: {cookies}')
    g_logger.info('Cookies deleted.')

def nodelogin(nextcloudnode):
    global g_wait
    deleteCookies()
    g_logger.info(f'Logging in to {nextcloudnode}')
    loginurl = g_drv.get_node_login_url(nextcloudnode)
    g_logger.info(f'Login url: {loginurl}')
    nodeuser = g_drv.get_seleniumuser(nextcloudnode)
    nodepwd = g_drv.get_seleniumuserpassword(nextcloudnode)
    g_loggedInNodes[nextcloudnode] = True

    g_driver.set_window_size(1920, 1152)
    # driver2 = webdriver.Firefox()
    g_driver.get(loginurl)

    g_wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
    g_wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

    return

class TestAppsSelenium(unittest.TestCase):
    global g_loggedInNodes, g_logger, g_drv, g_wait, g_driver
    drv = sunetnextcloud.TestTarget(g_testtarget)
    g_drv=drv
    logger = logging.getLogger(__name__)
    g_logger = logger
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
    
    with open(g_expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    # Some class names of icons changed from Nextcloud 27 to 28
    version = expectedResults[drv.target]['status']['version']
    if version.startswith('27'):
        homeIcon = 'icon-home'
        addIcon = 'icon-add'
    else:
        homeIcon = 'home-icon'
        addIcon = 'plus-icon'

    try:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        driver = webdriver.Chrome(options=options)
        g_driver=driver
    except Exception as error:
        logger.error(f'Error initializing Chrome driver: {error}')

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    for nextcloudnode in drv.nodestotest:
        g_loggedInNodes[nextcloudnode] = False

    def test_app_shortcuts(self):
        delay = 30 # seconds

        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait

        # The class name of the share icon changed in Nextcloud 28
        version = self.expectedResults[g_drv.target]['status']['version']
        self.logger.info(f'Expected Nextcloud version: {version}')

        for fullnode in g_drv.nodestotest:
            with self.subTest(mynode=fullnode):
                self.logger.info(f'TestID: Testing node {fullnode}')
                nodelogin(fullnode)


                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info('App menu is ready!')
                except TimeoutException:
                    self.logger.warning('Loading of app menu took too much time!')

                defaultApps = self.expectedResults[g_drv.target]['defaultapps']
                optionalApps = self.expectedResults[g_drv.target]['optionalapps']
                try:
                    for appentry in self.driver.find_elements(By.CLASS_NAME, "app-menu-entry"):
                        appid = appentry.get_attribute("data-app-id")
                        if appid in defaultApps or appid in optionalApps:
                            self.logger.info(f'Installed app {appid} expected!')
                        else:
                            self.logger.warning(f'Unexpected app on node: {appid}')
                            self.assertTrue(False)
                except Exception as error:
                    self.logger.warning(f'No app menu entries found: {error}')

                self.logger.info('And done...')

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
