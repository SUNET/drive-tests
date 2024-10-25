""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import unittest
import requests
import sunetnextcloud
from webdav3.client import Client
import pyotp
import pyautogui
import time
import json

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
from datetime import datetime

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

    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        self.logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        self.logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_node_lifecycle(self):
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

        drv.browsers=['firefox']
        for browser in drv.browsers:
            with self.subTest(mybrowser=browser):
                for fullnode in drv.fullnodes:
                    with self.subTest(mynode=fullnode):
                        session = requests.Session()
                        addUserUrl = drv.get_add_user_url(fullnode)
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
                        except:
                            self.logger.error(f'Error posting to create cli user')
                            return
                        try:
                            j = json.loads(r.text)
                            self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                            if (j["ocs"]["meta"]["statuscode"] == 102):
                                self.logger.warning(f'User already exists, delete and recreate')

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
                                r = session.post(url, headers=ocsheaders, data=data)
                                j = json.loads(r.text)
                                self.logger.info(json.dumps(j, indent=4, sort_keys=True))
                        except:
                            self.logger.info(f"No JSON reply received from {fullnode}")
                            self.logger.info(r.text)
                            return

                        self.logger.info(f'TestID: Testing node {fullnode} with browser {browser}')
                        loginurl = drv.get_node_login_url(fullnode)

                        try:
                            if browser == 'chrome':
                                options = Options()
                                options.add_argument("--no-sandbox")
                                options.add_argument("--disable-dev-shm-usage")
                                options.add_argument("--disable-gpu")
                                options.add_argument("--disable-extensions")
                                driver = webdriver.Chrome(options=options)
                            elif browser == 'firefox':
                                if use_driver_service == False:
                                    self.logger.info(f'Initialize Firefox driver without driver service')
                                    options = FirefoxOptions()
                                    # options.add_argument("--headless")
                                    driver = webdriver.Firefox(options=options)
                                else:
                                    self.logger.info(f'Initialize Firefox driver using snap geckodriver and driver service')
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
                        sel.nodelogin(sel.UserType.BASIC, username=lifecycleuser,password=lifecyclepwd)
                        wait = WebDriverWait(driver, delay)

                        # Create folder for testing using webdav
                        try:
                            url = drv.get_webdav_url(fullnode, lifecycleuser)
                            options = {
                            'webdav_hostname': url,
                            'webdav_login' : lifecycleuser,
                            'webdav_password' : lifecyclepwd 
                            }

                            client = Client(options)
                            dir = 'SharedFolder'
                            self.logger.info(f'Make and check directory: {dir}')
                            client.mkdir(dir)
                            self.assertEqual(client.list().count('SharedFolder/'), 1)
                        except:
                            self.logger.error(f'Webdav error making shared folder')                        

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

                        # Change user password and log on again
                        try:
                            wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
                            self.logger.info(f'user-menu clicked')
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Settings'))).click()
                            self.logger.info(f'Settings clicked')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Problem accessing user settings: {e}')

                        try:
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Security'))).click()
                            self.logger.info(f'Security clicked')
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
                            self.logger.info(f'user-menu clicked')
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Log out'))).click()
                            self.logger.info(f'Logout after password change complete')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Unable to log out: {e}')

                        # Open direct login url again
                        self.logger.info(f'Log in again after password change')
                        sel.nodelogin(sel.UserType.BASIC, username=lifecycleuser,password=lifecyclenewpwd)
                        wait = WebDriverWait(driver, delay)
                        try:
                            wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
                            self.logger.info(f'user-menu clicked')
                            wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Log out'))).click()
                            self.logger.info(f'Logout after relogin complete')
                            time.sleep(1)
                        except Exception as e:
                            self.logger.error(f'Unable to log out: {e}')

                        currentUrl = driver.current_url
                        self.logger.info(f'Logout url: {currentUrl}')

                        if fullnode == 'scilifelab':
                            self.assertEqual(currentUrl, drv.get_node_post_logout_saml_url(fullnode))
                        elif fullnode == 'kau':
                            self.assertEqual(currentUrl, drv.get_node_post_logout_url(fullnode))
                        elif fullnode == 'swamid' or fullnode == 'extern' or fullnode == 'sunet' or fullnode == 'vr' or fullnode == 'su':
                            pass
                        elif (self.expectedResults['global']['testGss'] == True) and (len(drv.allnodes) == 1):
                            self.assertEqual(currentUrl, drv.get_gss_post_logout_url())
                        elif (self.expectedResults['global']['testGss'] == False) | (len(drv.allnodes) == 1):
                            if simpleLogoutUrl == True:
                                self.assertEqual(currentUrl, drv.get_node_post_logout_simple_url(fullnode))
                            else:
                                self.assertEqual(currentUrl, drv.get_node_post_logout_url(fullnode))
                        else:
                            self.assertEqual(currentUrl, drv.get_gss_post_logout_url())
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


    # def test_portal_direct_login(self):
    #     delay = 30 # seconds
    #     drv = sunetnextcloud.TestTarget()
    #     # The class name of the share icon changed in Nextcloud 28
    #     version = self.expectedResults[drv.target]['status']['version']
    #     self.logger.info(f'Expected Nextcloud version: {version}')
    #     if version.startswith('27'):
    #         sharedClass = 'icon-shared'
    #         simpleLogoutUrl = False
    #         self.logger.info(f'We are on Nextcloud 27 and are not using the simple logout url')
    #     else:
    #         # This will select the first available sharing button
    #         sharedClass = 'files-list__row-action-sharing-status'
    #         simpleLogoutUrl = True
    #         self.logger.info(f'We are on Nextcloud 28 and are therefore using the simple logout url')

    #     for browser in drv.browsers:
    #         with self.subTest(mybrowser=browser):
    #             for fullnode in drv.fullnodes:
    #                 with self.subTest(mynode=fullnode):
    #                     self.logger.info(f'TestID: Testing node {fullnode} with browser {browser}')
    #                     loginurl = drv.get_portal_login_url()
    #                     self.logger.info(f'URL: {loginurl}')
    #                     nodeuser = drv.get_seleniumuser(fullnode)
    #                     self.logger.info(f'Username: {nodeuser}')
    #                     nodepwd = drv.get_seleniumuserpassword(fullnode)

    #                     # Create folder for testing using webdav
    #                     url = drv.get_webdav_url(fullnode, nodeuser)
    #                     options = {
    #                     'webdav_hostname': url,
    #                     'webdav_login' : nodeuser,
    #                     'webdav_password' : nodepwd 
    #                     }

    #                     client = Client(options)
    #                     dir = 'SharedFolder'
    #                     self.logger.info(f'Make and check directory: {dir}')
    #                     client.mkdir(dir)
    #                     self.assertEqual(client.list().count('SharedFolder/'), 1)

    #                     try:
    #                         if browser == 'chrome':
    #                             options = Options()
    #                             options.add_argument("--no-sandbox")
    #                             options.add_argument("--disable-dev-shm-usage")
    #                             options.add_argument("--disable-gpu")
    #                             options.add_argument("--disable-extensions")
    #                             driver = webdriver.Chrome(options=options)
    #                         elif browser == 'firefox':
    #                             if use_driver_service == False:
    #                                 self.logger.info(f'Initialize Firefox driver without driver service')
    #                                 options = FirefoxOptions()
    #                                 options.add_argument("--headless")
    #                                 driver = webdriver.Firefox(options=options)
    #                             else:
    #                                 self.logger.info(f'Initialize Firefox driver using snap geckodriver and driver service')
    #                                 driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
    #                                 driver = webdriver.Firefox(service=driver_service, options=options)
    #                         else:
    #                             self.logger.error(f'Unknown browser {browser}')
    #                             self.assertTrue(False)
    #                     except Exception as e:
    #                         self.logger.error(f'Error initializing driver for {browser}: {e}')
    #                         self.assertTrue(False)
    #                     driver.maximize_window()
    #                     # driver2 = webdriver.Firefox()
    #                     self.deleteCookies(driver)
    #                     driver.get(loginurl)

    #                     wait = WebDriverWait(driver, delay)
    #                     wait.until(EC.element_to_be_clickable((By.ID, 'site'))).send_keys(fullnode + Keys.ENTER)

    #                     self.logger.info(f'Check direct login checkbox')

    #                     wait.until(EC.element_to_be_clickable((By.ID, 'direct_login'))).click()

    #                     nodeloginurl = drv.get_node_login_url(fullnode, True)
    #                     self.logger.info(f'Locating button for {nodeloginurl}')
    #                     loginbutton = driver.find_element(By.XPATH, '//a[@href="' + nodeloginurl +'"]')
    #                     loginbutton.click()

    #                     wait.until(EC.element_to_be_clickable((By.ID, 'user'))).send_keys(nodeuser)
    #                     wait.until(EC.element_to_be_clickable((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

    #                     try:
    #                         wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
    #                         self.logger.info(f'App menu is ready!')
    #                     except TimeoutException:
    #                         self.logger.info(f'Loading of app menu took too much time!')

    #                     # Check URLs after login
    #                     dashboardUrl = drv.get_dashboard_url(fullnode)
    #                     currentUrl = driver.current_url
    #                     # self.assertEqual(dashboardUrl, currentUrl)                

    #                     files = driver.find_element(By.XPATH, '//a[@href="' + drv.indexsuffix + '/apps/files/' +'"]')
    #                     files.click()

    #                     try:
    #                         wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu-entry')))
    #                         self.logger.info(f'All files visible!')
    #                     except TimeoutException:
    #                         self.logger.info(f'Loading of all files took too much time!')

    #                     try:
    #                         wait.until(EC.presence_of_element_located((By.CLASS_NAME, sharedClass)))
    #                         sharefolder = driver.find_element(by=By.CLASS_NAME, value=sharedClass)
    #                         sharefolder.click()
    #                         self.logger.info(f'Clicked on share folder')
    #                     except:
    #                         self.logger.info(f'{sharedClass} not found')

    #                     try:
    #                         wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sharing-entry__title')))
    #                         self.logger.info(f'Share link enabled!')
    #                     except TimeoutException:
    #                         self.logger.info(f'No share link present!')

    #                     wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
    #                     logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
    #                     logoutLink.click()
    #                     self.logger.info(f'Logout complete')

    #                     currentUrl = driver.current_url
    #                     self.logger.info(currentUrl)

    #                     if fullnode == 'scilifelab':
    #                         self.assertEqual(currentUrl, drv.get_node_post_logout_saml_url(fullnode))
    #                     elif fullnode == 'kau':
    #                         self.assertEqual(currentUrl, drv.get_node_post_logout_url(fullnode))
    #                     elif fullnode == 'swamid' or fullnode == 'extern' or fullnode == 'sunet' or fullnode == 'vr' or fullnode == 'su':
    #                         pass
    #                     elif (self.expectedResults['global']['testGss'] == True) and (len(drv.allnodes) == 1):
    #                         self.assertEqual(currentUrl, drv.get_gss_post_logout_url())
    #                     elif (self.expectedResults['global']['testGss'] == False) | (len(drv.allnodes) == 1):
    #                         if simpleLogoutUrl == True:
    #                             self.assertEqual(currentUrl, drv.get_node_post_logout_simple_url(fullnode))
    #                         else:
    #                             self.assertEqual(currentUrl, drv.get_node_post_logout_url(fullnode))
    #                     else:
    #                         self.assertEqual(currentUrl, drv.get_gss_post_logout_url())
    #                     driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #                     driver.quit()

    # def test_saml_eduid_nomfa(self):
    #     self.logger.info(f'TestID: {self._testMethodName}')
    #     delay = 30 # seconds
    #     drv = sunetnextcloud.TestTarget()

    #     if len(drv.allnodes) == 1:
    #         self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml')
    #         return
        
    #     if drv.target == 'test':
    #         self.logger.warning(f'We are not testing eduid saml login in test until the new login portal is ready')
    #         return

    #     loginurl = drv.get_gss_url()
    #     self.logger.info(f'URL: {loginurl}')
    #     samluser=drv.get_samlusername("eduidtest")
    #     self.logger.info(f'Username: {samluser}')
    #     samlpassword=drv.get_samluserpassword("eduidtest")
        
    #     try:
    #         options = Options()
    #         driver = webdriver.Chrome(options=options)
    #     except Exception as e:
    #         self.logger.error(f'Error initializing driver: {e}')
    #         self.assertTrue(False)
    #     # driver2 = webdriver.Firefox()
    #     self.deleteCookies(driver)
    #     driver.maximize_window()        
    #     driver.get(loginurl)

    #     wait = WebDriverWait(driver, delay)

    #     loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

    #     wait.until(EC.element_to_be_clickable((By.LINK_TEXT, loginLinkText))).click()
    #     driver.implicitly_wait(g_driver_timeout)

    #     wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
    #     driver.implicitly_wait(g_driver_timeout)
        
    #     wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("eduid.se", Keys.RETURN)
    #     driver.implicitly_wait(g_driver_timeout)

    #     wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
    #     driver.implicitly_wait(g_driver_timeout)

    #     wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
    #     self.logger.info(f'Email entered')
    #     wait.until(EC.element_to_be_clickable((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
    #     self.logger.info(f'Password entered, proceeding')
    #     # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

    #     try:
    #         wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
    #         self.logger.info(f'App menu is ready!')
    #     except TimeoutException:
    #         self.logger.info(f'Loading of app menu took too much time!')

    #     driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #     dashboardUrl = drv.get_dashboard_url('extern')
    #     currentUrl = driver.current_url
    #     self.assertEqual(dashboardUrl, currentUrl)
    #     self.logger.info(f'{currentUrl}')

    #     wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
    #     logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
    #     logoutLink.click()
    #     self.logger.info(f'Logout complete')

    #     currentUrl = driver.current_url
    #     self.logger.info(currentUrl)
    #     self.assertEqual(currentUrl, drv.get_gss_post_logout_url())
    #     driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #     driver.close()
    #     self.logger.info(f'And done...')

    # def test_portal_saml_eduid_nomfa(self):
    #     self.logger.info(f'TestID: {self._testMethodName}')
    #     delay = 30 # seconds
    #     drv = sunetnextcloud.TestTarget()
    #     node = 'swamid'

    #     if len(drv.allnodes) == 1:
    #         self.logger.info(f'Only testing {drv.allnodes[0]}, not testing eduid saml')
    #         return
        
    #     if drv.target == 'test':
    #         self.logger.warning(f'We only test {node} in production right now')
    #         return

    #     loginurl = drv.get_node_login_url(node, False)
    #     self.logger.info(f'URL: {loginurl}')
    #     samluser=drv.get_samlusername("eduidtest")
    #     self.logger.info(f'Username: {samluser}')
    #     samlpassword=drv.get_samluserpassword("eduidtest")
        
    #     try:
    #         options = Options()
    #         driver = webdriver.Chrome(options=options)
    #     except Exception as e:
    #         self.logger.error(f'Error initializing driver: {e}')
    #         self.assertTrue(False)
    #     # driver2 = webdriver.Firefox()
    #     self.deleteCookies(driver)
    #     driver.maximize_window()        
    #     driver.get(loginurl)

    #     wait = WebDriverWait(driver, delay)

    #     wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
    #     driver.implicitly_wait(g_driver_timeout)
        
    #     wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("eduid.se", Keys.RETURN)
    #     driver.implicitly_wait(g_driver_timeout)

    #     wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
    #     driver.implicitly_wait(g_driver_timeout)

    #     wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
    #     self.logger.info(f'Email entered')
    #     wait.until(EC.element_to_be_clickable((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
    #     self.logger.info(f'Password entered, proceeding')

    #     try:
    #         wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
    #         self.logger.info(f'App menu is ready!')
    #     except TimeoutException:
    #         self.logger.info(f'Loading of app menu took too much time!')

    #     driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #     dashboardUrl = drv.get_dashboard_url(node)
    #     currentUrl = driver.current_url
    #     self.assertEqual(dashboardUrl, currentUrl)
    #     self.logger.info(f'{currentUrl}')

    #     wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
    #     logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
    #     logoutLink.click()
    #     self.logger.info(f'Logout complete')

    #     currentUrl = driver.current_url
    #     self.logger.info(currentUrl)
    #     # Assert portal logout url
    #     self.assertTrue(currentUrl.startswith('https://portal.drive.sunet.se/?SAMLRequest'))
    #     driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #     driver.close()
    #     self.logger.info(f'And done...')

    # def test_saml_su(self):
    #     self.logger.info(f'TestID: {self._testMethodName}')
    #     delay = 30 # seconds
    #     drv = sunetnextcloud.TestTarget()
    #     nodeName = 'su'
    #     if len(drv.allnodes) == 1:
    #         if drv.allnodes[0] != nodeName:
    #             self.logger.info(f'Only testing {drv.allnodes[0]}, not testing su saml')
    #             return
            
    #     if drv.target == 'test':
    #         self.logger.info(f'SU switched to portal login in test, we are not testing anything here')
    #         return

    #     for browser in drv.browsers:
    #         totp = 0
    #         loginurl = drv.get_gss_url()
    #         self.logger.info(f'URL: {loginurl}')
    #         samluser=drv.get_samlusername(nodeName)
    #         self.logger.info(f'Username: {samluser}')
    #         samlpassword=drv.get_samluserpassword(nodeName)

    #         try:
    #             if browser == 'chrome':
    #                 options = Options()
    #                 options.add_argument("--no-sandbox")
    #                 options.add_argument("--disable-dev-shm-usage")
    #                 options.add_argument("--disable-gpu")
    #                 options.add_argument("--disable-extensions")
    #                 driver = webdriver.Chrome(options=options)
    #             elif browser == 'firefox':
    #                 if use_driver_service == False:
    #                     self.logger.info(f'Initialize Firefox driver without driver service')
    #                     options = FirefoxOptions()
    #                     # options.add_argument("--headless")
    #                     driver = webdriver.Firefox(options=options)
    #                 else:
    #                     self.logger.info(f'Initialize Firefox driver using snap geckodriver and driver service')
    #                     driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
    #                     driver = webdriver.Firefox(service=driver_service, options=options)
    #             else:
    #                 self.logger.error(f'Unknown browser {browser}')
    #                 self.assertTrue(False)
    #         except Exception as e:
    #             self.logger.error(f'Error initializing driver for {browser}: {e}')
    #             self.assertTrue(False)

    #         self.deleteCookies(driver)
    #         driver.maximize_window()        
    #         driver.get(loginurl)

    #         wait = WebDriverWait(driver, delay)

    #         loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

    #         wait.until(EC.element_to_be_clickable((By.LINK_TEXT, loginLinkText))).click()
    #         driver.implicitly_wait(g_driver_timeout)

    #         wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
    #         driver.implicitly_wait(g_driver_timeout)
            
    #         wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("su.se", Keys.RETURN)
    #         driver.implicitly_wait(g_driver_timeout)

    #         driver.implicitly_wait(g_driver_timeout)

    #         wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
    #         driver.implicitly_wait(g_driver_timeout)

    #         wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
    #         wait.until(EC.element_to_be_clickable((By.ID, 'password'))).send_keys(samlpassword + Keys.ENTER)

    #         # Wait for TOTP screen
    #         requireTotp = False
    #         try:
    #             self.logger.info(f'Check if TOTP selection dialogue is visible')
    #             wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="' + drv.indexsuffix + '/login/challenge/totp?redirect_url=' + drv.indexsuffix + '/apps/dashboard/' +'"]'))).click()
    #             self.logger.info(f'Found and clicked on TOTP selection dialogue')
    #             requireTotp = True
    #         except:
    #             self.logger.info(f'No need to select TOTP provider')
    #             requireTotp = False

    #         if requireTotp:
    #             nodetotpsecret = drv.get_samlusertotpsecret(nodeName)
    #             totp = pyotp.TOTP(nodetotpsecret)
    #             while totp == pyotp.TOTP(nodetotpsecret):
    #                 self.logger.warning(f'We already used this TOTP, so we wait until it changes')
    #                 time.sleep(10)

    #             wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(totp.now() + Keys.ENTER)
    #             self.logger.info(f'TOTP entered')

    #         try:
    #             wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
    #             self.logger.info(f'App menu is ready!')
    #         except TimeoutException:
    #             self.logger.warning(f'Loading of app menu took too much time! Try TOTP again')
    #             wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(totp.now() + Keys.ENTER)
    #             self.logger.info(f'TOTP entered again, wait for the app menu')
    #             wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))

    #         driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #         dashboardUrl = drv.get_dashboard_url('su')
    #         currentUrl = driver.current_url
    #         try:
    #             self.assertEqual(dashboardUrl, currentUrl)
    #         except:
    #             self.assertEqual(dashboardUrl + '#/', currentUrl)
    #             self.logger.warning(f'Dashboard URL contains trailing #, likely due to the tasks app')
    #             self.logger.info(f'{currentUrl}')

    #         wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
    #         logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
    #         logoutLink.click()
    #         self.logger.info(f'Logout complete')
    #         currentUrl = driver.current_url
    #         self.logger.info(currentUrl)
    #         self.assertEqual(currentUrl, drv.get_gss_post_logout_url())
    #         driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #         driver.close()
    #         self.logger.info(f'And done...')

    # def test_portal_su_saml(self):
    #     self.logger.info(f'TestID: {self._testMethodName}')
    #     delay = 30 # seconds
    #     drv = sunetnextcloud.TestTarget()
    #     nodeName = 'su'
    #     if len(drv.allnodes) == 1:
    #         if drv.allnodes[0] != nodeName:
    #             self.logger.info(f'Only testing {drv.allnodes[0]}, not testing su saml')
    #             return
            
    #     if drv.target == 'prod':
    #         self.logger.info(f'SU has not switched to the portal in prod, we are not testing anything here')
    #         return

    #     for browser in drv.browsers:
    #         loginurl = drv.get_portal_login_url()
    #         self.logger.info(f'URL: {loginurl}')
    #         samluser=drv.get_samlusername(nodeName)
    #         self.logger.info(f'Username: {samluser}')
    #         samlpassword=drv.get_samluserpassword(nodeName)
            
    #         try:
    #             if browser == 'chrome':
    #                 options = Options()
    #                 options.add_argument("--no-sandbox")
    #                 options.add_argument("--disable-dev-shm-usage")
    #                 options.add_argument("--disable-gpu")
    #                 options.add_argument("--disable-extensions")
    #                 driver = webdriver.Chrome(options=options)
    #             elif browser == 'firefox':
    #                 if use_driver_service == False:
    #                     self.logger.info(f'Initialize Firefox driver without driver service')
    #                     options = FirefoxOptions()
    #                     options.add_argument("--headless")
    #                     driver = webdriver.Firefox(options=options)
    #                 else:
    #                     self.logger.info(f'Initialize Firefox driver using snap geckodriver and driver service')
    #                     driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
    #                     driver = webdriver.Firefox(service=driver_service, options=options)
    #             else:
    #                 self.logger.error(f'Unknown browser {browser}')
    #                 self.assertTrue(False)
    #         except Exception as e:
    #             self.logger.error(f'Error initializing driver for {browser}: {e}')
    #             self.assertTrue(False)

    #         self.deleteCookies(driver)
    #         driver.maximize_window()        
    #         driver.get(loginurl)

    #         wait = WebDriverWait(driver, delay)
    #         wait.until(EC.presence_of_element_located((By.ID, 'site')))
    #         input = driver.find_element(By.ID, 'site')
    #         input.send_keys(nodeName)
    #         input.send_keys(Keys.ENTER)
    #         input.send_keys(Keys.ESCAPE)

    #         nodeloginurl = drv.get_node_url(nodeName)
    #         self.logger.info(f'Locating button for {nodeloginurl}')
    #         loginbutton = driver.find_element(By.XPATH, '//a[@href="' + nodeloginurl +'/"]')
    #         loginbutton.click()

    #         wait = WebDriverWait(driver, delay)
    #         wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
    #         driver.implicitly_wait(g_driver_timeout)

    #         wait.until(EC.element_to_be_clickable((By.ID, 'searchinput'))).send_keys("su.se", Keys.RETURN)
    #         driver.implicitly_wait(g_driver_timeout)

    #         wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'label-url'))).click()
    #         driver.implicitly_wait(g_driver_timeout)

    #         wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(samluser)
    #         wait.until(EC.element_to_be_clickable((By.ID, 'password'))).send_keys(samlpassword + Keys.ENTER)

    #         # Wait for TOTP screen
    #         requireTotp = False
    #         try:
    #             self.logger.info(f'Check if TOTP selection dialogue is visible')
    #             wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="' + drv.indexsuffix + '/login/challenge/totp?redirect_url=' + drv.indexsuffix + '/apps/dashboard/' +'"]'))).click()
    #             self.logger.info(f'Found and clicked on TOTP selection dialogue')
    #             requireTotp = True
    #         except:
    #             self.logger.info(f'No need to select TOTP provider')
    #             requireTotp = False

    #         if requireTotp:
    #             nodetotpsecret = drv.get_samlusertotpsecret(nodeName)
    #             totp = pyotp.TOTP(nodetotpsecret)
    #             wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(totp.now() + Keys.ENTER)

    #         try:
    #             wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
    #             self.logger.info(f'App menu is ready!')
    #         except TimeoutException:
    #             self.logger.info(f'Loading of app menu took too much time!')

    #         driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #         dashboardUrl = drv.get_dashboard_url('su')
    #         currentUrl = driver.current_url
    #         self.logger.info(f'{currentUrl}')

    #         try:
    #             wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
    #             logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
    #             logoutLink.click()
    #             self.logger.info(f'Logout complete')
    #             currentUrl = driver.current_url
    #             self.logger.info(f'{currentUrl}')
    #             # self.assertEqual(driver.current_url, drv.get_gss_post_logout_url())
    #         except Exception as error:
    #             self.logger.warning(f'Could not logout due to: {error}')
    #             screenshot = pyautogui.screenshot()
    #             screenshot.save("screenshots/" + "test_portal_su_saml" + g_filename + ".png")
    #         driver.implicitly_wait(g_driver_timeout) # seconds before quitting
    #         driver.close()
    #         self.logger.info(f'And done...')

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
