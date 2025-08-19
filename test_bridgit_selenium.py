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
g_required_connections = ['OSF', 'Zenodo']
# g_required_connections = ['Zenodo','OSF']
expectedResultsFile = 'expected.yaml'
g_drv = sunetnextcloud.TestTarget(g_testtarget)
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
g_logger={}
g_delay = 30 # seconds


class BridgITConnection():
  def __init__(self, name, configured, connected):
    self.name = name
    self.configured = configured
    self.connected = connected

def get_bridgit_settings_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
        for button in buttons:
            if button.get_attribute('title') == 'Settings':
                return button
    except Exception as error:
        g_logger.error(f'Settings button: {error}')
        return None
    return None

def get_bridgit_new_project_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
        for button in buttons:
            if button.get_attribute('aria-label') == 'New project':
                return button
    except Exception as error:
        g_logger.error(f'New project button: {error}')
        return None
    return None

def get_bridgit_new_project_next_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
        for button in buttons:
            if button.get_attribute('aria-label') == 'Next':
                return button
    except Exception as error:
        g_logger.error(f'New project next button: {error}')
        return None
    return None

def get_bridgit_upload_project_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
        for button in buttons:
            if button.get_attribute('aria-label') == 'Upload project':
                return button
    except Exception as error:
        g_logger.error(f'Upload project button: {error}')
        return None
    return None

def get_bridgit_osf_upload_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'p-button-label')
        for button in buttons:
            parent = button.find_element(By.XPATH, '../../../..')   # Identify button by parent name
            if button.text == 'Upload' and 'OSF' in parent.text:
                return button                
    except Exception as error:
        g_logger.error(f'Upload project button: {error}')
        return None
    return None

def get_bridgit_zenodo_upload_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'p-button-label')
        for button in buttons:
            parent = button.find_element(By.XPATH, '../../../..')   # Identify button by parent name
            if button.text == 'Upload' and 'Zenodo' in parent.text:
                return button                
    except Exception as error:
        g_logger.error(f'Upload project button: {error}')
        return None
    return None

def get_connection_status(driver, connections):
    buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
    for button in buttons:
        if button.text == 'Connect' or button.text == 'Disconnect':
            parent = button.find_element(By.XPATH, '../..')
            configuredConnection = parent.text.split('\n')

            requiredConnection = next((x for x in connections if x.name == configuredConnection[0]), None)

            if requiredConnection:
                g_logger.info(f'Update connection status of {requiredConnection.name}')
                requiredConnection.configured = True
                if button.text == 'Connect':
                    requiredConnection.connected = False
                elif button.text == 'Disconnect':
                    requiredConnection.connected = True

def configure_connection(driver, connection):
    g_logger.info(f'Configuring connection to {connection.name}')
    if connection.configured:
        g_logger.warning(f'{connection.name} is already configured')
        return

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

        if connection.name in buttonText:
            addOSFButton = button

    addOSFButton.click()

    # Wait until we can input some text
    wait = WebDriverWait(driver, g_delay)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-inputtext'))).send_keys(connection.name + Keys.ENTER)
    g_logger.info(f'{connection.name} connection configured')

