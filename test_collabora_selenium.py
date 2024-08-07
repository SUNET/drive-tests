""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test Collabora on a local node
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetnextcloud
import pyautogui

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from webdav3.client import Client

import logging
import os
import time
import yaml

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('NextcloudTestTarget')
g_expectedResultsFile = 'expected.yaml'
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_isLoggedIn=False
g_webdav_timeout = 30
g_collaboraRetryCount = 5
g_loggedInNodes={}
g_logger={}
g_driver={}
g_drv={}
g_wait={}

def deleteCookies():
    cookies = g_driver.get_cookies()
    g_logger.info(f'Deleting all cookies: {cookies}')
    g_driver.delete_all_cookies()
    cookies = g_driver.get_cookies()
    g_logger.info(f'Cookies deleted: {cookies}')

def nodelogin(collaboranode):
    global g_wait
    deleteCookies()
    g_logger.info(f'Logging in to {collaboranode}')
    loginurl = g_drv.get_node_login_url(collaboranode)
    g_logger.info(f'Login url: {loginurl}')
    nodeuser = g_drv.get_seleniumuser(collaboranode)
    nodepwd = g_drv.get_seleniumuserpassword(collaboranode)
    g_isLoggedIn = True
    g_loggedInNodes[collaboranode] = True

    g_driver.maximize_window()
    actions = ActionChains(g_driver)
    # driver2 = webdriver.Firefox()
    g_driver.get(loginurl)

    g_wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
    g_wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

    return

def checkFile(node, foldername, filename):
    fullPath = foldername + '/' + filename
    g_logger.info(f'Check if file {fullPath} exists on {node}')
    nodeuser = g_drv.get_seleniumuser(node)
    nodepwd = g_drv.get_seleniumuserpassword(node)
    url = g_drv.get_webdav_url(node, nodeuser)
    options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodepwd, 
        'webdav_timeout': g_webdav_timeout
    }
    client = Client(options)
    g_logger.info(f'Folder contains {len(client.list(foldername))} elements')
    exists = client.check(fullPath)
    g_logger.info(f'File {fullPath} exists on {node}: {exists}')
    return exists

