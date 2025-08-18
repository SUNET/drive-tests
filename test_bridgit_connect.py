""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test apps in Sunet Drive
"""
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

class TestRdsSelenium(unittest.TestCase):
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
    
    def test_rds_connect(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
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
                except Exception as error:
                    self.logger.error(f'Error initializing Chrome driver: {error}')
                    self.assertTrue(False)
                driver.maximize_window()
                # driver2 = webdriver.Firefox()
                driver.get(loginurl)
                # Store the ID of the original window for authorization window
                original_window = driver.current_window_handle

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info('App menu is ready!')
                except TimeoutException:
                    self.logger.info('Loading of app menu took too much time!')

                # Check URLs after login
                # dashboardUrl = drv.get_dashboard_url(fullnode)
                # currentUrl = driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                bridgit = driver.find_element(By.XPATH, '//a[@href="'+ '/apps/rdsng/' +'"]')
                bridgit.click()

                try:
                    self.logger.info('Waiting for BridgIT iframe')
                    # wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'rds-editor')))
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'app-frame')))
                    self.logger.info('BridgIT iframe loaded')
                    proceed = True
                except Exception as error:
                    self.logger.error(f'BridgIT iframe not loaded: {error}')
                    proceed = False
                self.assertTrue(proceed)

                time.sleep(3)
                # Getting started button
                try:
                    needsToConnect = False
                    span_element = driver.find_element(By.XPATH, '//span[@class="p-button-label"]')
                    if span_element.text == 'Authorize bridgit':
                        needsToConnect = True
                    self.logger.info(f'Bridgit needs to connect!')
                except Exception:
                    self.logger.info('BridgIT is already connected:')
                    needsToConnect = False
                    pass

                if needsToConnect:
                    try:
                        self.logger.info('Try to find authorize button...')
                        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//span[@class="p-button-label"]'))).click()
                        self.logger.info('Authorize button clicked!')
                    except TimeoutException:
                        self.logger.info('Unable to find authorize button!')

                    # Loop through until we find a new window handle
                    self.logger.info(f'Window handles')
                    self.logger.info(f'Original handle: {original_window}')
                    self.logger.info(f'All handles: {driver.window_handles}')                    
                    driver.switch_to.window(original_window)

                    for window_handle in driver.window_handles:
                        if window_handle != original_window:
                            driver.switch_to.window(window_handle)
                            break        

                    self.logger.info('Switch back to default (iframe) content')
                    driver.switch_to.default_content()

                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/input'))).click()
                    self.logger.info('Input clicked')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="submit-wrapper"]/input'))).click()
                    # /html/body/div[2]/div/main/div/form[1]/input
                    self.logger.info('Access granted')

                    self.logger.info('Switch back to original window')
                    driver.switch_to.window(original_window)

                    try:
                        self.logger.info('Waiting for BridgIT frame')
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "app-frame")))
                        self.logger.info('BridgIT iframe loaded')
                        proceed = True
                    except Exception as error:
                        self.logger.error(f'BridgIT iframe not loaded: {error}')
                        proceed = False
                    self.assertTrue(proceed)

                self.logger.info('Done...')
                time.sleep(2)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
