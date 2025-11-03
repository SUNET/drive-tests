""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import HtmlTestRunner
import unittest
import requests
import sunetnextcloud
from webdav3.client import Client
import time
import json

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import FirefoxOptions
import os
import yaml
import logging
from datetime import datetime

drv = sunetnextcloud.TestTarget()

expectedResultsFile = 'expected.yaml'
geckodriver_path = "/snap/bin/geckodriver"
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_driver_timeout = 20
ocsheaders = { "OCS-APIRequest" : "true" } 

use_driver_service = False
if os.environ.get('SELENIUM_DRIVER_SERVICE') == 'True':
    use_driver_service = True

class TestUserlifecycleSelenium(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    with open(expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_node_lifecycle(self):
        delay = 30 # seconds
        # The class name of the share icon changed in Nextcloud 28
        version = self.expectedResults[drv.target]['status']['version']
        self.logger.info(f'Expected Nextcloud version: {version}')
        sharedClass = 'files-list__row-action-sharing-status'

        drv.browsers=['firefox']
        for browser in drv.browsers:
            with self.subTest(mybrowser=browser):
                for fullnode in drv.nodestotest:
                    with self.subTest(mynode=fullnode):
                        session = requests.Session()
                        addUserUrl = drv.get_users_url(fullnode)
                        self.logger.info(f'{self._testMethodName} {addUserUrl}')
                        nodeuser = drv.get_ocsuser(fullnode)
                        nodepwd = drv.get_ocsuserapppassword(fullnode)
                        addUserUrl = addUserUrl.replace("$USERNAME$", nodeuser)
                        addUserUrl = addUserUrl.replace("$PASSWORD$", nodepwd)

                        lifecycleuser = "__lifecycle_user_" + fullnode
                        lifecyclepwd = sunetnextcloud.Helper().get_random_string(12)

                        data = { 'userid': lifecycleuser, 'password': lifecyclepwd}

                        self.logger.info(f'Create cli user {lifecycleuser}')
                        try:
                            r = session.post(addUserUrl, headers=ocsheaders, data=data)
                        except Exception as error:
                            self.logger.error(f'Error posting to create cli user {error}')
                            return
                        try:
                            j = json.loads(r.text)
                            self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                            if (j["ocs"]["meta"]["statuscode"] == 102):
                                self.logger.warning('User already exists, delete and recreate')

                                userurl = drv.get_user_url(fullnode, lifecycleuser)
                                userurl = userurl.replace("$USERNAME$", nodeuser)
                                userurl = userurl.replace("$PASSWORD$", nodepwd)
                                r = session.delete(userurl, headers=ocsheaders)
                                j = json.loads(r.text)
                                self.logger.info(json.dumps(j, indent=4, sort_keys=True))
                                r = session.post(addUserUrl, headers=ocsheaders, data=data)
                                j = json.loads(r.text)
                                self.logger.info(json.dumps(j, indent=4, sort_keys=True))


                                if (j["ocs"]["meta"]["statuscode"] != 100):
                                    self.logger.info(f'Retry to delete cli user after {lifecycleuser} after error {j["ocs"]["meta"]["statuscode"]}')
                                    r = session.delete(userurl, headers=ocsheaders)
                                    j = json.loads(r.text)
                                    self.logger.info(json.dumps(j, indent=4, sort_keys=True))
                                    r = session.post(addUserUrl, headers=ocsheaders, data=data)
                                    j = json.loads(r.text)
                                    self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                            elif (j["ocs"]["meta"]["statuscode"] != 100):
                                self.logger.info(f'Retry to create cli user {lifecycleuser} after error {j["ocs"]["meta"]["statuscode"]}')
                                r = session.post(addUserUrl, headers=ocsheaders, data=data)
                                j = json.loads(r.text)
                                self.logger.info(json.dumps(j, indent=4, sort_keys=True))
                        except Exception as error:
                            self.logger.info(f'No JSON reply received from {fullnode}: {error}')
                            self.logger.info(r.text)
                            return

                        self.logger.info(f'TestID: Testing node {fullnode} with browser {browser}')

                        newOtpSecret = ''
                        sel = sunetnextcloud.SeleniumHelper(browser, fullnode)
                        sel.delete_cookies()
                        driver = sel.driver
                        if drv.target == 'test':
                            mfaUser = True
                        else:
                            mfaUser = False

                        newOtpSecret = sel.nodelogin(sel.UserType.BASIC, username=lifecycleuser,password=lifecyclepwd, mfaUser=mfaUser, addOtp=mfaUser, totpsecret=newOtpSecret)
                        wait = WebDriverWait(driver, delay)

                        lifecycleapppwd = sel.create_app_password()
                        self.logger.info(f'Got app password: {lifecycleapppwd} and secret {newOtpSecret}')

                        # Create folder for testing using webdav
                        try:
                            url = drv.get_webdav_url(fullnode, lifecycleuser)
                            options = {
                            'webdav_hostname': url,
                            'webdav_login' : lifecycleuser,
                            'webdav_password' : lifecycleapppwd 
                            }

                            client = Client(options)
                            dir = 'SharedFolder'
                            self.logger.info(f'Make and check directory: {dir}')
                            client.mkdir(dir)
                            self.assertEqual(client.list().count('SharedFolder/'), 1)
                        except Exception as error:
                            self.logger.error(f'Webdav error making shared folder {error}')                        

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

                        # Change user password and log on again
                        try:
                            wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
                            self.logger.info('user-menu clicked')
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Settings'))).click()
                            self.logger.info('Settings clicked')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Problem accessing user settings: {e}')

                        try:
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Security'))).click()
                            self.logger.info('Security clicked')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Problem accessing security settings: {e}')

                        # Type old and new password

                        lifecyclenewpwd = sunetnextcloud.Helper().get_random_string(12)

                        wait.until(EC.element_to_be_clickable((By.ID, 'old-pass'))).send_keys(lifecyclepwd)
                        wait.until(EC.element_to_be_clickable((By.ID, 'new-pass'))).send_keys(lifecyclenewpwd)
                        time.sleep(1)
                        wait.until(EC.element_to_be_clickable((By.ID, 'new-pass'))).send_keys(Keys.ENTER)
                        time.sleep(2)
                       
                        try:
                            wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
                            self.logger.info('user-menu clicked')
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Log out'))).click()
                            self.logger.info('Logout after password change complete')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Unable to log out: {e}')

                        # Open direct login url again
                        self.logger.info('Log in again after password change')
                        sel.nodelogin(sel.UserType.BASIC, username=lifecycleuser,password=lifecyclenewpwd, mfaUser=mfaUser, totpsecret=newOtpSecret)

                        wait = WebDriverWait(driver, delay)
                        try:
                            wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
                            self.logger.info('user-menu clicked')
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Log out'))).click()
                            self.logger.info('Logout after relogin complete')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Unable to log out: {e}')

                        currentUrl = driver.current_url
                        self.logger.info(f'Logout url: {currentUrl}')

                        driver.implicitly_wait(g_driver_timeout) # seconds before quitting
                        driver.quit()

                        self.logger.info(f'Delete user {lifecycleuser}')
                        userurl = drv.get_user_url(fullnode, lifecycleuser)
                        userurl = userurl.replace("$USERNAME$", nodeuser)
                        userurl = userurl.replace("$PASSWORD$", nodepwd)
                        r = session.delete(userurl, headers=ocsheaders)
                        j = json.loads(r.text)
                        self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                        if (j["ocs"]["meta"]["statuscode"] != 100):
                            self.logger.info(f'Retry to delete cli user after {lifecycleuser} after error {j["ocs"]["meta"]["statuscode"]}')
                            r = session.delete(userurl, headers=ocsheaders)
                            j = json.loads(r.text)
                            self.logger.info(json.dumps(j, indent=4, sort_keys=True))

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-userlifecycle", add_timestamp=False))
