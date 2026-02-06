""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
from datetime import datetime
import unittest
import sunetnextcloud
from webdav3.client import Client
import pyotp
import pyscreeze
import pyautogui
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os
import logging
import yaml

drv = sunetnextcloud.TestTarget()
g_testtarget = os.environ.get('NextcloudTestTarget')
g_expectedResultsFile = 'expected.yaml'
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_version={}

class TestLoginMultiSelenium(unittest.TestCase):
    global drv, g_version
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    with open(g_expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    # Some class names of icons changed from Nextcloud 27 to 28
    drv = sunetnextcloud.TestTarget(g_testtarget)
    drv = drv
    g_version = expectedResults[drv.target]['status']['version']

    def test_logger(self):
        self.logger.info('self.logger.info test_logger')
        self.logger.info(f'Expecting Nextcloud version: {g_version}')
        pass

    def test_node_multi_login(self):
        delay = 30 # seconds
        for fullnode in drv.nodestotest:
            with self.subTest(mynode=fullnode):
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

                browser = 'chrome'
                sel = sunetnextcloud.SeleniumHelper(browser, fullnode)
                sel.delete_cookies()
                sel.nodelogin(sel.UserType.SELENIUM, mfaUser=True)
                driver = sel.driver

                if browser == 'chrome':
                    driver.set_window_size(1920, 1152)
                else:
                    driver.maximize_window()
                wait = WebDriverWait(driver, delay)

                try:
                    self.logger.info('Waiting for files app button')
                    wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="'+ drv.indexsuffix + '/apps/files/' +'"]')))
                    files = driver.find_element(By.XPATH, '//a[@href="'+ drv.indexsuffix + '/apps/files/' +'"]')
                    files.click()
                except Exception:
                    self.logger.warning('Files app button not found, do we have to totp again?')
                    totpselect = driver.find_element(By.XPATH, '//a[@href="'+ drv.indexsuffix + '/login/challenge/totp' +'"]')
                    self.logger.warning('Found TOTP selection dialogue')
                    totpselect.click()
                    totp = pyotp.TOTP(nodetotpsecret)
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu-entry')))
                    self.logger.info('All files visible!')
                except TimeoutException:
                    self.logger.warning('Loading of all files took too much time!')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + fullnode + "test_node_multi_login" + g_filename + ".png")
                    self.assertTrue(False)

                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@title="Show sharing options"]')))
                    sharefolder = driver.find_element(by=By.XPATH, value='//*[@title="Show sharing options"]')
                    sharefolder.click()
                    self.logger.info('Clicked on share folder')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sharing-entry__title')))
                    self.logger.info('Share link enabled!')
                except TimeoutException:
                    self.logger.info('No share link present!')

                wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
                logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
                logoutLink.click()
                self.logger.info('Logout complete')

                self.logger.info(f'{driver.current_url}')

                self.logger.info('TOTP Login done, testing normal login now')
                sel.delete_cookies()
                time.sleep(1)

                loginurl = drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = drv.get_seleniumuser(fullnode)
                self.logger.info(f'Username: {nodeuser}')
                nodepwd = drv.get_seleniumuserapppassword(fullnode)

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

                driver.get(loginurl)
                self.logger.info(f'Wait {delay}s before next login cycle')
                time.sleep(delay)

                sel.nodelogin(sel.UserType.SELENIUM, mfaUser=True)

                files = driver.find_element(By.XPATH, '//a[@href="'+ drv.indexsuffix + '/apps/files/' +'"]')
                files.click()

                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@title="Show sharing options"]')))
                    sharefolder = driver.find_element(by=By.XPATH, value='//*[@title="Show sharing options"]')
                    sharefolder.click()
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sharing-entry__title')))
                    self.logger.info('Share link enabled!')
                except TimeoutException:
                    self.logger.info('No share link present!')

                wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
                logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
                logoutLink.click()
                self.logger.info('Logout complete')

                self.logger.info(driver.current_url)
                driver.implicitly_wait(10) # seconds before quitting

if __name__ == '__main__':
    drv.run_tests(os.path.basename(__file__))
