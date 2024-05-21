""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetnextcloud
from webdav3.client import Client
import pyotp
import pyautogui

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
import yaml
import logging

# 'prod' for production environment, 'test' for test environment
expectedResultsFile = 'expected.yaml'
g_testtarget = os.environ.get('NextcloudTestTarget')
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

class TestLoginSeleniumTotp(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    with open(expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        self.logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        self.logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_gss_login(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget(g_testtarget)
        if drv.testgss == False:
            self.logger.info('Not testing gss')
            return

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing gss')
            return

        fullnode = 'gss'

        loginurl = drv.get_node_login_url(fullnode)
        self.logger.info(f'URL: {loginurl}')
        nodeuser = drv.get_seleniummfauser(fullnode)
        self.logger.info(f'Username: {nodeuser}')
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
        self.deleteCookies(driver)
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

        # Wait for TOTP screen
        try:
            self.logger.info(f'Check if TOTP selection dialogue is visible')
            totpselect = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/login/challenge/totp' +'"]')
            self.logger.warning(f'Found TOTP selection dialogue')
            totpselect.click()
        except:
            self.logger.info(f'No need to select TOTP provider')

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
        drv = sunetnextcloud.TestTarget()

        # The class name of the share icon changed in Nextcloud 28
        version = self.expectedResults[drv.target]['status']['version']
        self.logger.info(f'Expected Nextcloud version: {version}')
        if version.startswith('27'):
            sharedClass = 'icon-shared'
            simpleLogoutUrl = False
            self.logger.info(f'We are on Nextcloud 27 and are not using the simple logout url')
        else:
            # This will select the first available sharing button
            sharedClass = 'files-list__row-action-sharing-status'
            simpleLogoutUrl = True
            self.logger.info(f'We are on Nextcloud 28 and are therefore using the simple logout url')

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.logger.info(f'TestID: {fullnode}')
                loginurl = drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = drv.get_seleniummfauser(fullnode)
                self.logger.info(f'Username: {nodeuser}')
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
                self.deleteCookies(driver)
                driver.get(loginurl)

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                # Wait for TOTP screen
                try:
                    self.logger.info(f'Check if TOTP selection dialogue is visible')
                    totpselect = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/login/challenge/totp' +'"]')
                    self.logger.warning(f'Found TOTP selection dialogue')
                    totpselect.click()
                except:
                    self.logger.info(f'No need to select TOTP provider')

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

                try:
                    self.logger.info(f'Waiting for files app button')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="'+ '/index.php/apps/files/' +'"]')))
                    files = driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/apps/files/' +'"]')
                    files.click()
                except:
                    self.logger.error(f'Files app button not found, saving screenshot')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + fullnode + "test_node_login" + g_filename + ".png")
                    self.assertTrue(False)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu-entry')))
                    self.logger.info(f'All files visible!')
                except TimeoutException:
                    self.logger.info(f'Loading of all files took too much time!')

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, sharedClass)))
                    sharefolder = driver.find_element(by=By.CLASS_NAME, value=sharedClass)
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
                elif fullnode == 'swamid' or fullnode == 'extern' or fullnode == 'sunet' or fullnode == 'vr':
                    pass
                else:
                    self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())

                driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(f'{driver.current_url}')

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