class TestCollaboraSelenium(unittest.TestCase):
    global g_loggedInNodes, g_logger, g_drv, g_wait, g_driver
    drv = sunetnextcloud.TestTarget(g_testtarget)
    g_drv=drv
    logger = logging.getLogger(__name__)
    g_logger = logger
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
    
    with open(g_expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    testfolders = ['SeleniumCollaboraTest', 'selenium-system', 'selenium-personal']

    # Some class names of icons changed from Nextcloud 27 to 28
    version = expectedResults[drv.target]['status']['version']
    if version.startswith('27'):
        homeIcon = 'icon-home'
        addIcon = 'icon-add'
    else:
        homeIcon = 'home-icon'
        addIcon = 'plus-icon'

    try:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        driver = webdriver.Chrome(options=options)
        g_driver=driver
    except Exception as error:
        logger.error(f'Error initializing Chrome driver: {error}')

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    for collaboranode in drv.fullnodes:
        g_loggedInNodes[collaboranode] = False

    # text file
    def test_markup_text(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait

        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info(f'App menu is ready!')
                except TimeoutException:
                    self.logger.warning(f'Loading of app menu took too much time!')
                    success = False

                if success == False:
                    self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                # Check URLs after login
                dashboardUrl = self.drv.get_dashboard_url(collaboranode)
                currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)

                try:
                    self.logger.info(f'Wait for {self.drv.indexsuffix}/apps/files/')
                    wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')))
                    files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')
                    files.click()
                except Exception as error:
                    self.logger.warning(f'Wait for {self.drv.indexsuffix}/apps/files/ took too long: {error}')
                    success = False
                self.assertTrue(success)

                try:
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                    self.logger.info(f'All files visible!')
                except TimeoutException:
                    self.logger.warning(f'Loading of all files took too much time!')
                    success = False

                if success == False:
                    self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                self.driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(self.driver.current_url)
                if self.version.startswith('27'):
                    self.logger.info(f'Looking for home icon in {self.version}')
                    try:
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.homeIcon)))
                    except Exception as error:
                        self.logger.error(f'Home icon in files app not found: {error}')

                else:
                    self.logger.info(f'Looking for all files text in {self.version}')
                    # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                    self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                    self.logger.info(f'All files found!')

                self.logger.info(f'Looking for SeleniumCollaboraTest folder')

                try:
                    if self.version.startswith('27'):
                        self.driver.find_element(By.XPATH, "//*[contains(@class, 'innernametext') and text()='SeleniumCollaboraTest']")
                        self.logger.info(f'SeleniumCollaboraTest folder found')
                    else:
                        self.driver.find_element(By.XPATH, "//*[contains(text(), 'SeleniumCollaboraTest')]")
                        self.logger.info(f'SeleniumCollaboraTest folder found')
                except Exception as error:
                    self.logger.info(f'SeleniumCollaboraTest folder not found, creating; {error}')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                    time.sleep(1)

                    if self.version.startswith('27'):
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys('SeleniumCollaboraTest' + Keys.ENTER)
                    else:
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New folder']"))).click()
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id^=\'input\']')))
                        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                        ActionChains(self.driver).send_keys(f'SeleniumCollaboraTest{Keys.ENTER}').perform()
                    time.sleep(1)
                folderurl = self.drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                fileCreated = False

                retryCount = 0
                while fileCreated == False:
                    retryCount += 1
                    if retryCount >= g_collaboraRetryCount:
                        self.logger.error(f'File {g_filename}.md has not been created after {retryCount}')
                        self.assertTrue(False)
                        break

                    # Check if the folder is empty
                    try:
                        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Upload some content or sync with your devices!']")))
                        if self.version.startswith('27'):
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-filestable')))
                        else:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__table')))
                        isEmpty = False
                        self.logger.info(f'Folder is not empty, adding new content')
                    except Exception as error:
                        self.logger.info(f'Folder is empty, creating new files; {error}')
                        isEmpty = True

                    # Sort file list so that new files are created at the beginning of the list
                    if isEmpty == False:
                        try:
                            if self.version.startswith('27'):
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click()
                            else:
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__column-sort-button'))).click()
                            self.logger.info(f'Changed sort order to descending')
                        except Exception as error:
                            self.logger.warning(f'Unable to change sort order to descending: {error}')

                    time.sleep(3)
                    try:
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-text'))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New text file')]"))).click()
                        if self.version.startswith('27'):
                            # Write the filename in the menu
                            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)
                        else:
                            # Starting with Nextcloud 28, we have to rename the file
                            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New document')]")))
                            self.logger.info(f'Renaming the file we just created to {g_filename}.md')
                            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                            time.sleep(0.5)
                            ActionChains(self.driver).send_keys(f'{g_filename}.md').perform()
                            time.sleep(0.5)
                            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                            pass
                    except Exception as error:
                        self.logger.warning(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)

                    # Verify the file has been created
                    fileCreated = checkFile(collaboranode, "SeleniumCollaboraTest", g_filename + '.md')
                    if fileCreated == False:
                        self.logger.warning(f'File {g_filename}.md has not been created in try {retryCount}, refresh page and retry')
                        self.driver.refresh()
                        time.sleep(3)

                self.logger.info(f'Sleep for 3 seconds...')
                time.sleep(3)

                self.logger.info(f'Can we type in the markup area?')
                ActionChains(self.driver).send_keys(f'Lorem Ipsum! {Keys.ENTER} {g_filename}').perform()
                time.sleep(3) # We give nextcloud a literal second to register the keystrokes before closing the document
                self.logger.info(f'Closing document...')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'header-close'))).click()
                except Exception as error:
                    self.logger.warning(f"Closing markup document failed: {error}")

                self.logger.info(f'Manually open home folder in case closing of document fails')
                self.driver.get(self.drv.get_folder_url(collaboranode,''))

                self.logger.info(f'And done...')
                time.sleep(1)

    def test_collabora_document(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait
        
        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info(f'App menu is ready!')
                except TimeoutException:
                    self.logger.warning(f'Loading of app menu took too much time!')
                    success = False

                if success == False:
                    self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))
                    success = True
                self.assertTrue(success)

                # Check URLs after login
                dashboardUrl = self.drv.get_dashboard_url(collaboranode)
                currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                for testfolder in self.testfolders:
                    with self.subTest(myFolder=testfolder):
                        self.logger.info(f'TestID: {collaboranode} for folder {testfolder}')

                        try:
                            self.logger.info(f'Wait for {self.drv.indexsuffix}/apps/files/')
                            wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')))
                            self.logger.info(f'Get link for files app')
                            files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')
                            self.logger.info(f'Click on files app')
                            files.click()
                        except Exception as error:
                            self.logger.warning(f'Wait for {self.drv.indexsuffix}/apps/files/ took too long: {error}')
                            success = False

                        self.logger.info(f'Success: {success}')
                        self.assertTrue(success)

                        try:
                            wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                            self.logger.info(f'All files visible!')
                        except TimeoutException:
                            self.logger.warning(f'Loading of all files took too much time!')
                            success = False

                        if success == False:
                            self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                            self.driver.get(self.drv.get_folder_url(collaboranode,''))
                            success = True

                        self.assertTrue(success)

                        self.driver.implicitly_wait(10) # seconds before quitting
                        self.logger.info(self.driver.current_url)
                        
                        if self.version.startswith('27'):
                            self.logger.info(f'Looking for home icon in {self.version}')
                            try:
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.homeIcon)))
                            except Exception as error:
                                self.logger.error(f'Home icon in files app not found: {error}')
                        else:
                            self.logger.info(f'Looking for all files text in {self.version}')
                            # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                            self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                            self.logger.info(f'All files found!')

                        self.logger.info(f'Looking for {testfolder} folder')
                        
                        try:
                            if self.version.startswith('27'):
                                wait.until(EC.presence_of_element_located((By.XPATH, f'//*[contains(@class, \'innernametext\') and text()=\'{testfolder}\']')))
                                self.logger.info(f'{testfolder} folder found')
                            else:
                                self.driver.find_element(By.XPATH, f"//*[contains(text(), '{testfolder}')]")
                                self.logger.info(f'{testfolder} folder found')
                        except Exception as error:
                            self.logger.info(f'{testfolder} folder not found, creating; Exception was: {error}')
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                            time.sleep(1)

                            if self.version.startswith('27'):
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys(testfolder + Keys.ENTER)
                            else:
                                self.logger.info(f'Creating {testfolder} on {self.version}')
                                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New folder']"))).click()
                                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id^=\'input\']')))
                                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                                ActionChains(self.driver).send_keys(f'SeleniumCollaboraTest{Keys.ENTER}').perform()
                            time.sleep(1)

                        folderurl = self.drv.get_folder_url(collaboranode, testfolder)
                        self.driver.get(folderurl)

                        fileCreated = False

                        retryCount = 0
                        while fileCreated == False:
                            retryCount += 1
                            if retryCount >= g_collaboraRetryCount:
                                self.logger.error(f'File {g_filename} has not been created after {retryCount}')
                                self.assertTrue(False)
                                break

                            # Check if the folder is empty
                            try:
                                # wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Upload some content or sync with your devices!']")))
                                if self.version.startswith('27'):
                                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-filestable')))
                                else:
                                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__table')))
                                isEmpty = False
                                self.logger.info(f'Folder is not empty, adding new content')
                            except Exception as error:
                                self.logger.info(f'Folder is empty, creating new files; Exception was: {error}')
                                isEmpty = True

                            # Sort file list so that new files are created at the beginning of the list
                            if isEmpty == False:
                                try:
                                    if self.version.startswith('27'):
                                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click()
                                    else:
                                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__column-sort-button'))).click()
                                    self.logger.info(f'Changed sort order to descending')
                                except Exception as error:
                                    self.logger.warning(f'Unable to change sort order to descending; Exception was {error}')

                            time.sleep(3)
                        
                            try:
                                self.logger.info(f'Click on add icon')
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                                self.logger.info(f'Click on add document')
                                # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-document'))).click()
                                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New document')]"))).click()

                                if self.version.startswith('27'):
                                    # Write the filename in the menu
                                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)
                                else:
                                    # Starting with Nextcloud 28, we have to rename the file
                                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New document')]")))
                                    self.logger.info(f'Renaming the file we just created to {g_filename}.odt')
                                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                                    time.sleep(0.5)
                                    ActionChains(self.driver).send_keys(f'{g_filename}.odt').perform()
                                    time.sleep(0.5)
                                    ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                                    pass
                            except Exception as error:
                                self.logger.warning(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                                screenshot = pyautogui.screenshot()
                                screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                                self.assertTrue(False)

                            # Verify the file has been created
                            fileCreated = checkFile(collaboranode, testfolder, g_filename + '.odt')
                            if fileCreated == False:
                                self.logger.warning(f'File {g_filename}.odt has not been created in try {retryCount}, refresh page and retry')
                                self.driver.refresh()
                                time.sleep(3)

                        self.logger.info(f'Sleep for 3 seconds...')
                        time.sleep(3)
                        self.logger.info(f'Proceeding...')

                        try:
                            self.logger.info(f'Waiting for collabora frame')
                            wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[id^='collaboraframe']")))
                            self.logger.info(f'Collabora loaded... Let\'s type some text')
                            time.sleep(3)
                            ActionChains(self.driver).send_keys(f'Lorem Ipsum! {Keys.ENTER} {g_filename}').perform()
                            time.sleep(3)
                        except Exception as error:
                            self.logger.error(f'Error writing to the document: {error}')
                            success = False

                        self.logger.info(f'Open the folder URL instead of closing the document')
                        self.driver.get(self.drv.get_folder_url(collaboranode,''))
                        self.assertTrue(success)

                self.logger.info('End of test!')
                self.assertTrue(g_loggedInNodes.get(collaboranode))

    # spreadsheet
    def test_collabora_spreadsheet(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait
        
        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info(f'App menu is ready!')
                except TimeoutException:
                    self.logger.warning(f'Loading of app menu took too much time!')
                    success = False

                if success == False:
                    self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                # Check URLs after login
                dashboardUrl = self.drv.get_dashboard_url(collaboranode)
                currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                try:
                    self.logger.info(f'Wait for {self.drv.indexsuffix}/apps/files/')
                    wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')))
                    files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')
                    files.click()
                except Exception as error:
                    self.logger.warning(f'Wait for {self.drv.indexsuffix}/apps/files/ took too long: {error}')
                    success = False
                self.assertTrue(success)

                try:
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                    self.logger.info(f'All files visible!')
                except TimeoutException:
                    self.logger.warning(f'Loading of all files took too much time!')
                    success = False

                if success == False:
                    self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                self.driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(self.driver.current_url)
                
                if self.version.startswith('27'):
                    self.logger.info(f'Looking for home icon in {self.version}')
                    try:
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.homeIcon)))
                    except Exception as error:
                        self.logger.error(f'Home icon in files app not found: {error}')

                else:
                    self.logger.info(f'Looking for all files text in {self.version}')
                    # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                    self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                    self.logger.info(f'All files found!')                

                self.logger.info(f'Looking for SeleniumCollaboraTest folder')
                
                try:
                    if self.version.startswith('27'):
                        self.driver.find_element(By.XPATH, "//*[contains(@class, 'innernametext') and text()='SeleniumCollaboraTest']")
                        self.logger.info(f'SeleniumCollaboraTest folder found')
                    else:
                        self.driver.find_element(By.XPATH, "//*[contains(text(), 'SeleniumCollaboraTest')]")
                        self.logger.info(f'SeleniumCollaboraTest folder found')
                except Exception as error:
                    self.logger.info(f'SeleniumCollaboraTest folder not found, creating; {error}')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                    time.sleep(1)

                    if self.version.startswith('27'):
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys('SeleniumCollaboraTest' + Keys.ENTER)
                    else:
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New folder']"))).click()
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id^=\'input\']')))
                        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                        ActionChains(self.driver).send_keys(f'SeleniumCollaboraTest{Keys.ENTER}').perform()
                    time.sleep(1)
                folderurl = self.drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                fileCreated = False
                retryCount = 0
                while fileCreated == False:
                    retryCount += 1
                    if retryCount >= g_collaboraRetryCount:
                        self.logger.error(f'File {g_filename} has not been created after {retryCount}')
                        self.assertTrue(False)
                        break

                    # Check if the folder is empty
                    try:
                        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Upload some content or sync with your devices!']")))
                        if self.version.startswith('27'):
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-filestable')))
                        else:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__table')))
                        isEmpty = False
                        self.logger.info(f'Folder is not empty, adding new content')
                    except Exception as error:
                        self.logger.info(f'Folder is empty, creating new files: {error}')
                        isEmpty = True

                    # Sort file list so that new files are created at the beginning of the list
                    if isEmpty == False:
                        try:
                            if self.version.startswith('27'):
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click()
                            else:
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__column-sort-button'))).click()
                            self.logger.info(f'Changed sort order to descending')
                        except Exception as error:
                            self.logger.warning(f'Unable to change sort order to descending: {error}')

                    time.sleep(3)
                    try:
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-spreadsheet'))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New spreadsheet')]"))).click()
                        if self.version.startswith('27'):
                            # Write the filename in the menu
                            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)
                        else:
                            # Starting with Nextcloud 28, we have to rename the file
                            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New document')]")))
                            self.logger.info(f'Renaming the file we just created to {g_filename}.ods')
                            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                            time.sleep(0.5)
                            ActionChains(self.driver).send_keys(f'{g_filename}.ods').perform()
                            time.sleep(0.5)
                            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                            pass
                    except Exception as error:
                        self.logger.error(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)

                    # Verify the file has been created
                    fileCreated = checkFile(collaboranode, "SeleniumCollaboraTest", g_filename + '.ods')
                    if fileCreated == False:
                        self.logger.warning(f'File {g_filename}.ods has not been created in try {retryCount}, refresh page and retry')
                        self.driver.refresh()
                        time.sleep(3)

                self.logger.info(f'Sleep for 3 seconds...')
                time.sleep(3)
                self.logger.info(f'Proceeding...')

                try:
                    self.logger.info(f'Waiting for collabora frame')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[id^='collaboraframe']")))
                    self.logger.info(f'Collabora loaded... Let\'s type some text')
                    time.sleep(1)
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.UP).key_up(Keys.CONTROL).perform()
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.LEFT).key_up(Keys.CONTROL).perform()
                    ActionChains(self.driver).send_keys(f'{g_filename}{Keys.ENTER}{Keys.SPACE}1{Keys.ENTER}{Keys.SPACE}2{Keys.ENTER}{Keys.SPACE}3{Keys.ENTER}{Keys.SPACE}4{Keys.ENTER}{Keys.SPACE}').perform()
                    time.sleep(1)
                except Exception as error:
                    self.logger.error(f'Error writing to the document: {error}')
                    success = False

                self.logger.info(f'Open the folder URL instead of closing the document')
                self.driver.get(self.drv.get_folder_url(collaboranode,''))
                self.assertTrue(success)

                self.logger.info('End of test!')
                
    # presentation
    def test_collabora_presentation(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait
        
        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info(f'App menu is ready!')
                except TimeoutException:
                    self.logger.warning(f'Loading of app menu took too much time!')
                    success = False

                if success == False:
                    self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))
                    success = True
                self.assertTrue(success)

                # Check URLs after login
                dashboardUrl = self.drv.get_dashboard_url(collaboranode)
                currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                try:
                    self.logger.info(f'Wait for {self.drv.indexsuffix}/apps/files/')
                    wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')))
                    files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ self.drv.indexsuffix + '/apps/files/' +'"]')
                    files.click()
                except Exception as error:
                    self.logger.warning(f'Wait for {self.drv.indexsuffix}/apps/files/ took too long: {error}')
                    success = False
                self.assertTrue(success)

                try:
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                    self.logger.info(f'All files visible!')
                except Exception as error:
                    self.logger.warning(f'Loading of all files took too much time: {error}')
                    success = False

                if success == False:
                    self.logger.warning(f'Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                self.driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(self.driver.current_url)
                
                if self.version.startswith('27'):
                    self.logger.info(f'Looking for home icon in {self.version}')
                    try:
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.homeIcon)))
                    except Exception as error:
                        self.logger.error(f'Home icon in files app not found: {error}')
                else:
                    self.logger.info(f'Looking for all files text in {self.version}')
                    # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                    self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                    self.logger.info(f'All files found!')                

                self.logger.info(f'Looking for SeleniumCollaboraTest folder')
                
                try:
                    if self.version.startswith('27'):
                        self.driver.find_element(By.XPATH, "//*[contains(@class, 'innernametext') and text()='SeleniumCollaboraTest']")
                        self.logger.info(f'SeleniumCollaboraTest folder found')
                    else:
                        self.driver.find_element(By.XPATH, "//*[contains(text(), 'SeleniumCollaboraTest')]")
                        self.logger.info(f'SeleniumCollaboraTest folder found')
                except Exception as error:
                    self.logger.info(f'SeleniumCollaboraTest folder not found, creating; {error}')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                    time.sleep(1)

                    if self.version.startswith('27'):
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys('SeleniumCollaboraTest' + Keys.ENTER)
                    else:
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New folder']"))).click()
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id^=\'input\']')))
                        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                        ActionChains(self.driver).send_keys(f'SeleniumCollaboraTest{Keys.ENTER}').perform()
                    time.sleep(1)
                folderurl = self.drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                fileCreated = False

                retryCount = 0
                while fileCreated == False:
                    retryCount += 1
                    if retryCount >= g_collaboraRetryCount:
                        self.logger.error(f'File {g_filename} has not been created after {retryCount}')
                        self.assertTrue(False)
                        break

                    # Check if the folder is empty
                    try:
                        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Upload some content or sync with your devices!']")))
                        if self.version.startswith('27'):
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-filestable')))
                        else:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__table')))
                        isEmpty = False
                        self.logger.info(f'Folder is not empty, adding new content')
                    except Exception as error:
                        self.logger.info(f'Folder is empty, creating new files: {error}')
                        isEmpty = True

                    # Sort file list so that new files are created at the beginning of the list
                    if isEmpty == False:
                        try:
                            if self.version.startswith('27'):
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click()
                            else:
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__column-sort-button'))).click()
                            self.logger.info(f'Changed sort order to descending')
                        except Exception as error:
                            self.logger.warning(f'Unable to change sort order to descending: {error}')

                    time.sleep(3)
                    try:
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, self.addIcon))).click()
                        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-presentation'))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New presentation')]"))).click()
                        if self.version.startswith('27'):
                            # Write the filename in the menu
                            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)
                        else:
                            # Starting with Nextcloud 28, we have to rename the file
                            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'New document')]")))
                            self.logger.info(f'Renaming the file we just created to {g_filename}.odp')
                            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                            time.sleep(0.5)
                            ActionChains(self.driver).send_keys(f'{g_filename}.odp').perform()
                            time.sleep(0.5)
                            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                            pass
                    except Exception as error:
                        self.logger.error(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)

                    # Verify the file has been created
                    fileCreated = checkFile(collaboranode, "SeleniumCollaboraTest", g_filename + '.odp')
                    if fileCreated == False:
                        self.logger.warning(f'File {g_filename}.odp has not been created in try {retryCount}, refresh page and retry')
                        self.driver.refresh()
                        time.sleep(3)

                self.logger.info(f'Sleep for 3 seconds...')
                time.sleep(3)
                self.logger.info(f'Proceeding...')

                try:
                    self.logger.info(f'Waiting for collabora frame')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[id^='collaboraframe']")))
                    self.logger.info(f'Collabora loaded... Let\'s type some text')
                    time.sleep(3)
                    ActionChains(self.driver).send_keys(f'Lorem ipsum! {Keys.ENTER}{g_filename}').perform()
                    time.sleep(1)
                except Exception as error:
                    self.logger.error(f'Error writing to the document: {error}')
                    success = False

                self.logger.info(f'Open the folder URL instead of closing the document')
                self.driver.get(self.drv.get_folder_url(collaboranode,''))
                self.assertTrue(success)

                self.logger.info('End of test!')

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
