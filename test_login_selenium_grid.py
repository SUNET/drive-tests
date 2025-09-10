""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import unittest
import xmlrunner
import HtmlTestRunner
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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import FirefoxOptions
import os
import logging
from datetime import datetime

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

geckodriver_path = "/snap/bin/geckodriver"
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_driver_timeout = 20

use_driver_service = False
if os.environ.get('SELENIUM_DRIVER_SERVICE') == 'True':
    use_driver_service = True

class TestLoginSelenium(unittest.TestCase):
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
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_node_login(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        # The class name of the share icon changed in Nextcloud 28
        version = drv.expectedResults[drv.target]['status']['version']
        self.logger.info(f'Expected Nextcloud version: {version}')
        sharedClass = 'files-list__row-action-sharing-status'

        for browser in drv.browsers:
            with self.subTest(mybrowser=browser):
                for fullnode in drv.nodestotest:
                    with self.subTest(mynode=fullnode):
                        self.logger.info(f'TestID: Testing node {fullnode} with browser {browser}')
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
                        client.verify = drv.verify
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
                                if not drv.verify:
                                    options.add_argument("--ignore-certificate-errors")
                                driver = webdriver.Chrome(options=options)
                            elif browser == 'firefox':
                                if not use_driver_service:
                                    self.logger.info('Initialize Firefox driver without driver service')
                                    options = FirefoxOptions()
                                    if not drv.verify:
                                        options.add_argument("--ignore-certificate-errors")
                                    # options.add_argument("--headless")
                                    driver = webdriver.Firefox(options=options)
                                else:
                                    self.logger.info('Initialize Firefox driver using snap geckodriver and driver service')
                                    driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
                                    driver = webdriver.Firefox(service=driver_service, options=options)
                            else:
                                self.logger.error(f'Unknown browser {browser}')
                                self.assertTrue(False)
                        except Exception as e:
                            self.logger.error(f'Error initializing driver for {browser}: {e}')
                            self.assertTrue(False)
                        driver.maximize_window()
                        # driver2 = webdriver.Firefox()

                        sel = sunetnextcloud.SeleniumHelper(driver, fullnode)
                        sel.delete_cookies()
                        sel.nodelogin(sel.UserType.SELENIUM)

                        wait = WebDriverWait(driver, delay)
                        files = driver.find_element(By.XPATH, '//a[@href="' + drv.indexsuffix + '/apps/files/' +'"]')
                        files.click()

                        try:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu-entry')))
                            self.logger.info('All files visible!')
                        except TimeoutException:
                            self.logger.info('Loading of all files took too much time!')

                        try:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, sharedClass)))
                            sharefolder = driver.find_element(by=By.CLASS_NAME, value=sharedClass)
                            sharefolder.click()
                            self.logger.info('Clicked on share folder')
                        except Exception as error:
                            self.logger.info(f'{sharedClass} not found: {error}')

                        try:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sharing-entry__title')))
                            self.logger.info('Share link enabled!')
                        except TimeoutException:
                            self.logger.info('No share link present!')

                        try:
                            wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
                            self.logger.info('user-menu clicked')
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Log out'))).click()
                            self.logger.info('Logout complete')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Unable to log out: {e}')

                        currentUrl = driver.current_url
                        self.logger.info(f'Logout url: {currentUrl}')

                        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
                        driver.quit()

    def test_saml_eduid_nomfa(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()

        if len(drv.allnodes) == 1:
            self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml')
            return
        
        loginurl = drv.get_login_url()
        self.logger.info(f'URL: {loginurl}')
        samluser=drv.get_samlusername("eduidtest")
        self.logger.info(f'Username: {samluser}')
        samlpassword=drv.get_samluserpassword("eduidtest")
        
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

        # loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

        # wait.until(EC.element_to_be_clickable((By.LINK_TEXT, loginLinkText))).click()
        # driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
        driver.implicitly_wait(g_driver_timeout)
        
        wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("eduid.se", Keys.RETURN)
        driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
        driver.implicitly_wait(g_driver_timeout)

        wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
        self.logger.info('Email entered')
        wait.until(EC.element_to_be_clickable((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
        self.logger.info('Password entered, proceeding')
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info('App menu is ready!')
        except TimeoutException:
            self.logger.info('Loading of app menu took too much time!')

        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
        dashboardUrl = drv.get_dashboard_url('extern')
        currentUrl = driver.current_url
        self.assertEqual(dashboardUrl, currentUrl)
        self.logger.info(f'{currentUrl}')

        wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        self.logger.info('Logout complete')

        currentUrl = driver.current_url
        self.logger.info(currentUrl)
        self.assertEqual(currentUrl, drv.get_post_logout_url())
        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
        driver.close()
        self.logger.info('And done...')

    def test_saml_su(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        nodeName = 'su'
        if len(drv.allnodes) == 1:
            if drv.allnodes[0] != nodeName:
                self.logger.info(f'Only testing {drv.allnodes[0]}, not testing su saml')
                return
            
        for browser in drv.browsers:
            totp = 0
            loginurl = drv.get_login_url()
            self.logger.info(f'URL: {loginurl}')
            samluser=drv.get_samlusername(nodeName)
            self.logger.info(f'Username: {samluser}')
            samlpassword=drv.get_samluserpassword(nodeName)

            try:
                if browser == 'chrome':
                    options = Options()
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-extensions")
                    driver = webdriver.Chrome(options=options)
                elif browser == 'firefox':
                    if not use_driver_service:
                        self.logger.info('Initialize Firefox driver without driver service')
                        options = FirefoxOptions()
                        # options.add_argument("--headless")
                        driver = webdriver.Firefox(options=options)
                    else:
                        self.logger.info('Initialize Firefox driver using snap geckodriver and driver service')
                        driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
                        driver = webdriver.Firefox(service=driver_service, options=options)
                else:
                    self.logger.error(f'Unknown browser {browser}')
                    self.assertTrue(False)
            except Exception as e:
                self.logger.error(f'Error initializing driver for {browser}: {e}')
                self.assertTrue(False)

            self.deleteCookies(driver)
            driver.maximize_window()        
            driver.get(loginurl)

            wait = WebDriverWait(driver, delay)

            wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
            driver.implicitly_wait(g_driver_timeout)
            
            wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("su.se", Keys.RETURN)
            driver.implicitly_wait(g_driver_timeout)

            driver.implicitly_wait(g_driver_timeout)

            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
            driver.implicitly_wait(g_driver_timeout)

            wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
            wait.until(EC.element_to_be_clickable((By.ID, 'password'))).send_keys(samlpassword + Keys.ENTER)

            # Wait for TOTP screen
            requireTotp = False
            try:
                self.logger.info('Check if TOTP selection dialogue is visible')
                wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="' + drv.indexsuffix + '/login/challenge/totp?redirect_url=' + drv.indexsuffix + '/apps/dashboard/' +'"]'))).click()
                self.logger.info('Found and clicked on TOTP selection dialogue')
                requireTotp = True
            except Exception as error:
                self.logger.info(f'No need to select TOTP provider: {error}')
                requireTotp = False

            if requireTotp:
                nodetotpsecret = drv.get_samlusertotpsecret(nodeName)
                totp = pyotp.TOTP(nodetotpsecret)
                while totp == pyotp.TOTP(nodetotpsecret):
                    self.logger.warning('We already used this TOTP, so we wait until it changes')
                    time.sleep(10)

                wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(totp.now() + Keys.ENTER)
                self.logger.info('TOTP entered')

            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                self.logger.info('App menu is ready!')
            except TimeoutException:
                self.logger.warning('Loading of app menu took too much time! Try TOTP again')
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(totp.now() + Keys.ENTER)
                self.logger.info('TOTP entered again, wait for the app menu')
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))

            driver.implicitly_wait(g_driver_timeout) # seconds before quitting
            dashboardUrl = drv.get_dashboard_url('su')
            currentUrl = driver.current_url
            try:
                self.assertEqual(dashboardUrl, currentUrl)
            except Exception as error:
                self.assertEqual(dashboardUrl + '#/', currentUrl)
                self.logger.warning(f'Dashboard URL contains trailing #, likely due to the tasks app: {error}')
                self.logger.info(f'{currentUrl}')

            wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
            logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
            logoutLink.click()
            self.logger.info('Logout complete')
            currentUrl = driver.current_url
            self.logger.info(currentUrl)
            self.assertEqual(currentUrl, drv.get_post_logout_url())
            driver.implicitly_wait(g_driver_timeout) # seconds before quitting
            driver.close()
            self.logger.info('And done...')

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-selenium", add_timestamp=False))
