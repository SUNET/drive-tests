""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test Collabora on a local node
"""
from datetime import datetime
import xmlrunner
import unittest
import tempfile
import sunetnextcloud

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdav3.client import Client
import os
import time
import logging
import yaml
import pyotp

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('NextcloudTestTarget')
g_bridgitnodes = ["richir"]
expectedResultsFile = 'expected.yaml'
g_drv = sunetnextcloud.TestTarget(g_testtarget)
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_logger={}

def create_test_data(fullnode):
    nodeuser = g_drv.get_seleniumuser(fullnode)
    g_logger.info(f'Username: {nodeuser}')
    nodepwd = g_drv.get_seleniumuserpassword(fullnode)


    # Create a test file
    try:
        tmpfilename = tempfile.gettempdir() + '/' + fullnode + '_' + g_filename + '.txt'
        filename = fullnode + '_' + g_filename + '.txt'
    except Exception as error:
        g_logger.error(f'Getting temp dir for {fullnode}: {error}')
    
    with open(tmpfilename, 'w') as f:
        f.write('Testdata from Sunet Drive')
        f.close()

    # Create folder for testing using webdav
    url = g_drv.get_webdav_url(fullnode, nodeuser)
    options = {
    'webdav_hostname': url,
    'webdav_login' : nodeuser,
    'webdav_password' : nodepwd 
    }

    client = Client(options)
    directories = ['OSF_TestData', 'Zenodo_TestData']
    for dir in directories:
        g_logger.info(f'Potentially clean test data directory: {dir}')
        g_logger.info(f'Before clean: {client.list()}')

        if f'{dir}/' in client.list():
            g_logger.info(f'Clean directory {dir}')
            client.clean(dir)
        else:
            g_logger.info('Nothing to clean, creating directory')
        client.mkdir(dir)

        targetfile = f'{dir}/{filename}'
        try:
            g_logger.info(f'Uploading {tmpfilename} to {targetfile}')
            client.upload_sync(remote_path=targetfile, local_path=tmpfilename)
        except Exception as error:
            g_logger.error(f'Error uploading file to {fullnode}: {error}')

    g_logger.info(f'User directories: {client.list()}')

class TestBridgITSelenium(unittest.TestCase):
    global g_logger
    g_logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    with open(expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        g_logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        g_logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        g_logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_bridgit_app(self):
        delay = 30 # seconds

        for bridgitnode in g_bridgitnodes:
            with self.subTest(mynode=bridgitnode):
                loginurl = g_drv.get_node_login_url(bridgitnode)
                g_logger.info(f"Login url: {loginurl}")
                nodeuser = g_drv.get_seleniumuser(bridgitnode)
                nodepwd = g_drv.get_seleniumuserpassword(bridgitnode)
                
                try:
                    options = Options()
                    driver = webdriver.Chrome(options=options)
                except Exception as error:
                    g_logger.error(f'Error initializing Chrome driver: {error}')
                    self.assertTrue(False)
                driver.maximize_window()
                # driver2 = webdriver.Firefox()
                driver.get(loginurl)

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    g_logger.info("Page is ready!")
                    proceed = True
                except TimeoutException:
                    g_logger.info("Loading took too much time!")
                    proceed = False

                self.assertTrue(proceed)

                try:
                    bridgitAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/apps/rdsng/' +'"]')
                    bridgitAppButton.click()
                    proceed = True
                except TimeoutException:
                    g_logger.info("Loading BridgIT took too much time!")
                    proceed = False

                self.assertTrue(proceed)

                g_logger.info('End of test!')
                time.sleep(5)

    def test_bridgit_connections(self):
        global g_logger
        g_logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        g_drv = sunetnextcloud.TestTarget()

        osfConfigured = False
        osfConnected = True
        osfConnectButton = None
        zenodoConfigured = False
        zenodoConnected = True
        zenodoConnectButton = None

        for bridgitnode in g_bridgitnodes:
            with self.subTest(mynode=bridgitnode):
                create_test_data(bridgitnode)

                proceed = True
                loginurl = g_drv.get_node_login_url(bridgitnode)
                g_logger.info(f"Login url: {loginurl}")
                nodeuser = g_drv.get_seleniumuser(bridgitnode)
                nodepwd = g_drv.get_seleniumuserpassword(bridgitnode)

                try:
                    options = Options()
                    driver = webdriver.Chrome(options=options)
                except Exception as error:
                    g_logger.error(f'Error initializing Chrome driver: {error}')
                    self.assertTrue(False)
                # driver2 = webdriver.Firefox()

                # Store ID of the original window handle
                original_window = driver.current_window_handle

                self.deleteCookies(driver)
                driver.maximize_window()        
                driver.get(loginurl)

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    g_logger.info('App menu is ready!')
                except TimeoutException:
                    g_logger.info('Loading of app menu took too much time!')

                try:
                    bridgitAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/apps/rdsng/' +'"]')
                    bridgitAppButton.click()
                    proceed = True
                except TimeoutException:
                    g_logger.error("Loading BridgIT took too much time!")
                    proceed = False

                try:
                    g_logger.info("Waiting for bridgit frame")
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "app-frame")))
                    g_logger.info("BridgIT iframe loaded")
                except Exception as error:
                    g_logger.error(f"BridgIT iframe not loaded: {error}")
                    proceed = False
                
                self.assertTrue(proceed)

                time.sleep(3)
                try:
                    span_element = driver.find_element(By.XPATH, '//span[@class="p-button-label"]')
                    if span_element.text == 'Authorize bridgit':
                        proceed = False
                    g_logger.warning(f'Bridgit needs to connect!')
                except Exception:
                    g_logger.info('BridgIT is already connected')
                    proceed = True
                    pass

                self.assertTrue(proceed)

                hasConnections = True
                for elem in driver.find_elements(By.XPATH, './/span'):
                    if elem.text == 'No connections yet!':
                        g_logger.info(f'BridgIT has no connections yet...')
                        hasConnections = False
                        break

                if hasConnections:
                    g_logger.info(f'BridgIT already has connections!')

                try:
                    buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
                    settingsButton = None
                    for button in buttons:
                        if button.get_attribute('title') == 'Settings':
                            settingsButton = button
                except Exception as error:
                    g_logger.error(f'Settings button: {error}')
                    self.assertTrue(False)

                # click on settings button
                settingsButton.click()
                g_logger.info(f'Settings button clicked')

                time.sleep(1)

                if hasConnections:
                    g_logger.info('Try to find out which connections are available')

                    # look for p-tag-label buttons for the repositories and click on the first one
                    repositoryElements = driver.find_elements(By.CLASS_NAME, 'truncate')
                    for elem in repositoryElements:
                        g_logger.info(f'{elem.text}')
                        elementText = elem.get_attribute('title') # Get title text to see if it is the OSF or Zenodo button

                        if 'Open Science Framework' in elementText:
                            osfConfigured = True
                        elif 'Zenodo' in elementText:
                            zenodoConfigured = True

                    g_logger.info(f'OSF Configured: {osfConfigured}')
                    g_logger.info(f'Zenodo Configured: {zenodoConfigured}')

                if not osfConfigured:
                    g_logger.info(f'Configure OSF')
                    for elem in driver.find_elements(By.XPATH, './/span'):
                        if elem.text == 'Add a new connection...':
                            g_logger.info(f'Click on new connection')
                            elem.click()
                            break

                    # look for p-tag-label buttons for the repositories and click on the first one
                    repositoryButtons = driver.find_elements(By.CLASS_NAME, 'truncate')
                    addOSFButton = None
                    for button in repositoryButtons:
                        buttonText = button.get_attribute('title') # Get title text to see if it is the OSF or Zenodo button

                        if 'OSF' in buttonText:
                            addOSFButton = button

                    # Only OSF first
                    addOSFButton.click()

                    # Wait until we can input some text
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-inputtext'))).send_keys('OSF Connection' + Keys.ENTER)
                    g_logger.info(f'OSF Connection configured')

                if not zenodoConfigured:
                    g_logger.info(f'Configure Zenodo')
                    for elem in driver.find_elements(By.XPATH, './/span'):
                        if elem.text == 'Add a new connection...':
                            g_logger.info(f'Click on new connection')
                            elem.click()
                            break

                    # look for p-tag-label buttons for the repositories and click on the first one
                    repositoryButtons = driver.find_elements(By.CLASS_NAME, 'truncate')
                    addOSFButton = None
                    for button in repositoryButtons:
                        buttonText = button.get_attribute('title') # Get title text to see if it is the OSF or Zenodo button

                        if 'Zenodo' in buttonText:
                            addZenodoButton = button

                    # Only OSF first
                    addZenodoButton.click()

                    # Wait until we can input some text
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-inputtext'))).send_keys('Zenodo Connection' + Keys.ENTER)
                    g_logger.info(f'Zenodo Connection configured')

                time.sleep(1)
                g_logger.info('Check if OSF and Zenodo are also connected')
                try:
                    buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
                    settingsButton = None
                    for button in buttons:
                        if button.text == 'Connect':
                            
                            parent = button.find_element(By.XPATH, '../..')
                            g_logger.info(f'Button parent text: {parent.text}')

                            if 'OSF Connection' in parent.text:
                                g_logger.info(f'Save OSF connect button')
                                osfConnectButton = button
                                osfConnected = False

                            if 'Zenodo Connection' in parent.text:
                                g_logger.info(f'Save Zenodo connect button')
                                zenodoConnectButton = button
                                zenodoConnected = False

                except Exception as error:
                    g_logger.error(f'Connect button: {error}')
                    self.assertTrue(False)

                if not osfConnected:

                    osfuserenv = "OSF_TEST_USER"
                    osfuser = os.environ.get(osfuserenv)
                    osfpwdenv = "OSF_TEST_USER_PASSWORD"
                    osfpwd = os.environ.get(osfpwdenv)


                    g_logger.info('Click on OSF Connect button')
                    osfConnectButton.click()

                    # Loop through until we find a new window handle
                    for window_handle in driver.window_handles:
                        if window_handle != original_window:
                            driver.switch_to.window(window_handle)
                            break

                    wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(osfuser)
                    wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(osfpwd + Keys.ENTER)

                    # Allow connection
                    WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="allow"]/span'))).click()
                    g_logger.info('Done connecting to OSF')

                    # Switch back to main window
                    driver.switch_to.window(original_window)

                    time.sleep(5)

                if not zenodoConnected:
                    # Get connect buttons again
                    try:
                        buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
                        settingsButton = None
                        for button in buttons:
                            if button.text == 'Connect':
                                
                                parent = button.find_element(By.XPATH, '../..')
                                g_logger.info(f'Button parent text: {parent.text}')

                                if 'OSF Connection' in parent.text:
                                    g_logger.info(f'Save OSF connect button')
                                    osfConnectButton = button
                                    osfConnected = False

                                if 'Zenodo Connection' in parent.text:
                                    g_logger.info(f'Save Zenodo connect button')
                                    zenodoConnectButton = button
                                    zenodoConnected = False

                    except Exception as error:
                        g_logger.error(f'Connect button: {error}')
                        self.assertTrue(False)

                    zenodouserenv = "ZENODO_TEST_USER"
                    zenodouser = os.environ.get(zenodouserenv)
                    zenodopwdenv = "ZENODO_TEST_USER_PASSWORD"
                    zenodopwd = os.environ.get(zenodopwdenv)

                    g_logger.info('Click on Zenodo Connect button')
                    zenodoConnectButton.click()

                    # Loop through until we find a new window handle
                    for window_handle in driver.window_handles:
                        if window_handle != original_window:
                            driver.switch_to.window(window_handle)
                            break

                    wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(zenodouser)
                    wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(zenodopwd + Keys.ENTER)
                    # Allow connection
                    WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.CLASS_NAME, 'positive'))).click()
                    g_logger.info(f'Done connecting to Zenodo')

                    # Switch back to main window
                    driver.switch_to.window(original_window)

                    time.sleep(15)

                g_logger.info('Done...')

    def test_bridgit_osf(self):
        g_logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        g_drv = sunetnextcloud.TestTarget()

        for bridgitnode in g_bridgitnodes:
            with self.subTest(mynode=bridgitnode):
                loginurl = g_drv.get_node_login_url(bridgitnode)
                g_logger.info(f"Login url: {loginurl}")
                nodeuser = g_drv.get_seleniumuser(bridgitnode)
                nodepwd = g_drv.get_seleniumuserpassword(bridgitnode)

                # nodeName = 'su'
                # if len(g_drv.allnodes) == 1:
                #     if g_drv.allnodes[0] != nodeName:
                #         g_logger.info(f'Only testing {g_drv.allnodes[0]}, not testing su saml')
                #         return

                # loginurl = g_drv.get_gss_url()
                # g_logger.info(f'URL: {loginurl}')
                # samluser=g_drv.get_samlusername(nodeName)
                # g_logger.info(f'Username: {samluser}')
                # samlpassword=g_drv.get_samluserpassword(nodeName)
                
                try:
                    options = Options()
                    driver = webdriver.Chrome(options=options)
                except Exception as error:
                    g_logger.error(f'Error initializing Chrome driver: {error}')
                    self.assertTrue(False)
                # driver2 = webdriver.Firefox()
                self.deleteCookies(driver)
                driver.maximize_window()        
                driver.get(loginurl)

                # wait = WebDriverWait(driver, delay)

                # loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

                # wait.until(EC.presence_of_element_located((By.LINK_TEXT, loginLinkText))).click()
                # driver.implicitly_wait(10)

                # wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
                # driver.implicitly_wait(10)
                
                # wait.until(EC.presence_of_element_located((By.ID, 'searchinput'))).send_keys("su.se", Keys.RETURN)
                # driver.implicitly_wait(10)

                # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'label-url'))).click()
                # driver.implicitly_wait(10)

                # wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(samluser)
                # wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(samlpassword + Keys.ENTER)
                # # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

                # # Wait for TOTP screen
                # requireTotp = False
                # try:
                #     g_logger.info('Check if TOTP selection dialogue is visible')
                #     totpselect = driver.find_element(By.XPATH, '//a[@href="' + g_drv.indexsuffix + '/login/challenge/totp?redirect_url=' + g_drv.indexsuffix + '/apps/dashboard/' +'"]')
                #     g_logger.warning('Found TOTP selection dialogue')
                #     requireTotp = True
                #     totpselect.click()
                # except Exception as error:
                #     g_logger.info(f'No need to select TOTP provider: {error}')

                # if requireTotp:
                #     nodetotpsecret = g_drv.get_samlusertotpsecret(nodeName)
                #     totp = pyotp.TOTP(nodetotpsecret)
                #     wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

                # try:
                #     wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                #     g_logger.info('App menu is ready!')
                # except TimeoutException:
                #     g_logger.info('Loading of app menu took too much time!')

                # driver.implicitly_wait(10) # seconds before quitting
                # dashboardUrl = g_drv.get_dashboard_url('su')
                # currentUrl = driver.current_url
                # try:
                #     self.assertEqual(dashboardUrl, currentUrl)
                # except Exception as error:       
                #     self.assertEqual(dashboardUrl + '#/', currentUrl)
                #     g_logger.warning(f'Dashboard URL contains trailing #, likely due to the tasks app: {error}')
                # g_logger.info(f'{driver.current_url}')

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    g_logger.info('App menu is ready!')
                except TimeoutException:
                    g_logger.info('Loading of app menu took too much time!')

                try:
                    bridgitAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/apps/rdsng/' +'"]')
                    bridgitAppButton.click()
                    proceed = True
                except TimeoutException:
                    g_logger.error("Loading BridgIT took too much time!")
                    proceed = False

                try:
                    g_logger.info("Waiting for bridgit frame")
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "app-frame")))
                    g_logger.info("BridgIT iframe loaded")
                except Exception as error:
                    g_logger.error(f"BridgIT iframe not loaded: {error}")
                    proceed = False

                try:
                    g_logger.info('Looking for active projects')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Active Projects')]"))).click()
                except Exception as error:
                    g_logger.error(f'Active Projects element not found: {error}')
                    proceed = False

                try:
                    g_logger.info('Create new project')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'new project')]"))).click()
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:
                    g_logger.error(f'New Project element not found: {error}')
                    proceed = False

                try:
                    g_logger.info('Input project name')
                    # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Choose')]"))).click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-')]" ))).send_keys('TestProject')
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:
                    g_logger.error(f'Could not set project name: {error}')
                    proceed = False

                try:
                    g_logger.info('Pick folder')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Pick')]"))).click()
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:
                    g_logger.error(f'Pick folder not found: {error}')
                    proceed = False

                # We need to switch to the parent frame to use BridgIT here
                g_logger.info('Switch to parent frame')
                driver.switch_to.parent_frame() 

                try:
                    g_logger.info('Choose source folder?')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Choose source folder')]")))
                    g_logger.error('Choose source folder!')
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:        
                    g_logger.error(f'Choose source folder error: {error}')
                    proceed = False

                try:
                    g_logger.info('Set sort order to newest first?')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Modified')]"))).click()
                    g_logger.info('Set sort order to newest first!')
                    # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Modified')]"))).click()
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:        
                    g_logger.error(f'Could not change sort order: {error}')
                    proceed = False

                try:
                    g_logger.info('Select folder BridgITDemo')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'BridgITDemo')]"))).click()
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:        
                    g_logger.error(f'BridgITDemo folder not found: {error}')
                    proceed = False

                try:
                    g_logger.info('Click on Choose')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), ' Choose')]"))).click()
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:
                    g_logger.error(f'BridgITDemo folder not found: {error}')
                    proceed = False

                try:
                    g_logger.info("Switch back to bridgit iframe")
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "app-frame")))
                except Exception as error:
                    g_logger.error(f"BridgIT iframe not loaded: {error}")
                    proceed = False

                try:
                    g_logger.info('Select OSF Connector')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Open Science Framework')]"))).click()
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:        
                    g_logger.error(f'OSF Connector not found: {error}')
                    proceed = False

                time.sleep(3)

                try:
                    g_logger.info('Continue (to describo)')
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Continue')]"))).click()
                    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
                except Exception as error:
                    g_logger.error(f'Continue button not found: {error}')
                    proceed = False

                time.sleep(3)

                g_logger.info("Switch to Describo frame")
                try:
                    g_logger.info("Waiting for describo frame")
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "describoWindow")))
                    g_logger.info("Describo iframe loaded")
                except Exception as error:
                    g_logger.info(f"Describo iframe not loaded: {error}")
                    proceed = False
                time.sleep(3)

                # OSF Settings
                g_logger.info("Wait for OSF Settings and click")
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"tab-OSF settings\"]/span"))).click()
                time.sleep(1)

                # Check if we have to delete entries:
                checkForOsfEntries = True
                while checkForOsfEntries:
                    try:
                        deleteButton = driver.find_element(by=By.CLASS_NAME, value='el-button--danger')
                        deleteButton.click()
                        g_logger.info("Deleting existing entries")
                        time.sleep(1)
                    except Exception as error:
                        g_logger.info(f"No more entries to delete, continue: {error}")
                        checkForOsfEntries = False

                try:
                    # OSF Text
                    g_logger.info("Click on +Text")
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pane-OSF settings"]/div/div[1]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span'))).click()

                    # OSF Add Text, again random number ID
                    g_logger.info("Add OSF Title")
                    tsTitle = "BridgIT Sunet Drive Title - " + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Add text']"))).send_keys(tsTitle + Keys.ENTER)
                    time.sleep(3)

                    g_logger.info("Click on +Select for Osfcategory")
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[2]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span"))).click()
                    g_logger.info("Click on category dropdown menu")
                    wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Select']"))).click()
                    time.sleep(1)
                    
                    g_logger.info("Click on third entry in category list")
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@id, 'el-popper-container-')]/div/div/div/div[1]/ul/li[3]"))).click()
                    time.sleep(1)
            
                    # g_logger.info(f"Select data category")
                    # wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"el-popper-container-254\"]/div/div/div/div[1]/ul/li[3]"))).click()
                    # time.sleep(1)

                    g_logger.info("Click on +TextArea for OSF Description")
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[3]/div/div[2]/div[1]/div[1]/div/div[1]/div/button"))).click()
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'el-textarea__inner'))).send_keys("OSF Project Description")
                except Exception as error:
                    g_logger.error(f'Error entering OSF metadata {error}')

                g_logger.info("Switch to parent frame")
                driver.switch_to.parent_frame() 

                g_logger.info("Click on continue button")
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Continue')]"))).click()

                g_logger.info("Click on publish button")
                # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Publish')]"))).click()
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button[2]/span'))).click()

                try:
                    g_logger.info('Wait maximum 60s for success info')
                    idElement = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Project created with ID')]")))
                    g_logger.info(f'ID element found: {idElement.text}')

                    osfUrl = 'https://test.osf.io/' + idElement.text.replace('Project created with ID','').replace(' ','') + '/'
                    g_logger.info(f'OSF URL: {osfUrl}')

                    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'successfully published')]")))
                    g_logger.info('Dataset successfully published!')
                except Exception as error:
                    g_logger.info(f'Error publishing dataset {error}')

                try:
                    g_logger.info('Try to get DOI string')
                    doiElement = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Published project with DOI')]")))
                    g_logger.info(f'Project DOI: {doiElement.text.replace('Published project with DOI','').replace(' ','')}')
                except Exception as error:
                    g_logger.warning(f'Could not get DOI information: {error}')

                self.assertTrue(proceed)

        g_logger.info('End of test!')

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
