""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import unittest
import sunetnextcloud
from webdav3.client import Client
import pyotp
import pyautogui
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import FirefoxOptions
import os
import yaml
import time
import logging
import json
import requests
from datetime import datetime

expectedResultsFile = 'expected.yaml'
geckodriver_path = "/snap/bin/geckodriver"
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_driver_timeout = 20
ocsheaders = { "OCS-APIRequest" : "true" } 

use_driver_service = False
if os.environ.get('SELENIUM_DRIVER_SERVICE') == 'True':
    use_driver_service = True

class TestProvisionNewSsoUser(unittest.TestCase):
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

    def test_saml_eduid_nomfa(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        node = 'extern'

        if len(drv.allnodes) == 1:
            if drv.allnodes[0] != node:
                self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml on {node}')
                return
        
        if drv.target == 'test':
            self.logger.warning(f'We are not testing eduid saml login in test until the new login portal is ready')
            return

        loginurl = drv.get_gss_url()
        self.logger.info(f'URL: {loginurl}')
        samluser=drv.get_samlusername("eduidtemp")
        samluseralias=drv.get_samluseralias("eduidtemp")
        self.logger.info(f'Username: {samluser} - {samluseralias}')
        samlpassword=drv.get_samluserpassword("eduidtemp")
        
        # Delete the user before we proceed
        session = requests.Session()

        ocsuser = drv.get_ocsuser(node)
        ocspwd = drv.get_ocsuserapppassword(node)
        
        self.logger.info(f'Delete sso user {samluseralias}')
        userurl = drv.get_user_url(node, samluseralias)
        userurl = userurl.replace("$USERNAME$", ocsuser)
        userurl = userurl.replace("$PASSWORD$", ocspwd)
        r = session.delete(userurl, headers=ocsheaders)
        j = json.loads(r.text)
        self.logger.info(json.dumps(j, indent=4, sort_keys=True))

        if (j["ocs"]["meta"]["statuscode"] != 100):
            self.logger.info(f'Retry to delete cli user {samluseralias} after error {j["ocs"]["meta"]["statuscode"]}')
            r = session.delete(userurl, headers=ocsheaders)
            j = json.loads(r.text)
            self.logger.info(json.dumps(j, indent=4, sort_keys=True))

        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            self.logger.error(f'Error initializing driver: {e}')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        self.deleteCookies(driver)
        driver.maximize_window()        
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)

        loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, loginLinkText))).click()
        driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
        driver.implicitly_wait(g_driver_timeout)
        
        wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("eduid.se", Keys.RETURN)
        driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
        driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
        self.logger.info(f'Email entered')
        wait.until(EC.element_to_be_clickable((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
        self.logger.info(f'Password entered, proceeding')
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time!')

        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
        dashboardUrl = drv.get_dashboard_url('extern')
        currentUrl = driver.current_url
        self.assertEqual(dashboardUrl, currentUrl)
        self.logger.info(f'{currentUrl}')

        wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        self.logger.info(f'Logout complete')

        currentUrl = driver.current_url
        self.logger.info(currentUrl)
        self.assertEqual(currentUrl, drv.get_gss_post_logout_url())
        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
        driver.close()
        self.logger.info(f'And done...')

    def test_portal_saml_eduid_nomfa(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        node = 'extern'

        if len(drv.allnodes) == 1:
            if drv.allnodes[0] != node:
                self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml on {node}')
                return
        
        if drv.target == 'prod':
            self.logger.warning(f'We only test {node} in production right now')
            return

        loginurl = drv.get_node_login_url(node, False)
        self.logger.info(f'URL: {loginurl}')
        samluser=drv.get_samlusername("eduidtemp")
        samluseralias=drv.get_samluseralias("eduidtemp")
        self.logger.info(f'Username: {samluser} - {samluseralias}')
        samlpassword=drv.get_samluserpassword("eduidtemp")      

        # Delete the user before we proceed
        session = requests.Session()

        ocsuser = drv.get_ocsuser(node)
        ocspwd = drv.get_ocsuserapppassword(node)
        
        self.logger.info(f'Delete sso user {samluseralias}')
        userurl = drv.get_user_url(node, samluseralias)
        userurl = userurl.replace("$USERNAME$", ocsuser)
        userurl = userurl.replace("$PASSWORD$", ocspwd)
        r = session.delete(userurl, headers=ocsheaders)
        j = json.loads(r.text)
        self.logger.info(json.dumps(j, indent=4, sort_keys=True))

        if (j["ocs"]["meta"]["statuscode"] != 100):
            self.logger.info(f'Retry to delete cli user {samluseralias} after error {j["ocs"]["meta"]["statuscode"]}')
            r = session.delete(userurl, headers=ocsheaders)
            j = json.loads(r.text)
            self.logger.info(json.dumps(j, indent=4, sort_keys=True))

        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            self.logger.error(f'Error initializing driver: {e}')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        self.deleteCookies(driver)
        driver.maximize_window()        
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)

        wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
        driver.implicitly_wait(g_driver_timeout)
        
        wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("eduid.se", Keys.RETURN)
        driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
        driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
        self.logger.info(f'Email entered')
        wait.until(EC.element_to_be_clickable((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
        self.logger.info(f'Password entered, proceeding')

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time!')

        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
        dashboardUrl = drv.get_dashboard_url(node)
        currentUrl = driver.current_url
        self.assertEqual(dashboardUrl, currentUrl)
        self.logger.info(f'{currentUrl}')

        wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        self.logger.info(f'Logout complete')

        currentUrl = driver.current_url
        self.logger.info(currentUrl)
        # Assert portal logout url
        self.assertTrue(currentUrl.startswith('https://portal.drive.test.sunet.se/?SAMLRequest'))
        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
        driver.close()
        self.logger.info(f'And done...')

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