def connect_connection(driver, connection):
    g_logger.info(f'Connect to {connection.name}')
    original_window = driver.current_window_handle
    wait = WebDriverWait(driver, g_delay)

    if connection.connected:
        g_logger.warning(f'{connection.name} is already configured')
        return

    if 'OSF' in connection.name:
        g_logger.info(f'Start connecting to {connection.name}')
        if get_connector_connect_button(driver, connection.name) is None:
            g_logger.error(f'No connect button found for {connection.name} on {driver.current_url}')
            return
        get_connector_connect_button(driver, connection.name).click()

        osfuserenv = "OSF_TEST_USER"
        osfuser = os.environ.get(osfuserenv)
        osfpwdenv = "OSF_TEST_USER_PASSWORD"
        osfpwd = os.environ.get(osfpwdenv)

        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(osfuser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(osfpwd + Keys.ENTER)

        # Allow connection
        WebDriverWait(driver, g_delay).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="allow"]/span'))).click()
        g_logger.info('Done connecting to OSF')

        # Switch back to main window
        driver.switch_to.window(original_window)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "app-frame")))
        connection.connected = True
    elif 'Zenodo' in connection.name:
        if get_connector_connect_button(driver, connection.name) is None:
            g_logger.error(f'No connect button found for {connection.name} on {driver.current_url}')
            return
        g_logger.info(f'Start connecting to {connection.name}')
        get_connector_connect_button(driver, connection.name).click()

        zenodouserenv = "ZENODO_TEST_USER"
        zenodouser = os.environ.get(zenodouserenv)
        zenodopwdenv = "ZENODO_TEST_USER_PASSWORD"
        zenodopwd = os.environ.get(zenodopwdenv)

        # Loop through until we find a new window handle
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(zenodouser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(zenodopwd + Keys.ENTER)
        # Allow connection
        WebDriverWait(driver, g_delay).until(EC.element_to_be_clickable((By.CLASS_NAME, 'positive'))).click()
        g_logger.info(f'Done connecting to Zenodo')

        # Switch back to main window
        driver.switch_to.window(original_window)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "app-frame")))
        connection.connected = True
    else:
        g_logger.error(f'Unknown connector {connection.name}')
    
