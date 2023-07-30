""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test Collabora on a local node
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetdrive
import pyautogui

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import logging
import os
import time

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('DriveTestTarget')
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_isLoggedIn=False
g_loggedInNodes={}

class TestCollaboraSelenium(unittest.TestCase):
    global g_loggedInNodes
    drv = sunetdrive.TestTarget(g_testtarget)
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    testfolders = ['SeleniumCollaboraTest', 'selenium-system', 'selenium-personal']

    try:
        options = Options()
        # options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
    except:
        self.logger.error(f'Error initializing Chrome driver')
        self.assertTrue(False)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    for collaboranode in drv.fullnodes:
        g_loggedInNodes[collaboranode] = False

    # text file
    def test_markup_text(self):
        delay = 30 # seconds
        global g_isLoggedIn
        global g_loggedInNodes
        wait = WebDriverWait(self.driver, delay)

        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    self.logger.info(f'Logging in to {collaboranode}')
                    loginurl = self.drv.get_node_login_url(collaboranode)
                    self.logger.info(f'Login url: {loginurl}')
                    nodeuser = self.drv.get_seleniumuser(collaboranode)
                    nodepwd = self.drv.get_seleniumuserpassword(collaboranode)
                    g_isLoggedIn = True
                    g_loggedInNodes[collaboranode] = True
                
                    self.driver.maximize_window()
                    actions = ActionChains(self.driver)
                    # driver2 = webdriver.Firefox()
                    self.driver.get(loginurl)

                    wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                    wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                print('Waiting for app menu')
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
                    self.logger.info(f'Wait for /index.php/apps/files/')
                    wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ '/index.php/apps/files/' +'"]')))
                    files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/files/' +'"]')
                    files.click()
                except:
                    self.logger.warning(f'Wait for /index.php/apps/files/ took too long')
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
                print(self.driver.current_url)
                
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-home')))
                
                try:
                    self.driver.find_element(By.XPATH, "//*[contains(@class, 'innernametext') and text()='SeleniumCollaboraTest']")
                    self.logger.info(f'SeleniumCollaboraTest folder found')
                except:
                    self.logger.info(f'SeleniumCollaboraTest folder not found, creating')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys('SeleniumCollaboraTest' + Keys.ENTER)

                folderurl = self.drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                # Sort file list so that new files are created at the beginning of the list
                try:
                    self.logger.info(f'Wait for folder to be sortable')
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'SeleniumCollaboraTest')))
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator')))
                except:
                    self.logger.error(f'Unable to sort, saving screenshot of latest result...')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + collaboranode + "_test_markup_text_" + g_filename + ".png")
                    self.assertTrue(False)

                if (EC.presence_of_element_located((By.CLASS_NAME, 'icon-triangle-n'))):
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click
                    self.logger.info(f'Change sorting to descending!')

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-text'))).click()
                
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)

                self.logger.info(f'Sleep for 3 seconds...')
                time.sleep(3)
                self.logger.info(f'Can we type in the markup area?')
                ActionChains(self.driver).send_keys(f'Lorem Ipsum! {Keys.ENTER} {g_filename}').perform()
                time.sleep(3) # We give nextcloud a literal second to register the keystrokes before closing the document
                self.logger.info(f'Closing document...')
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'header-close'))).click()
                except:
                    self.logger.warning("Closing markup document failed")

                self.logger.info(f'Manually open home folder in case closing of document fails')
                self.driver.get(self.drv.get_folder_url(collaboranode,''))

                self.logger.info(f'And done...')
                time.sleep(1)

    def test_collabora_document(self):
        delay = 30 # seconds
        global g_isLoggedIn
        global g_loggedInNodes
        wait = WebDriverWait(self.driver, delay)
        
        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    self.logger.info(f'Logging in to {collaboranode}')
                    loginurl = self.drv.get_node_login_url(collaboranode)
                    self.logger.info(f'Login url: {loginurl}')
                    nodeuser = self.drv.get_seleniumuser(collaboranode)
                    nodepwd = self.drv.get_seleniumuserpassword(collaboranode)
                    g_isLoggedIn = True
                    g_loggedInNodes[collaboranode] = True
                    
                    self.driver.maximize_window()
                    actions = ActionChains(self.driver)
                    # driver2 = webdriver.Firefox()
                    self.driver.get(loginurl)

                    wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                    wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                print('Waiting for app menu')
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
                    self.logger.info(f'Testing folder {testfolder}')

                    try:
                        self.logger.info(f'Wait for /index.php/apps/files/')
                        wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ '/index.php/apps/files/' +'"]')))
                        files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/files/' +'"]')
                        files.click()
                    except:
                        self.logger.warning(f'Wait for /index.php/apps/files/ took too long')
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
                    print(self.driver.current_url)
                    
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-home')))
                    
                    try:
                        wait.until(EC.presence_of_element_located((By.XPATH, f'//*[contains(@class, \'innernametext\') and text()=\'{testfolder}\']')))
                        self.logger.info(f'{testfolder} folder found')
                    except:
                        self.logger.info(f'{testfolder} folder not found, creating')

                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys(testfolder + Keys.ENTER)

                    folderurl = self.drv.get_folder_url(collaboranode, testfolder)
                    self.driver.get(folderurl)

                    # Sort file list so that new files are created at the beginning of the list
                    try:
                        self.logger.info(f'Wait for folder to be sortable')
                        wait.until(EC.presence_of_element_located((By.LINK_TEXT, testfolder)))
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator')))
                    except:
                        self.logger.error(f'Unable to sort, saving screenshot of latest result...')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + "_test_collabora_document_" + g_filename + ".png")
                        self.assertTrue(False)

                    if (EC.presence_of_element_located((By.CLASS_NAME, 'icon-triangle-n'))):
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click
                        self.logger.info(f'Change sorting to descending!')

                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-document'))).click()
                    
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)

                    self.logger.info(f'Sleep for 3 seconds...')
                    time.sleep(3)
                    self.logger.info(f'Proceeding...')

                    try:
                        self.logger.info(f'Waiting for collabora frame')
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "collaboraframe")))
                        self.logger.info(f'Collabora loaded... Wait for loleafletframe')
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "loleafletframe")))
                        self.logger.info(f'loleafletframe loaded')

                        skipwelcomeframe = False
                        try:
                            self.driver.find_element(by=By.CLASS_NAME, value='iframe-welcome-modal')
                            skipwelcomeframe = False
                        except NoSuchElementException:
                            self.logger.info(f'Quick test iframe-welcome-modal, skipping further checks')
                            skipwelcomeframe = True

                        if skipwelcomeframe == False:                        
                            try:
                                self.logger.info(f'Looking for welcome frame')
                                wait.until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, "iframe-welcome-modal")))
                                self.logger.info(f'Switched to iframe-welcome-modal')
                            except:
                                self.logger.info(f'No welcome frame found, skipping any further checks')
                                skipwelcomeframe = True

                        if skipwelcomeframe == False:                        
                            self.logger.info(f'Welcome screen found, trying to close it...')

                            wait.until(EC.presence_of_element_located((By.ID, 'slide-3-indicator'))).click()
                            time.sleep(2)
                            self.logger.info(f'Looking for slide-3-button...')
                            button = self.driver.find_element(By.ID, 'slide-3-button')
                            self.logger.info(f'Button found...')
                            button.click()
                            self.logger.info(f'Slide 3 button clicked...')
                            skipwelcomeframe = True
                        time.sleep(2)
                    except:
                        self.logger.info('Proceed...')

                    try:
                        blockSuccess = False
                        self.driver.switch_to.default_content()
                        self.logger.info(f'Switched to default content...')
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "collaboraframe")))
                        self.logger.info(f'Collabora loaded... Wait for loleafletframe')
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "loleafletframe")))
                        self.logger.info(f'loleafletframe loaded...')
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'leaflet-layer'))).click()
                        self.logger.info(f'Can we type in the leaflet layer?')
                        ActionChains(self.driver).send_keys(f'Lorem Ipsum! {Keys.ENTER} {g_filename}').perform()
                        time.sleep(1) # We give collabora a literal second to register the keystrokes before closing the document
                        self.logger.info(f'Closing document...')
                        blockSuccess = True
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'closebuttonimage'))).click()
                        self.logger.info(f'And done...')
                        time.sleep(3)
                    except:
                        self.logger.error(f'Content not found, saving screenshot of latest result...')
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                        if (blockSuccess == False):
                            success = False

                    self.logger.info(f'Manually open home folder in case closing of document fails')
                    self.driver.get(self.drv.get_folder_url(collaboranode,''))

                    self.assertTrue(success)

                self.logger.info('End of test!')
                self.assertTrue(g_loggedInNodes.get(collaboranode))

    # spreadsheet
    def test_collabora_spreadsheet(self):
        delay = 30 # seconds
        global g_isLoggedIn
        global g_loggedInNodes
        wait = WebDriverWait(self.driver, delay)
        
        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    self.logger.info(f'Logging in to {collaboranode}')
                    loginurl = self.drv.get_node_login_url(collaboranode)
                    self.logger.info(f'Login url: {loginurl}')
                    nodeuser = self.drv.get_seleniumuser(collaboranode)
                    nodepwd = self.drv.get_seleniumuserpassword(collaboranode)
                    g_isLoggedIn = True
                    g_loggedInNodes[collaboranode] = True
                
                    self.driver.maximize_window()
                    actions = ActionChains(self.driver)
                    # driver2 = webdriver.Firefox()
                    self.driver.get(loginurl)

                    wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                    wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                print('Waiting for app menu')
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
                    self.logger.info(f'Wait for /index.php/apps/files/')
                    wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ '/index.php/apps/files/' +'"]')))
                    files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/files/' +'"]')
                    files.click()
                except:
                    self.logger.warning(f'Wait for /index.php/apps/files/ took too long')
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
                print(self.driver.current_url)
                
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-home')))
                
                self.logger.info(f'Looking for SeleniumCollaboraTest folder')
                
                try:
                    self.driver.find_element(By.XPATH, "//*[contains(@class, 'innernametext') and text()='SeleniumCollaboraTest']")
                    self.logger.info(f'SeleniumCollaboraTest folder found')
                except:
                    self.logger.info(f'SeleniumCollaboraTest folder not found, creating')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys('SeleniumCollaboraTest' + Keys.ENTER)

                folderurl = self.drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                # Sort file list so that new files are created at the beginning of the list
                try:
                    self.logger.info(f'Wait for folder to be sortable')
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'SeleniumCollaboraTest')))
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator')))
                except:
                    self.logger.error(f'Unable to sort, saving screenshot of latest result...')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + collaboranode + "_test_collabora_spreadsheet_" + g_filename + ".png")
                    self.assertTrue(False)
                
                if (EC.presence_of_element_located((By.CLASS_NAME, 'icon-triangle-n'))):
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click
                    self.logger.info(f'Change sorting to descending!')

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-spreadsheet'))).click()
                
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)

                self.logger.info(f'Sleep for 3 seconds...')
                time.sleep(3)
                self.logger.info(f'Proceeding...')

                try:
                    self.logger.info(f'Waiting for collabora frame')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "collaboraframe")))
                    self.logger.info(f'Collabora loaded... Wait for loleafletframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "loleafletframe")))
                    self.logger.info(f'loleafletframe loaded')

                    skipwelcomeframe = False
                    try:
                        self.driver.find_element(by=By.CLASS_NAME, value='iframe-welcome-modal')
                        skipwelcomeframe = False
                    except NoSuchElementException:
                        self.logger.info(f'Quick test iframe-welcome-modal, skipping further checks')
                        skipwelcomeframe = True

                    if skipwelcomeframe == False:                        
                        try:
                            self.logger.info(f'Looking for welcome frame')
                            wait.until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, "iframe-welcome-modal")))
                            self.logger.info(f'Switched to iframe-welcome-modal')
                        except:
                            self.logger.info(f'No welcome frame found, skipping any further checks')
                            skipwelcomeframe = True

                    if skipwelcomeframe == False:
                        self.logger.info(f'Welcome screen found, trying to close it...')

                        wait.until(EC.presence_of_element_located((By.ID, 'slide-3-indicator'))).click()
                        time.sleep(2)
                        self.logger.info(f'Looking for slide-3-button...')
                        button = self.driver.find_element(By.ID, 'slide-3-button')
                        self.logger.info(f'Button found...')
                        button.click()
                        self.logger.info(f'Slide 3 button clicked...')
                        skipwelcomeframe = True
                    time.sleep(2)
                except:
                    self.logger.info('Proceed...')

                try:
                    blockSuccess = False
                    self.driver.switch_to.default_content()
                    self.logger.info(f'Switched to default content...')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "collaboraframe")))
                    self.logger.info(f'Collabora loaded... Wait for loleafletframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "loleafletframe")))
                    self.logger.info(f'loleafletframe loaded...')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'leaflet-layer'))).click()
                    self.logger.info(f'Can we type in the leaflet layer?')
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.UP).key_up(Keys.CONTROL).perform()
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.LEFT).key_up(Keys.CONTROL).perform()
                    ActionChains(self.driver).send_keys(f'{g_filename}{Keys.ENTER}{Keys.SPACE}1{Keys.ENTER}{Keys.SPACE}2{Keys.ENTER}{Keys.SPACE}3{Keys.ENTER}{Keys.SPACE}4{Keys.ENTER}{Keys.SPACE}').perform()
                    time.sleep(1) # We give collabora a literal second to register the keystrokes before closing the document
                    self.logger.info(f'Closing document...')
                    blockSuccess = True
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'closebuttonimage'))).click()
                    self.logger.info(f'And done...')
                except:
                    self.logger.error(f'Content not found, saving screenshot of latest result...')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                    if (blockSuccess == False):
                        success = False
                self.assertTrue(success)

                self.logger.info(f'Manually open home folder in case closing of document fails')
                self.driver.get(self.drv.get_folder_url(collaboranode,''))

                self.logger.info('End of test!')
                
    # presentation
    def test_collabora_presentation(self):
        delay = 30 # seconds
        global g_isLoggedIn
        global g_loggedInNodes
        wait = WebDriverWait(self.driver, delay)
        
        for collaboranode in self.drv.fullnodes:
            with self.subTest(mynode=collaboranode):
                # if g_isLoggedIn == False:
                if g_loggedInNodes.get(collaboranode) == False:
                    self.logger.info(f'Logging in to {collaboranode}')
                    loginurl = self.drv.get_node_login_url(collaboranode)
                    self.logger.info(f'Login url: {loginurl}')
                    nodeuser = self.drv.get_seleniumuser(collaboranode)
                    nodepwd = self.drv.get_seleniumuserpassword(collaboranode)
                    g_isLoggedIn = True
                    g_loggedInNodes[collaboranode] = True
                
                    self.driver.maximize_window()
                    actions = ActionChains(self.driver)
                    # driver2 = webdriver.Firefox()
                    self.driver.get(loginurl)

                    wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                    wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)
                self.assertTrue(g_loggedInNodes.get(collaboranode))
                success = True

                print('Waiting for app menu')
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
                    self.logger.info(f'Wait for /index.php/apps/files/')
                    wait.until(EC.presence_of_element_located((By.XPATH,'//a[@href="'+ '/index.php/apps/files/' +'"]')))
                    files = self.driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/files/' +'"]')
                    files.click()
                except:
                    self.logger.warning(f'Wait for /index.php/apps/files/ took too long')
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
                print(self.driver.current_url)
                
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-home')))
                
                try:
                    self.driver.find_element(By.XPATH, "//*[contains(@class, 'innernametext') and text()='SeleniumCollaboraTest']")
                    self.logger.info(f'SeleniumCollaboraTest folder found')
                except:
                    self.logger.info(f'SeleniumCollaboraTest folder not found, creating')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'displayname') and text()='New folder']"))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-folder')]" ))).send_keys('SeleniumCollaboraTest' + Keys.ENTER)

                folderurl = self.drv.get_folder_url(collaboranode, "SeleniumCollaboraTest")
                self.driver.get(folderurl)

                # Sort file list so that new files are created at the beginning of the list
                try:
                    self.logger.info(f'Wait for folder to be sortable')
                    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'SeleniumCollaboraTest')))
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator')))
                except:
                    self.logger.error(f'Unable to sort, saving screenshot of latest result...')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + collaboranode + "_test_collabora_presentation_" + g_filename + ".png")
                    self.assertTrue(False)
                
                if (EC.presence_of_element_located((By.CLASS_NAME, 'icon-triangle-n'))):
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sort-indicator'))).click
                    self.logger.info(f'Change sorting to descending!')

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-add'))).click()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-filetype-presentation'))).click()
                
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-file')]"))).send_keys(g_filename + Keys.ENTER)

                self.logger.info(f'Sleep for 3 seconds...')
                time.sleep(3)
                self.logger.info(f'Proceeding...')

                try:
                    self.logger.info(f'Waiting for collabora frame')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "collaboraframe")))
                    self.logger.info(f'Collabora loaded... Wait for loleafletframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "loleafletframe")))
                    self.logger.info(f'loleafletframe loaded')

                    skipwelcomeframe = False
                    try:
                        self.driver.find_element(by=By.CLASS_NAME, value='iframe-welcome-modal')
                        skipwelcomeframe = False
                    except NoSuchElementException:
                        self.logger.info(f'Quick test iframe-welcome-modal, skipping further checks')
                        skipwelcomeframe = True

                    if skipwelcomeframe == False:                        
                        try:
                            self.logger.info(f'Looking for welcome frame')
                            wait.until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, "iframe-welcome-modal")))
                            self.logger.info(f'Switched to iframe-welcome-modal')
                        except:
                            self.logger.info(f'No welcome frame found, skipping any further checks')
                            skipwelcomeframe = True

                    if skipwelcomeframe == False:
                        self.logger.info(f'Welcome screen found, trying to close it...')

                        wait.until(EC.presence_of_element_located((By.ID, 'slide-3-indicator'))).click()
                        time.sleep(2)
                        self.logger.info(f'Looking for slide-3-button...')
                        button = self.driver.find_element(By.ID, 'slide-3-button')
                        self.logger.info(f'Button found...')
                        button.click()
                        self.logger.info(f'Slide 3 button clicked...')
                        skipwelcomeframe = True
                    time.sleep(2)
                except:
                    self.logger.info('Proceed...')

                try:
                    blockSuccess = False
                    self.driver.switch_to.default_content()
                    self.logger.info(f'Switched to default content...')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "collaboraframe")))
                    self.logger.info(f'Collabora loaded... Wait for loleafletframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "loleafletframe")))
                    self.logger.info(f'loleafletframe loaded...')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'leaflet-layer'))).click()
                    self.logger.info(f'Can we type in the leaflet layer?')

                    ActionChains(self.driver).send_keys(f'Lorem ipsum! {Keys.ENTER}{g_filename}').perform()
                    time.sleep(1) # We give collabora a literal second to register the keystrokes before closing the document

                    self.logger.info(f'Closing document...')
                    blockSuccess = True
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'closebuttonimage'))).click()
                    self.logger.info(f'And done...')
                except:
                    self.logger.error(f'Content not found, saving screenshot of latest result...')
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshots/" + collaboranode + g_filename + ".png")
                    if (blockSuccess == False):
                        success = False
                self.assertTrue(success)

                self.logger.info(f'Manually open home folder in case closing of document fails')
                self.driver.get(self.drv.get_folder_url(collaboranode,''))

                self.logger.info('End of test!')

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
