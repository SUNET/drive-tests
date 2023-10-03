""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import unittest
import sunetdrive
from webdav3.client import Client

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
import time
import logging

class TestLoginSelenium(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_gss_login(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget()

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing gss')
            return

        fullnode = 'gss'

        loginurl = drv.get_node_login_url(fullnode)
        self.logger.info(f'Login url: {loginurl}')
        nodeuser = drv.get_seleniumuser(fullnode)
        nodepwd = drv.get_seleniumuserpassword(fullnode)
        
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

        # Check URL after login
        dashboardUrl = drv.get_dashboard_url(fullnode)
        currentUrl = driver.current_url
        # self.assertEqual(dashboardUrl, currentUrl)                

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
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                loginurl = drv.get_node_login_url(fullnode)
                self.logger.info(f'URL: {loginurl}')
                nodeuser = drv.get_seleniumuser(fullnode)
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

    def test_saml_eduid_nomfa(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget()

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml')
            return

        loginurl = drv.get_gss_url()
        self.logger.info(f'Login url: {loginurl}')

        samluser=drv.get_samlusername("eduidtest")
        samlpassword=drv.get_samluserpassword("eduidtest")
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
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

        wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(samluser)
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
        drv = sunetdrive.TestTarget()
        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing su saml')
            return

        loginurl = drv.get_gss_url()
        self.logger.info(f'Login url: {loginurl}')

        samluser=drv.get_samlusername("su")
        samlpassword=drv.get_samluserpassword("su")
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
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
