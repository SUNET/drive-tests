""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import unittest
import sunetnextcloud
from webdav3.client import Client
import pyotp

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import os
import yaml
import time
import logging

expectedResultsFile = 'expected.yaml'

class TestLoginSelenium(unittest.TestCase):
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
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_gss_login(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        if drv.testgss == False:
            self.logger.info('Not testing gss')
            return

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing gss')
            return

        fullnode = 'gss'

        loginurl = drv.get_node_login_url(fullnode)
        self.logger.info(f'URL: {loginurl}')
        nodeuser = drv.get_seleniumuser(fullnode)
        self.logger.info(f'Username: {nodeuser}')
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        self.deleteCookies(driver)
        driver.maximize_window()        
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

        # Check URL after login
        dashboardUrl = drv.get_dashboard_url(fullnode)
        currentUrl = driver.current_url
        # self.assertEqual(dashboardUrl, currentUrl)                

        try:
            myElem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time!')

        files = driver.find_element(By.XPATH, '//a[@href="' + drv.indexsuffix + '/apps/files/' +'"]')
        files.click()

        try:
            myElem = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
            self.logger.info(f'All files visible!')
        except TimeoutException:
            self.logger.info(f'Loading of all files took too much time!')


        wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        self.logger.info(f'Logout complete')

        currentUrl = driver.current_url
        self.logger.info(driver.current_url)
        self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())
        driver.implicitly_wait(10) # seconds before quitting

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

        for browser in drv.browsers:
            with self.subTest(mybrowser=browser):
                for fullnode in drv.fullnodes:
                    with self.subTest(mynode=fullnode):
                        self.logger.info(f'Testing node {fullnode} with browser {browser}')
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
                            if browser == 'chrome':
                                options = Options()
                                options.add_argument("--no-sandbox")
                                options.add_argument("--disable-dev-shm-usage")
                                options.add_argument("--disable-gpu")
                                options.add_argument("--disable-extensions")
                                driver = webdriver.Chrome(options=options)
                            elif browser == 'firefox':
                                driver = webdriver.Firefox()
                            else:
                                self.logger.error(f'Unknown browser {browser}')
                                self.assertTrue(False)
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

                        try:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                            self.logger.info(f'App menu is ready!')
                        except TimeoutException:
                            self.logger.info(f'Loading of app menu took too much time!')

                        # Check URLs after login
                        dashboardUrl = drv.get_dashboard_url(fullnode)
                        currentUrl = driver.current_url
                        # self.assertEqual(dashboardUrl, currentUrl)                

                        files = driver.find_element(By.XPATH, '//a[@href="' + drv.indexsuffix + '/apps/files/' +'"]')
                        files.click()

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
                            self.logger.info(f'{sharedClass} not found')

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
                        elif fullnode == 'swamid' or fullnode == 'extern' or fullnode == 'sunet':
                            pass
                        elif (self.expectedResults['global']['testGss'] == True) and (len(drv.allnodes) == 1):
                            self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())
                        elif (self.expectedResults['global']['testGss'] == False) | (len(drv.allnodes) == 1):
                            if simpleLogoutUrl == True:
                                self.assertEqual(driver.current_url, drv.get_node_post_logout_simple_url(fullnode))
                            else:
                                self.assertEqual(driver.current_url, drv.get_node_post_logout_url(fullnode))
                        else:
                            self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())
                        driver.implicitly_wait(10) # seconds before quitting
                        driver.quit()

    def test_saml_eduid_nomfa(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml')
            return
        
        if drv.target == 'test':
            self.logger.warning(f'We are not testing eduid saml login in test until the new login portal is ready')
            return

        loginurl = drv.get_gss_url()
        self.logger.info(f'URL: {loginurl}')
        samluser=drv.get_samlusername("eduidtest")
        self.logger.info(f'Username: {samluser}')
        samlpassword=drv.get_samluserpassword("eduidtest")
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        self.deleteCookies(driver)
        driver.maximize_window()        
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)

        loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

        wait.until(EC.presence_of_element_located((By.LINK_TEXT, loginLinkText))).click()
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
        driver.implicitly_wait(10)
        
        wait.until(EC.presence_of_element_located((By.ID, 'searchinput'))).send_keys("eduid.se", Keys.RETURN)
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'label-url'))).click()
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(samluser)
        self.logger.info(f'Email entered')
        wait.until(EC.presence_of_element_located((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
        self.logger.info(f'Password entered, proceeding')
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time!')

        driver.implicitly_wait(10) # seconds before quitting
        dashboardUrl = drv.get_dashboard_url('extern')
        currentUrl = driver.current_url
        self.assertEqual(dashboardUrl, currentUrl)
        self.logger.info(f'{driver.current_url}')

        wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        self.logger.info(f'Logout complete')

        currentUrl = driver.current_url
        self.logger.info(driver.current_url)
        self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())
        driver.implicitly_wait(10) # seconds before quitting

        driver.implicitly_wait(10) # seconds before quitting

    def test_portal_saml_eduid_nomfa(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml')
            return
        
        if drv.target == 'prod':
            self.logger.warning(f'We are not testing eduid saml login in prod until the new login portal is ready')
            return

        loginurl = drv.get_node_login_url('extern', False)
        self.logger.info(f'URL: {loginurl}')
        samluser=drv.get_samlusername("eduidtest")
        self.logger.info(f'Username: {samluser}')
        samlpassword=drv.get_samluserpassword("eduidtest")
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        self.deleteCookies(driver)
        driver.maximize_window()        
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)

        # loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

        # wait.until(EC.presence_of_element_located((By.LINK_TEXT, loginLinkText))).click()
        # driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
        driver.implicitly_wait(10)
        
        wait.until(EC.presence_of_element_located((By.ID, 'searchinput'))).send_keys("eduid.se", Keys.RETURN)
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'label-url'))).click()
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(samluser)
        self.logger.info(f'Email entered')
        wait.until(EC.presence_of_element_located((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
        self.logger.info(f'Password entered, proceeding')
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time!')

        driver.implicitly_wait(10) # seconds before quitting
        dashboardUrl = drv.get_dashboard_url('extern')
        currentUrl = driver.current_url
        self.assertEqual(dashboardUrl, currentUrl)
        self.logger.info(f'{driver.current_url}')

        wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        self.logger.info(f'Logout complete')

        currentUrl = driver.current_url
        self.logger.info(driver.current_url)
        self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())
        driver.implicitly_wait(10) # seconds before quitting

        driver.implicitly_wait(10) # seconds before quitting

    def test_saml_su_nomfa(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        nodeName = 'su'
        if len(drv.allnodes) == 1:
            if drv.allnodes[0] != nodeName:
                self.logger.info(f'Only testing {drv.allnodes[0]}, not testing su saml')
                return

        loginurl = drv.get_gss_url()
        self.logger.info(f'URL: {loginurl}')
        samluser=drv.get_samlusername(nodeName)
        self.logger.info(f'Username: {samluser}')
        samlpassword=drv.get_samluserpassword(nodeName)
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        self.deleteCookies(driver)
        driver.maximize_window()        
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)

        loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

        wait.until(EC.presence_of_element_located((By.LINK_TEXT, loginLinkText))).click()
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
        driver.implicitly_wait(10)
        
        wait.until(EC.presence_of_element_located((By.ID, 'searchinput'))).send_keys("su.se", Keys.RETURN)
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'label-url'))).click()
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(samluser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(samlpassword + Keys.ENTER)
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

        # Wait for TOTP screen
        requireTotp = False
        try:
            self.logger.info(f'Check if TOTP selection dialogue is visible')
            totpselect = driver.find_element(By.XPATH, '//a[@href="' + drv.indexsuffix + '/login/challenge/totp?redirect_url=' + drv.indexsuffix + '/apps/dashboard/' +'"]')
            self.logger.warning(f'Found TOTP selection dialogue')
            requireTotp = True
            totpselect.click()
        except:
            self.logger.info(f'No need to select TOTP provider')

        if requireTotp:
            nodetotpsecret = drv.get_samlusertotpsecret(nodeName)
            totp = pyotp.TOTP(nodetotpsecret)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time!')

        driver.implicitly_wait(10) # seconds before quitting
        dashboardUrl = drv.get_dashboard_url('su')
        currentUrl = driver.current_url
        try:
            self.assertEqual(dashboardUrl, currentUrl)
        except:
            self.assertEqual(dashboardUrl + '#/', currentUrl)
            self.logger.warning(f'Dashboard URL contains trailing #, likely due to the tasks app')
        self.logger.info(f'{driver.current_url}')

        wait.until(EC.presence_of_element_located((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        self.logger.info(f'Logout complete')
        currentUrl = driver.current_url
        self.logger.info(driver.current_url)
        self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())
        driver.implicitly_wait(10) # seconds before quitting

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
