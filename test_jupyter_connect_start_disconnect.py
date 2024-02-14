""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test apps in Sunet Drive
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetdrive
from webdav3.client import Client

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import logging

class TestJupyterSelenium(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        self.logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        self.logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass
    
    def test_authorize_jupyter(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                loginurl = drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = drv.get_seleniumuser(fullnode)
                self.logger.info(f'Username: {nodeuser}')
                nodepwd = drv.get_seleniumuserpassword(fullnode)

                # Create folder for testing using webdav
                url = drv.get_webdav_url(fullnode, nodeuser)
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)
                dir = 'SharedFolder'
                self.logger.info(f'Make and check directory: {dir}')
                client.mkdir(dir)
                self.assertEqual(client.list().count('SharedFolder/'), 1)

                try:
                    options = Options()
                    driver = webdriver.Chrome(options=options)
                except:
                    self.logger.error(f'Error initializing Chrome driver')
                    self.assertTrue(False)
                driver.maximize_window()
                # driver2 = webdriver.Firefox()
                driver.get(loginurl)

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info(f'App menu is ready!')
                except TimeoutException:
                    self.logger.info(f'Loading of app menu took too much time!')

                # Check URLs after login
                dashboardUrl = drv.get_dashboard_url(fullnode)
                currentUrl = driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                jupyter = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/apps/integration_jupyterhub/' +'"]')
                jupyter.click()

                try:
                    self.logger.info(f'Waiting for jupyter iframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//*[@id="content"]/iframe')))
                    self.logger.info('Jupyter iframe loaded')
                except:
                    self.logger.error(f'Jupyter iframe not loaded')

                try:
                    self.logger.info(f'Authorizing Jupyter app')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/input'))).click()
                    self.logger.info(f'Logged in to jupyter app')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="submit-wrapper"]/input'))).click()
                    self.logger.info(f'Authorization granted')
                except:
                    self.logger.error(f'Error authorizing JupyterHub app')

                # Starting the server
                try:
                    wait.until(EC.presence_of_element_located((By.ID, 'start')))
                    needsToConnect = True
                    self.logger.info(f'Server needs to be started')
                except:
                    needsToConnect = False
                    self.logger.info(f'Server already started')

                if needsToConnect:
                    login = driver.find_element(By.ID, 'start')
                    login.click()
                    self.logger.info(f'Starting server')

                try:
                    self.logger.info(f'Logging out')
                    wait.until(EC.presence_of_element_located((By.ID, 'logout'))).click()
                    self.logger.info(f'Logged out and disconnected from JupyterHub')
                    proceed = True
                except:
                    self.logger.error(f'Error logging out from JupyterHub')
                    proceed = False
                self.assertTrue(proceed)

                self.logger.info(f'Done...')
                time.sleep(2)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
