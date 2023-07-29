""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import unittest
import sunetdrive
from webdav3.client import Client
import pyotp

import time

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

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('DriveTestTarget')

class TestLoginSeleniumTotp(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_gss_login(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget(g_testtarget)

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing gss')
            return

        fullnode = 'gss'

        loginurl = drv.get_node_login_url(fullnode)
        self.logger.info(f'Login url: {loginurl}')

        nodeuser = drv.get_seleniummfauser(fullnode)
        nodepwd = drv.get_seleniummfauserpassword(fullnode)
        nodeapppwd = drv.get_seleniummfauserapppassword(fullnode)
        nodetotpsecret = drv.get_seleniummfausertotpsecret(fullnode)

        # nodeuser = drv.get_seleniumuser(fullnode)
        # nodepwd = drv.get_seleniumuserpassword(fullnode)
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

        # Wait for TOTP screen
        totp = pyotp.TOTP(nodetotpsecret)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

        # Check URL after login
        dashboardUrl = drv.get_dashboard_url(fullnode)
        currentUrl = driver.current_url
        self.assertEqual(dashboardUrl, currentUrl)                

        try:
            myElem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time!')

        files = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/apps/files/' +'"]')
        files.click()

        try:
            myElem = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
            self.logger.info(f'All files visible!')
        except TimeoutException:
            self.logger.info(f'Loading of all files took too much time!')

        driver.implicitly_wait(10) # seconds before quitting
        print(driver.current_url)

    def test_node_login(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                loginurl = drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = drv.get_seleniummfauser(fullnode)
                nodepwd = drv.get_seleniummfauserpassword(fullnode)
                nodeapppwd = drv.get_seleniummfauserapppassword(fullnode)
                nodetotpsecret = drv.get_seleniummfausertotpsecret(fullnode)

                # Create folder for testing using webdav
                url = drv.get_webdav_url(fullnode, nodeuser)
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodeapppwd 
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

                # Wait for TOTP screen
                totp = pyotp.TOTP(nodetotpsecret)
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info(f'App menu is ready!')
                except TimeoutException:
                    self.logger.info(f'Loading of app menu took too much time!')

                # Check URLs after login
                dashboardUrl = drv.get_dashboard_url(fullnode)
                currentUrl = driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                files = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/apps/files/' +'"]')
                files.click()

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu-entry')))
                    self.logger.info(f'All files visible!')
                except TimeoutException:
                    self.logger.info(f'Loading of all files took too much time!')

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-shared')))
                    sharefolder = driver.find_element(by=By.CLASS_NAME, value='icon-shared')
                    sharefolder.click()
                    self.logger.info(f'Clicked on share folder')
                except:
                    self.logger.info(f'icon-shared not found')

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sharing-entry__title')))
                    self.logger.info(f'Share link enabled!')
                except TimeoutException:
                    self.logger.info(f'No share link present!')

                wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
                logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
                logoutLink.click()
                self.logger.info(f'Logout complete')

                currentUrl = driver.current_url
                self.logger.info(driver.current_url)

                if fullnode == 'scilifelab':
                    self.assertEqual(driver.current_url, drv.get_node_post_logout_saml_url(fullnode))
                elif fullnode == 'kau':
                    self.assertEqual(driver.current_url, drv.get_node_post_logout_url(fullnode))
                else:
                    self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())

                driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(f'{driver.current_url}')

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