def get_connector_connect_button(driver, connectionName):
    g_logger.info(f'Get connector button for {connectionName}')
    buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
    g_logger.info(f'Found {len(buttons)} buttons')

    if len(buttons) == 0:
        g_logger.error(f'Did not find any buttons for {driver.current_url}! Did you forget to switch to the app frame?.')
        return None
    for button in buttons:
        if button.text == 'Connect':
            parent = button.find_element(By.XPATH, '../..')
            g_logger.info(f'Button parent: {parent.text}')
            if connectionName in parent.text:
                return button
    return None

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

                wait = WebDriverWait(driver, g_delay)
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
        g_delay = 30 # seconds
        g_drv = sunetnextcloud.TestTarget()

        for bridgitnode in g_bridgitnodes:
            with self.subTest(mynode=bridgitnode):
                # create_test_data(bridgitnode)

                proceed = True
                loginurl = g_drv.get_node_login_url(bridgitnode)
                g_logger.info(f"Login url: {loginurl}")
                nodeuser = g_drv.get_seleniumuser(bridgitnode)
                nodepwd = g_drv.get_seleniumuserpassword(bridgitnode)

                connections = []
                for required_connection in g_required_connections:
                    connections.append(BridgITConnection(required_connection, False, False))

                g_logger.info(f'The following connections are required:')
                for connection in connections:
                    g_logger.info(f'{connection.name} - {connection.configured} - {connection.connected}')

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

                wait = WebDriverWait(driver, g_delay)
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

                settingsButton = get_bridgit_settings_button(driver)
                settingsButton.click()
                g_logger.info(f'Settings button clicked')

                time.sleep(1)

                get_connection_status(driver, connections)
                configuredConnections = connections
                for connection in connections:
                    g_logger.info(f'{connection.name} - {connection.configured} - {connection.connected}')

                get_connection_status(driver, connections)                
                requiredConfiguration = next((x for x in connections if x.configured == False), None)
                while requiredConfiguration is not None:
                    g_logger.info(f'Configure {requiredConfiguration.name}')
                    configure_connection(driver, requiredConfiguration)
                    time.sleep(7) # TODO: Wait for connecting in UI
                    get_connection_status(driver, connections)
                    requiredConfiguration = next((x for x in connections if x.configured == False), None)

                get_connection_status(driver, connections)
                requiredConnection = next((x for x in connections if x.connected == False), None)
                while requiredConnection is not None:
                    g_logger.info(f'Connect to {requiredConnection.name}')
                    connect_connection(driver, requiredConnection)
                    time.sleep(7)  # TODO: Wait for connecting in UI
                    get_connection_status(driver, connections)
                    requiredConnection = next((x for x in connections if x.connected == False), None)
                    time.sleep(1)

                time.sleep(5)
                g_logger.info('Done...')

    def test_bridgit_osf(self):
        g_logger.info(f'TestID: {self._testMethodName}')
        g_delay = 30 # seconds
        g_drv = sunetnextcloud.TestTarget()

        projectName = 'OSF Project'
        folderName = 'OSF_TestData'

        for bridgitnode in g_bridgitnodes:
            with self.subTest(mynode=bridgitnode):
                # create_test_data(bridgitnode)

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

                self.deleteCookies(driver)
                driver.maximize_window()        
                driver.get(loginurl)

                wait = WebDriverWait(driver, g_delay)
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

                newProjectButton = get_bridgit_new_project_button(driver)
                newProjectButton.click()
                g_logger.info(f'New project button clicked')


                wait = WebDriverWait(driver, g_delay)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-inputtext'))).send_keys(projectName + Keys.ENTER)
                g_logger.info(f'{projectName} created')

                newProjectNextButton = get_bridgit_new_project_next_button(driver)
                newProjectNextButton.click()

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-tree-node-label')))
                                
                for folderTreeElement in driver.find_elements(By.CLASS_NAME, 'p-tree-node-label'):
                    if folderTreeElement.text == folderName:
                        g_logger.info(f'Folder tree element found: {folderTreeElement.text}')
                        folderTreeElement.click()

                newProjectNextButton.click()
                newProjectNextButton.click()
                newProjectNextButton.click()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-fieldset-legend-label')))
                time.sleep(3)

                # Click on 'Metadata'
                for legendLabelElement in driver.find_elements(By.CLASS_NAME, 'p-fieldset-legend-label'):
                    g_logger.info(f'Label found: {legendLabelElement.text}')
                    if legendLabelElement.text == 'Metadata':
                        g_logger.info(f'Click on Metadata')
                        legendLabelElement.click()

                # Click on the chip label for OSF
                try:
                    for chipLabelElement in driver.find_elements(By.CLASS_NAME, 'p-chip-label'):
                        if chipLabelElement.text == 'OSF':
                            g_logger.info(f'Click on OSF chip label')
                            chipLabelElement.click()
                            break
                except Exception as error:
                    g_logger.error(f'{error}')

                # Wait for project title input field
                try:
                    g_logger.info(f'Write project title')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-inputtext')))
                    inputElements = driver.find_elements(By.CLASS_NAME, 'p-inputtext')
                    for inputElement in inputElements:
                        if inputElement.find_element(By.XPATH, '../..').text == 'Title':
                            inputElement.send_keys(projectName)
                            break                        
                except Exception as error:
                    g_logger.error(f'{error}')

                # Type the abstract name
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-textarea')))
                driver.find_element(By.CLASS_NAME, 'p-textarea').send_keys('project abstract')

                # Click on OSF Category
                driver.find_element(By.CLASS_NAME, 'p-select-label').click()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-select-option-label')))
                # Go through select option labels and click on data
                optionSelectElements = driver.find_elements(By.CLASS_NAME, 'p-select-option-label')
                for optionSelectElement in optionSelectElements:
                    g_logger.info(f'option: {optionSelectElement.text}')
                    if optionSelectElement.text == 'data':
                        optionSelectElement.click()
                        break

                # Click on upload
                uploadButton = get_bridgit_upload_project_button(driver)
                uploadButton.click()
                time.sleep(2)

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-dialog-title')))
                # Click on OSF upload button
                osfUploadButton = get_bridgit_osf_upload_button(driver)
                if osfUploadButton is not None:
                    osfUploadButton.click()
                else:
                    g_logger.error(f'OSF Upload button not found! Did you forget to connect to OSF?')

        g_logger.info(f'Done...')
        time.sleep(5)

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

                # wait = WebDriverWait(driver, g_delay)

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

                wait = WebDriverWait(driver, g_delay)
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
