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
from selenium.webdriver.common.action_chains import ActionChains
import os
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
        self.logger.info(f'self.logger.info test_logger')
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
                except:
                    self.logger.error(f'Error initializing Chrome driver')
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
                    self.logger.info(f'App menu is ready!')
                except TimeoutException:
                    self.logger.info(f'Loading of app menu took too much time!')

                # Check URLs after login
                dashboardUrl = drv.get_dashboard_url(fullnode)
                currentUrl = driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                rds = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/apps/rds/' +'"]')
                rds.click()

                try:
                    self.logger.info(f'Waiting for RDS iframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'rds-editor')))
                    self.logger.info('RDS iframe loaded')
                    proceed = True
                except:
                    self.logger.error(f'RDS iframe not loaded')
                    proceed = False
                self.assertTrue(proceed)

                time.sleep(3)
                # Getting started button
                try:
                    driver.find_element(by=By.XPATH, value='/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span')
                    needsToConnect = True
                except:
                    self.logger.info(f'RDS is already connected')
                    needsToConnect = False
                    pass

                if needsToConnect:
                    try:
                        self.logger.info(f'Try to find getting started button...')
                        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span'))).click()            
                        self.logger.info(f'Getting started button visible!')
                    except TimeoutException:
                        self.logger.info(f'Unable to find getting started button!')

                    # Loop through until we find a new window handle
                    for window_handle in driver.window_handles:
                        if window_handle != original_window:
                            driver.switch_to.window(window_handle)
                            break        

                    self.logger.info(f'Switched to authentication window')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/input'))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="submit-wrapper"]/input'))).click()
                    self.logger.info(f'Access granted')

                    self.logger.info(f'Switch back to original window')
                    driver.switch_to.window(original_window)

                    try:
                        self.logger.info(f'Waiting for rds frame')
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
                        self.logger.info(f'RDS iframe loaded')
                        proceed = True
                    except:
                        self.logger.error(f'RDS iframe not loaded')
                        proceed = False
                    self.assertTrue(proceed)

                self.logger.info(f'Done...')
                time.sleep(2)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
