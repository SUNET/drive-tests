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
import logging
import yaml

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('NextcloudTestTarget')
g_expectedResultsFile = 'expected.yaml'
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_drv={}
g_version={}

class TestLoginMultiSelenium(unittest.TestCase):
    global g_drv, g_version
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    with open(g_expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    # Some class names of icons changed from Nextcloud 27 to 28
    drv = sunetnextcloud.TestTarget(g_testtarget)
    g_drv = drv
    g_version = expectedResults[drv.target]['status']['version']

    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        self.logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        self.logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        self.logger.info(f'Expecting Nextcloud version: {g_version}')
        pass

    def test_node_multi_login(self):
        delay = 30 # seconds
        for fullnode in g_drv.fullnodes:
            with self.subTest(mynode=fullnode):
                success = True
                loginurl = g_drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = g_drv.get_seleniummfauser(fullnode)
                self.logger.info(f'Username: {nodeuser}')
                nodepwd = g_drv.get_seleniummfauserpassword(fullnode)
                nodeapppwd = g_drv.get_seleniummfauserapppassword(fullnode)
                nodetotpsecret = g_drv.get_seleniummfausertotpsecret(fullnode)

                # Create folder for testing using webdav
                url = g_drv.get_webdav_url(fullnode, nodeuser)
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
                wait = WebDriverWait(driver, delay)
                driver.set_window_size(1920, 1152)

                sel = sunetnextcloud.SeleniumHelper(driver, fullnode)
                sel.delete_cookies()
                sel.nodelogin(sel.UserType.SELENIUM_MFA)

                # self.deleteCookies(driver)
                # # driver2 = webdriver.Firefox()
                # driver.get(loginurl)

                # wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                # wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                # # Wait for TOTP screen
                # loggedIn = False
                # logonTries = 0
                # while loggedIn == False:
                #     logonTries += 1
                #     try:
                #         self.logger.info(f'Check if TOTP selection dialogue is visible')
                #         totpselect = driver.find_element(By.XPATH, '//a[@href="'+ g_drv.indexsuffix + '/login/challenge/totp' +'"]')
                #         self.logger.warning(f'Found TOTP selection dialogue')
                #         totpselect.click()
                #     except:
                #         self.logger.info(f'No need to select TOTP provider')

                #     totp = pyotp.TOTP(nodetotpsecret)
                #     wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

                #     try:
                #         wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                #         self.logger.info(f'App menu is ready!')
                #         loggedIn = True
                #     except TimeoutException:
                #         self.logger.warning(f'Loading of app menu took too much time!')
                    
                #     if logonTries >= 3:
                #         self.logger.error(f'Unable to log on after {logonTries} tries')
                #         self.assertTrue(False)
                #         return

                # # Check URLs after login
                # dashboardUrl = g_drv.get_dashboard_url(fullnode)
                # currentUrl = driver.current_url
                # # self.assertEqual(dashboardUrl, currentUrl)                

                try:
                    self.logger.info(f'Waiting for files app button')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]')))
                    files = driver.find_element(By.XPATH, '//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]')
                    files.click()
                except:
                    self.logger.warning(f'Files app button not found, do we have to totp again?')

                    totpselect = driver.find_element(By.XPATH, '//a[@href="'+ g_drv.indexsuffix + '/login/challenge/totp' +'"]')
                    self.logger.warning(f'Found TOTP selection dialogue')
                    totpselect.click()
                    totp = pyotp.TOTP(nodetotpsecret)
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu-entry')))
                    self.logger.info(f'All files visible!')
                except TimeoutException:
                    self.logger.warning(f'Loading of all files took too much time!')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + fullnode + "test_node_multi_login" + g_filename + ".png")
                    self.assertTrue(False)

                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@title="Show sharing options"]')))
                sharefolder = driver.find_element(by=By.XPATH, value='//*[@title="Show sharing options"]')
                sharefolder.click()
                self.logger.info(f'Clicked on share folder')

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sharing-entry__title')))
                    self.logger.info(f'Share link enabled!')
                except TimeoutException:
                    self.logger.info(f'No share link present!')

                wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
                logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
                logoutLink.click()
                self.logger.info(f'Logout complete')

                self.logger.info(f'{driver.current_url}')

                self.logger.info(f'TOTP Login done, testing normal login now')
                self.deleteCookies(driver)
                time.sleep(1)

                loginurl = g_drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = g_drv.get_seleniumuser(fullnode)
                self.logger.info(f'Username: {nodeuser}')
                nodepwd = g_drv.get_seleniumuserpassword(fullnode)

                # Create folder for testing using webdav
                url = g_drv.get_webdav_url(fullnode, nodeuser)
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

                # Right now we have to call the login page twice - Check after upgrade
                driver.get(loginurl)
                time.sleep(2)

                sel.nodelogin(sel.UserType.SELENIUM)

                files = driver.find_element(By.XPATH, '//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]')
                files.click()

                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@title="Show sharing options"]')))
                sharefolder = driver.find_element(by=By.XPATH, value='//*[@title="Show sharing options"]')
                sharefolder.click()

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
                driver.implicitly_wait(10) # seconds before quitting                

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
