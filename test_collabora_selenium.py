""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test Collabora on a local node
"""
import unittest
import xmlrunner
import HtmlTestRunner
import sunetnextcloud
import pyautogui
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import FirefoxOptions

from webdav3.client import Client

import logging
import time

g_drv = sunetnextcloud.TestTarget()
expectedResults = g_drv.expectedResults

g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_isLoggedIn=False
g_webdav_timeout = 30
g_collaboraRetryCount = 5
g_clickWait = 2
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
    g_loggedInNodes[collaboranode] = True

    g_driver.set_window_size(1920, 1152)
    # driver2 = webdriver.Firefox()
    g_driver.get(loginurl)

    g_wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
    g_wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)
    return

def removeFolder(node, foldername):
    fullPath = foldername + '/'
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
    client.verify = g_drv.verify
    # We check a few times if the file has been created
    exists = client.check(fullPath)
    if exists:
        g_logger.info(f'Folder {fullPath} was found, removing')
        client.clean(fullPath)
    else:
        g_logger.info(f'Folder {fullPath} not found')
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
    client.verify = g_drv.verify
    # We check a few times if the file has been created
    tryCount = 0
    while tryCount < 5:
        tryCount += 1
        g_logger.info(f'Folder contains {len(client.list(foldername))} elements')
        exists = client.check(fullPath)
        if exists:
            g_logger.info(f'File {fullPath} was found on try {tryCount}')
            return exists
        g_logger.info(f'File {fullPath} not found on try {tryCount} in {client.list()}')
        time.sleep(3)
    g_logger.info(f'File {fullPath} on {node} not found after {tryCount} tries: {exists}')
    return exists

def checkFolder(node, foldername, create=False):
    g_logger.info(f'Check if file {foldername} exists on {node}')
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
    client.verify = g_drv.verify
    if not create:
        return client.check(foldername)
    else:
        if not client.check(foldername):
            g_logger.info(f'Creating folder {foldername}')
            client.mkdir(foldername)
        return client.check(foldername)

def hasFiles(node, foldername):
    g_logger.info(f'Check if file {foldername} exists on {node}')
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
    client.verify = g_drv.verify
    return len(client.list(foldername))

class TestCollaboraSelenium(unittest.TestCase):
    global g_loggedInNodes, g_logger, g_drv, g_wait, g_driver
    g_drv = sunetnextcloud.TestTarget()

    logger = logging.getLogger(__name__)
    g_logger = logger
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
    
    testfolders = ['SeleniumCollaboraTest', 'selenium-system', 'selenium-personal']

    # Some class names of icons changed from Nextcloud 27 to 28
    version = expectedResults[g_drv.target]['status']['version']
    homeIcon = 'home-icon'
    addIcon = 'plus-icon'

    if len(g_drv.browsers) > 1:
        logger.warning(f'Please test only one browser by setting NextcloudTestBrowsers to the one you want to test: {g_drv.browsers}')
    
    logger.info(f'Testing browser: {g_drv.browsers[0]}')
    if g_drv.browsers[0] == 'chrome':
        try:
            options = ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            if not g_drv.verify:
                options.add_argument("--ignore-certificate-errors")
            driver = webdriver.Chrome(options=options)
            g_driver=driver
        except Exception as error:
            logger.error(f'Error initializing Chrome driver: {error}')
    elif g_drv.browsers[0] == 'firefox':
        try:
            options = FirefoxOptions()
            if not g_drv.verify:
                options.add_argument("--ignore-certificate-errors")
            driver = webdriver.Firefox(options=options)
            g_driver=driver
        except Exception as error:
            logger.error(f'Error initializing Firefox driver: {error}')
    else:
        logger.error(f'Unknown browser: {g_drv.browsers[0]}')

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    for collaboranode in g_drv.fullnodes:
        g_loggedInNodes[collaboranode] = False

    # text file
    def test_markup_text(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait

        for collaboranode in g_drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                removeFolder(collaboranode, 'Templates')
                if not g_loggedInNodes.get(collaboranode):
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info('App menu is ready!')
                except TimeoutException:
                    self.logger.warning('Loading of app menu took too much time!')
                    success = False

                if not success:
                    self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(g_drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                # TODO: Check URLs after login
                # dashboardUrl = g_drv.get_dashboard_url(collaboranode)
                # currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)

                try:
                    self.logger.info(f'Wait for {g_drv.indexsuffix}/apps/files/')
                    wait.until(EC.element_to_be_clickable((By.XPATH,'//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]'))).click()
                except Exception as error:
                    self.logger.warning(f'Wait for {g_drv.indexsuffix}/apps/files/ took too long: {error}')
                    success = False
                self.assertTrue(success)

                try:
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                    self.logger.info('All files visible!')
                except TimeoutException:
                    self.logger.warning('Loading of all files took too much time!')
                    success = False

                if not success:
                    self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(g_drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                self.driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(self.driver.current_url)
                self.logger.info(f'Looking for all files text in {self.version}')
                # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                self.logger.info('All files found!')

                self.logger.info('Looking for SeleniumCollaboraTest folder')
                folderExists = checkFolder(collaboranode, "SeleniumCollaboraTest", create=True)
                self.assertTrue(folderExists)

                folderurl = g_drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                fileCreated = False

                retryCount = 0
                while not fileCreated:
                    retryCount += 1
                    if retryCount >= g_collaboraRetryCount:
                        self.logger.error(f'File {g_filename}.md has not been created after {retryCount} tries, saving screenshot')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)
                        break

                    # Check if the folder is empty
                    if hasFiles(collaboranode, "SeleniumCollaboraTest") > 1:
                        isEmpty = False
                    else:
                        isEmpty = True
                    time.sleep(3)

                    # Sort file list so that new files are created at the beginning of the list
                    # if isEmpty == False:
                    #     try:
                    #         wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'files-list__column-sort-button'))).click()
                    #         self.logger.info(f'Changed sort order to descending')
                    #     except Exception as error:
                    #         self.logger.warning(f'Unable to change sort order to descending: {error}')
                    # time.sleep(3)

                    try:
                        self.logger.info('Click on add icon')
                        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, self.addIcon))).click()
                        self.logger.info('Click on new text file')
                        time.sleep(g_clickWait)
                        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-text'))).click()
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New text file']"))).click()
                        time.sleep(g_clickWait)
                        self.logger.info('Wait for dialog actions window')
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'dialog__actions')]")))
                        self.logger.info(f'Renaming the file we just created to {g_filename}.md')
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).send_keys(f'{g_filename}.md').perform()
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                    except Exception as error:
                        self.logger.warning(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)

                    # Verify the file has been created
                    fileCreated = checkFile(collaboranode, "SeleniumCollaboraTest", g_filename + '.md')
                    if not fileCreated:
                        self.logger.warning(f'File {g_filename}.md has not been created in try {retryCount}, refresh page and retry')
                        self.driver.refresh()
                        time.sleep(3)

                    # If it is the first entry in the list, we have to reload the page to get it to load
                    try:
                        if isEmpty:
                            self.logger.info('Reload page to open new document')
                            self.driver.refresh()
                    except Exception as e:
                        self.logger.error(f'Error: {e}')
                        
                self.logger.info('Sleep for 3 seconds...')
                time.sleep(3)

                self.logger.info('Can we type in the markup area?')
                ActionChains(self.driver).send_keys(f'Lorem Ipsum! {Keys.ENTER} {g_filename}').perform()
                time.sleep(3) # We give nextcloud a literal second to register the keystrokes before closing the document
                self.logger.info('Closing document...')
                try:
                    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'header-close'))).click()
                except Exception as error:
                    self.logger.warning(f"Closing markup document failed: {error}")

                self.logger.info('Manually open home folder in case closing of document fails')
                self.driver.get(g_drv.get_folder_url(collaboranode,''))

                self.logger.info('And done...')
                time.sleep(1)

    def test_collabora_document(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait
        
        for collaboranode in g_drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                removeFolder(collaboranode, 'Templates')
                if not g_loggedInNodes.get(collaboranode):
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info('App menu is ready!')
                except TimeoutException:
                    self.logger.warning('Loading of app menu took too much time!')
                    success = False

                if not success:
                    self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(g_drv.get_folder_url(collaboranode,''))
                    success = True
                self.assertTrue(success)

                # TODO: Check URLs after login
                # dashboardUrl = g_drv.get_dashboard_url(collaboranode)
                # currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                for testfolder in self.testfolders:
                    with self.subTest(myFolder=testfolder):
                        self.logger.info(f'TestID: {collaboranode} for folder {testfolder}')

                        try:
                            self.logger.info(f'Wait for {g_drv.indexsuffix}/apps/files/ and click')
                            wait.until(EC.element_to_be_clickable((By.XPATH,'//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]'))).click()
                            # self.logger.info(f'Get link for files app')
                            # files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]')
                            # self.logger.info(f'Click on files app')
                            # files.click()
                        except Exception as error:
                            self.logger.warning(f'Wait for {g_drv.indexsuffix}/apps/files/ took too long: {error}')
                            success = False

                        self.logger.info(f'Success: {success}')
                        self.assertTrue(success)

                        try:
                            wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                            self.logger.info('All files visible!')
                        except TimeoutException:
                            self.logger.warning('Loading of all files took too much time!')
                            success = False

                        if not success:
                            self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                            self.driver.get(g_drv.get_folder_url(collaboranode,''))
                            success = True

                        self.assertTrue(success)

                        self.driver.implicitly_wait(10) # seconds before quitting
                        self.logger.info(self.driver.current_url)
                        self.logger.info(f'Looking for all files text in {self.version}')
                        # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                        self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                        self.logger.info('All files found!')

                        self.logger.info(f'Looking for {testfolder} folder')
                        folderExists = checkFolder(collaboranode, testfolder, create=True)
                        self.assertTrue(folderExists)

                        folderurl = g_drv.get_folder_url(collaboranode, testfolder)
                        self.driver.get(folderurl)

                        fileCreated = False

                        retryCount = 0
                        while not fileCreated:
                            retryCount += 1
                            if retryCount >= g_collaboraRetryCount:
                                self.logger.error(f'File {g_filename} has not been created after {retryCount} tries, saving screenshot')
                                screenshot = pyautogui.screenshot()
                                screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                                self.assertTrue(False)
                                break

                            # Check if the folder is empty
                            if hasFiles(collaboranode, testfolder) > 1:
                                isEmpty = False
                            else:
                                isEmpty = True
                            time.sleep(3)
                        
                            try:
                                self.logger.info('Click on add icon')
                                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, self.addIcon))).click()
                                time.sleep(g_clickWait)
                                self.logger.info('Click on new document')
                                wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New document']"))).click()
                                time.sleep(g_clickWait)
                                self.logger.info('Wait for dialog actions window')
                                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'dialog__actions')]")))
                                self.logger.info(f'Renaming the file we just created to {g_filename}.odt')
                                time.sleep(g_clickWait)
                                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                                time.sleep(g_clickWait)
                                ActionChains(self.driver).send_keys(f'{g_filename}.odt').perform()
                                time.sleep(g_clickWait)
                                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                            except Exception as error:
                                self.logger.warning(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                                screenshot = pyautogui.screenshot()
                                screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                                self.assertTrue(False)

                            # Verify the file has been created
                            fileCreated = checkFile(collaboranode, testfolder, g_filename + '.odt')
                            if not fileCreated:
                                self.logger.warning(f'File {g_filename}.odt has not been created in try {retryCount}, refresh page and retry')
                                self.driver.refresh()
                                time.sleep(3)

                            # If it is the first entry in the list, we have to reload the page to get it to load
                            try:
                                if isEmpty:
                                    self.logger.info('Reload page to open new document')
                                    self.driver.refresh()
                            except Exception as e:
                                self.logger.error(f'Error: {e}')

                        self.logger.info('Sleep for 3 seconds...')
                        self.logger.info('Proceeding...')

                        try:
                            self.logger.info('Waiting for collabora frame')
                            wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[id^='collaboraframe']")))
                            self.logger.info('Collabora loaded. Wait for the save button...')
                            wait.until(EC.presence_of_element_located((By.ID, 'save-button')))
                            self.logger.info('Save button found. Let\'s type some text')
                            ActionChains(self.driver).send_keys(f'Lorem Ipsum! {Keys.ENTER} {g_filename}').perform()
                            time.sleep(3)
                        except Exception as error:
                            self.logger.error(f'Error writing to the document, saving screenshot: {error}')
                            screenshot = pyautogui.screenshot()
                            screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                            success = False

                        self.logger.info('Open the folder URL instead of closing the document')
                        self.driver.get(g_drv.get_folder_url(collaboranode,''))
                        self.assertTrue(success)

                self.logger.info('End of test!')
                self.assertTrue(g_loggedInNodes.get(collaboranode))

    # spreadsheet
    def test_collabora_spreadsheet(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait
        
        for collaboranode in g_drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                removeFolder(collaboranode, 'Templates')
                if not g_loggedInNodes.get(collaboranode):
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info('App menu is ready!')
                except TimeoutException:
                    self.logger.warning('Loading of app menu took too much time!')
                    success = False

                if not success:
                    self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(g_drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                # TODO: Check URLs after login
                # dashboardUrl = g_drv.get_dashboard_url(collaboranode)
                # currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                try:
                    self.logger.info(f'Wait for {g_drv.indexsuffix}/apps/files/')
                    wait.until(EC.element_to_be_clickable((By.XPATH,'//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]'))).click()
                    # files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]')
                    # files.click()
                except Exception as error:
                    self.logger.warning(f'Wait for {g_drv.indexsuffix}/apps/files/ took too long: {error}')
                    success = False
                self.assertTrue(success)

                try:
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                    self.logger.info('All files visible!')
                except TimeoutException:
                    self.logger.warning('Loading of all files took too much time!')
                    success = False

                if not success:
                    self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(g_drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                self.driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(self.driver.current_url)
                
                self.logger.info(f'Looking for all files text in {self.version}')
                # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                self.logger.info('All files found!')                

                self.logger.info('Looking for SeleniumCollaboraTest folder')
                folderExists = checkFolder(collaboranode, "SeleniumCollaboraTest", create=True)
                self.assertTrue(folderExists)

                folderurl = g_drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                fileCreated = False
                retryCount = 0
                while not fileCreated:
                    retryCount += 1
                    if retryCount >= g_collaboraRetryCount:
                        self.logger.error(f'File {g_filename} has not been created after {retryCount} tries, saving screenshot')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)
                        break

                    # Check if the folder is empty
                    if hasFiles(collaboranode, "SeleniumCollaboraTest") > 1:
                        isEmpty = False
                    else:
                        isEmpty = True

                    # try:
                    #     wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__table')))
                    #     isEmpty = False
                    #     self.logger.info(f'Folder is not empty, adding new content')
                    # except Exception as error:
                    #     self.logger.info(f'Folder seems empty, creating new files.')
                    #     isEmpty = True

                    # # Sort file list so that new files are created at the beginning of the list
                    # if isEmpty == False:
                    #     try:
                    #         wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'files-list__column-sort-button'))).click()
                    #         self.logger.info(f'Changed sort order to descending')
                    #     except Exception as error:
                    #         self.logger.warning(f'Unable to change sort order to descending: {error}')

                    time.sleep(3)
                    try:
                        self.logger.info('Click on add icon')
                        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, self.addIcon))).click()
                        self.logger.info('Click on new spreadsheet')
                        time.sleep(g_clickWait)
                        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-spreadsheet'))).click()
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New spreadsheet']"))).click()
                        time.sleep(g_clickWait)
                        self.logger.info('Wait for dialog actions window')
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'dialog__actions')]")))
                        self.logger.info(f'Renaming the file we just created to {g_filename}.ods')
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).send_keys(f'{g_filename}.ods').perform()
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                    except Exception as error:
                        self.logger.error(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)

                    # Verify the file has been created
                    fileCreated = checkFile(collaboranode, "SeleniumCollaboraTest", g_filename + '.ods')
                    if not fileCreated:
                        self.logger.warning(f'File {g_filename}.ods has not been created in try {retryCount}, refresh page and retry')
                        self.driver.refresh()
                        time.sleep(3)

                    # If it is the first entry in the list, we have to reload the page to get it to load
                    try:
                        if isEmpty:
                            self.logger.info('Reload page to open new document')
                            self.driver.refresh()
                    except Exception as e:
                        self.logger.error(f'Error: {e}')

                self.logger.info('Sleep for 3 seconds...')
                time.sleep(3)
                self.logger.info('Proceeding...')

                try:
                    self.logger.info('Waiting for collabora frame')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[id^='collaboraframe']")))
                    self.logger.info('Collabora loaded. Wait for the save button...')
                    wait.until(EC.presence_of_element_located((By.ID, 'save-button')))
                    self.logger.info('Save button found. Let\'s type some text')
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.UP).key_up(Keys.CONTROL).perform()
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.LEFT).key_up(Keys.CONTROL).perform()
                    ActionChains(self.driver).send_keys(f'{g_filename}{Keys.ENTER}{Keys.SPACE}1{Keys.ENTER}{Keys.SPACE}2{Keys.ENTER}{Keys.SPACE}3{Keys.ENTER}{Keys.SPACE}4{Keys.ENTER}{Keys.SPACE}').perform()
                    time.sleep(1)
                except Exception as error:
                    self.logger.error(f'Error writing to the document, saving screenshot: {error}')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                    success = False

                self.logger.info('Open the folder URL instead of closing the document')
                self.driver.get(g_drv.get_folder_url(collaboranode,''))
                self.assertTrue(success)

                self.logger.info('End of test!')
                
    # presentation
    def test_collabora_presentation(self):
        delay = 30 # seconds
        global g_isLoggedIn, g_loggedInNodes, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait
        
        for collaboranode in g_drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                self.logger.info(f'TestID: {collaboranode}')
                # if g_isLoggedIn == False:
                removeFolder(collaboranode, 'Templates')
                if not g_loggedInNodes.get(collaboranode):
                    nodelogin(collaboranode)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                self.logger.info('Waiting for app menu')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info('App menu is ready!')
                except TimeoutException:
                    self.logger.warning('Loading of app menu took too much time!')
                    success = False

                if not success:
                    self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(g_drv.get_folder_url(collaboranode,''))
                    success = True
                self.assertTrue(success)

                # TODO: Check URLs after login
                # dashboardUrl = g_drv.get_dashboard_url(collaboranode)
                # currentUrl = self.driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                try:
                    self.logger.info(f'Wait for {g_drv.indexsuffix}/apps/files/')
                    wait.until(EC.element_to_be_clickable((By.XPATH,'//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]'))).click()
                    # files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ g_drv.indexsuffix + '/apps/files/' +'"]')
                    # files.click()
                except Exception as error:
                    self.logger.warning(f'Wait for {g_drv.indexsuffix}/apps/files/ took too long: {error}')
                    success = False
                self.assertTrue(success)

                try:
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
                    self.logger.info('All files visible!')
                except Exception as error:
                    self.logger.warning(f'Loading of all files took too much time: {error}')
                    success = False

                if not success:
                    self.logger.warning('Manually open home folder in case loading of all files takes too much time')
                    self.driver.get(g_drv.get_folder_url(collaboranode,''))
                    success = True

                self.assertTrue(success)

                self.driver.implicitly_wait(10) # seconds before quitting
                self.logger.info(self.driver.current_url)
                self.logger.info(f'Looking for all files text in {self.version}')
                # //*[@id="app-content-vue"]/div[1]/div/nav/ul/li/a/span/span[2] "//h4/a[contains(text(),'SAP M')]"
                self.driver.find_element(By.XPATH, "//*[contains(text(), 'All files')]")
                self.logger.info('All files found!')                

                self.logger.info('Looking for SeleniumCollaboraTest folder')
                folderExists = checkFolder(collaboranode, "SeleniumCollaboraTest", create=True)
                self.assertTrue(folderExists)
                
                folderurl = g_drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                fileCreated = False

                retryCount = 0
                while not fileCreated:
                    retryCount += 1
                    if retryCount >= g_collaboraRetryCount:
                        self.logger.error(f'File {g_filename} has not been created after {retryCount} tries, saving screenshot')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)
                        break

                    # Check if the folder is empty
                    if hasFiles(collaboranode, "SeleniumCollaboraTest") > 1:
                        isEmpty = False
                    else:
                        isEmpty = True

                    # try:
                    #     wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'files-list__table')))
                    #     isEmpty = False
                    #     self.logger.info(f'Folder is not empty, adding new content')
                    # except Exception as error:
                    #     self.logger.info(f'Folder seems empty, creating new files.')
                    #     isEmpty = True

                    # # Sort file list so that new files are created at the beginning of the list
                    # if isEmpty == False:
                    #     try:
                    #         wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'files-list__column-sort-button'))).click()
                    #         self.logger.info(f'Changed sort order to descending')
                    #     except Exception as error:
                    #         self.logger.warning(f'Unable to change sort order to descending: {error}')

                    time.sleep(3)
                    try:
                        self.logger.info('Click on add icon')
                        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, self.addIcon))).click()
                        self.logger.info('Click on new presentation')
                        time.sleep(g_clickWait)
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'action-button__text') and text()='New presentation']"))).click()
                        time.sleep(g_clickWait)
                        self.logger.info('Wait for dialog actions window')
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'dialog__actions')]")))
                        self.logger.info(f'Renaming the file we just created to {g_filename}.odp')
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).send_keys(f'{g_filename}.odp').perform()
                        time.sleep(g_clickWait)
                        ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                    except Exception as error:
                        self.logger.error(f'Unable to create new file: {g_filename}, saving screenshot: {error}')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        self.assertTrue(False)

                    # Verify the file has been created
                    fileCreated = checkFile(collaboranode, "SeleniumCollaboraTest", g_filename + '.odp')
                    if not fileCreated:
                        self.logger.warning(f'File {g_filename}.odp has not been created in try {retryCount}, refresh page and retry')
                        self.driver.refresh()
                        time.sleep(3)

                    # If it is the first entry in the list, we have to reload the page to get it to load
                    try:
                        if isEmpty:
                            self.logger.info('Reload page to open new document')
                            self.driver.refresh()
                    except Exception as e:
                        self.logger.error(f'Error: {e}')

                self.logger.info('Sleep for 3 seconds...')
                time.sleep(3)
                self.logger.info('Proceeding...')

                try:
                    self.logger.info('Waiting for collabora frame')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[id^='collaboraframe']")))
                    self.logger.info('Collabora loaded. Wait for the save button...')
                    wait.until(EC.presence_of_element_located((By.ID, 'save-button')))
                    self.logger.info('Save button found. Let\'s type some text')
                    ActionChains(self.driver).send_keys(f'Lorem ipsum! {Keys.ENTER}{g_filename}').perform()
                    time.sleep(1)
                except Exception as error:
                    self.logger.error(f'Error writing to the document, saving screenshot: {error}')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                    success = False

                self.logger.info('Open the folder URL instead of closing the document')
                self.driver.get(g_drv.get_folder_url(collaboranode,''))
                self.assertTrue(success)

                self.logger.info('End of test!')

if __name__ == '__main__':
    if g_drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{g_drv.expectedResults[g_drv.target]['status']['version']}-collabora", add_timestamp=False))
