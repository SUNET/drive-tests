""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test apps in Sunet Drive
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetnextcloud
from webdav3.client import Client

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import logging
import pyautogui

g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

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
        self.logger.info('self.logger.info test_logger')
        pass
    
    def test_jupyter_aio(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                loginurl = drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = drv.get_jupyteruser(fullnode)
                self.logger.info(f'Username: {nodeuser}')
                nodepwd = drv.get_jupyteruserpassword(fullnode)

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
                    self.logger.error('Error initializing Chrome driver')
                    self.assertTrue(False)
                driver.maximize_window()
                # driver2 = webdriver.Firefox()
                driver.get(loginurl)

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info('App menu is ready!')
                except TimeoutException:
                    self.logger.info('Loading of app menu took too much time!')

                # Check URLs after login
                dashboardUrl = drv.get_dashboard_url(fullnode)
                currentUrl = driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                jupyter = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/apps/integration_jupyterhub/' +'"]')
                jupyter.click()

                try:
                    self.logger.info('Waiting for jupyter iframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//*[@id="content"]/iframe')))
                    self.logger.info('Jupyter iframe loaded')
                except:
                    self.logger.error('Jupyter iframe not loaded')

                try:
                    self.logger.info('Authorizing Jupyter app')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/input'))).click()
                    self.logger.info('Logged in to jupyter app')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="submit-wrapper"]/input'))).click()
                    self.logger.info('Authorization granted')
                except:
                    self.logger.error('Error authorizing JupyterHub app')

                # Starting the server
                try:
                    wait.until(EC.presence_of_element_located((By.ID, 'start')))
                    needsToConnect = True
                    self.logger.info('Server needs to be started')
                except:
                    needsToConnect = False
                    self.logger.info('Server already started')

                if needsToConnect:
                    login = driver.find_element(By.ID, 'start')
                    login.click()
                    self.logger.info('Starting server')
                time.sleep(3)
                try:
                    self.logger.info('Logging out')
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'lm-MenuBar-itemLabel') and text()='File']"))).click()
                    self.logger.info('File menu opened')
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@data-command='hub:logout']"))).click()
                    time.sleep(600)
                    # wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@data-command='hub:logout']"))).click()
                    self.logger.info('Logged out and disconnected from JupyterHub')
                    proceed = True
                except:
                    self.logger.error('Error logging out from JupyterHub, saving screenshot')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + fullnode + "test_jupyter_aio" + g_filename + ".png")
                    proceed = False

                time.sleep(2)
                self.assertTrue(proceed)

                self.logger.info('Done...')
                time.sleep(2)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
