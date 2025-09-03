""" Bridgit publish tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Connect Bridgit to OSF and Zenodo and publish data
"""
from datetime import datetime
import xmlrunner
import HtmlTestRunner
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

# 'prod' for production environment, 'test' for test environment, 'custom' for custom environment
g_testtarget = os.environ.get('NextcloudTestTarget')
g_bridgitnodes = ["richir"]
g_required_connections = ['OSF', 'Zenodo']
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

# Metadata add creator button
def get_bridgit_add_creator_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'capitalize')
        for button in buttons:
            if button.get_attribute('title') == 'Add new Creator':
                return button
    except Exception as error:
        g_logger.error(f'Add creator button: {error}')
        return None
    return None

# Metadata add subject button
def get_bridgit_add_subject_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'capitalize')
        for button in buttons:
            if button.get_attribute('title') == 'Add new Subject':
                return button
    except Exception as error:
        g_logger.error(f'Add subject button: {error}')
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

def get_bridgit_upload_project_close_button(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'p-button')
        for button in buttons:
            if button.get_attribute('aria-label') == 'Close':
                return button
    except Exception as error:
        g_logger.error(f'Upload project close button: {error}')
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
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="allow"]/span'))).click()
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
                driver.set_window_size(1920, 1152)
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
                driver.set_window_size(1920, 1152)        
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

                self.deleteCookies(driver)
                driver.set_window_size(1920, 1152)        
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
                if newProjectButton is None:
                    g_logger.warning(f'New project button not found. Wait a few seconds and try again!')
                    time.sleep(3)
                    newProjectButton = get_bridgit_new_project_button(driver)
                    if newProjectButton is None:
                        g_logger.error(f'New project button not found!')
                        self.assertTrue(False)
                wait.until(EC.element_to_be_clickable(newProjectButton))
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
                    proceed = False
                
                self.assertTrue(proceed)

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
                    proceed = False
                
                self.assertTrue(proceed)

                # Type the abstract name
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-textarea')))
                driver.find_element(By.CLASS_NAME, 'p-textarea').send_keys('project abstract')

                # Click on OSF Category
                driver.find_element(By.CLASS_NAME, 'p-select-label').click()
                time.sleep(1)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-select-option-label')))
                # Go through select option labels and click on data
                optionSelectElements = driver.find_elements(By.CLASS_NAME, 'p-select-option-label')
                for optionSelectElement in optionSelectElements:
                    if optionSelectElement.text == 'data':
                        g_logger.info(f'Select {optionSelectElement.text}')
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
                    proceed = False
                
                self.assertTrue(proceed)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-toast-summary')))
                except Exception as error:
                    g_logger.info(f'Upload summary not found')
                    proceed = False
                
                self.assertTrue(proceed)

                summary = driver.find_element(By.CLASS_NAME, 'p-toast-summary')
                if summary.text == 'Job completed':
                    g_logger.info(f'Data successfully published to OSF')
                else:
                    g_logger.error(f'Error publishing data: {summary.text}')

                # Close the upload dialog
                closeButton = get_bridgit_upload_project_close_button(driver)
                closeButton.click()

                # Click on Overview to get the link to the data
                for legendLabelElement in driver.find_elements(By.CLASS_NAME, 'p-fieldset-legend-label'):
                    if legendLabelElement.text == 'Overview':
                        g_logger.info(f'Click on Overview')
                        legendLabelElement.click()

                try:
                    publicationLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'test.osf.io')
                    g_logger.info(f'Data published at {publicationLink.text}')
                except Exception as error:
                    g_logger.error(f'OSF publication link not found')
                    proceed = False
                
                self.assertTrue(proceed)

        g_logger.info(f'Done...')
        time.sleep(5)

    def test_bridgit_zenodo(self):
        g_logger.info(f'TestID: {self._testMethodName}')
        g_delay = 30 # seconds
        g_drv = sunetnextcloud.TestTarget()

        projectName = 'Zenodo Project'
        folderName = 'Zenodo_TestData'

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

                self.deleteCookies(driver)
                driver.set_window_size(1920, 1152)        
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
                if newProjectButton is None:
                    g_logger.warning(f'New project button not found. Wait a few seconds and try again!')
                    time.sleep(3)
                    newProjectButton = get_bridgit_new_project_button(driver)
                    if newProjectButton is None:
                        g_logger.error(f'New project button not found!')
                        self.assertTrue(False)
                wait.until(EC.element_to_be_clickable(newProjectButton))
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
                    if legendLabelElement.text == 'Metadata':
                        g_logger.info(f'Click on Metadata')
                        legendLabelElement.click()

                # Click on the chip label for Zenodo
                try:
                    for chipLabelElement in driver.find_elements(By.CLASS_NAME, 'p-chip-label'):
                        if chipLabelElement.text == 'Zenodo':
                            g_logger.info(f'Click on Zenodo chip label')
                            chipLabelElement.click()
                            break
                except Exception as error:
                    g_logger.error(f'{error}')
                    proceed = False
                
                self.assertTrue(proceed)

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
                    proceed = False
                
                self.assertTrue(proceed)

                # Type the abstract name
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-textarea')))
                driver.find_element(By.CLASS_NAME, 'p-textarea').send_keys('project abstract')

                # Click on Creator
                addCreatorButton = get_bridgit_add_creator_button(driver)
                if addCreatorButton is not None:
                    addCreatorButton.click()
                else:
                    g_logger.error('Unable to find add creator button')
                    proceed = False
                
                self.assertTrue(proceed)

                # Wait for Name input field
                try:
                    g_logger.info(f'Write creator name')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-inputtext')))
                    inputElements = driver.find_elements(By.CLASS_NAME, 'p-inputtext')
                    g_logger.info(f'Found {len(inputElements)} input elements')
                    for inputElement in inputElements:
                        if 'Name' in inputElement.find_element(By.XPATH, '../..').text:
                            g_logger.info(f'Write creator name')
                            inputElement.send_keys('Sunet Drive Bridgit Testautomation User')
                            time.sleep(1)
                            inputElement.send_keys(Keys.ESCAPE)                            
                            break                        
                except Exception as error:
                    g_logger.error(f'{error}')
                    proceed = False
                
                self.assertTrue(proceed)

                # Click on Subject
                addCreatorButton = get_bridgit_add_subject_button(driver)
                if addCreatorButton is not None:
                    addCreatorButton.click()
                else:
                    g_logger.error('Unable to find add subject button')
                    proceed = False
                
                self.assertTrue(proceed)

                # Wait for Subject input field
                try:
                    g_logger.info(f'Write subject name')
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-inputtext')))
                    inputElements = driver.find_elements(By.CLASS_NAME, 'p-inputtext')
                    g_logger.info(f'Found {len(inputElements)} input elements')
                    for inputElement in inputElements:
                        if inputElement.find_element(By.XPATH, '../..').text == '': # TODO: Bridgit should introduce a label here that is not empty
                            g_logger.info(f'Write subject name')
                            inputElement.send_keys('testautomations')
                            time.sleep(1)
                            inputElement.send_keys(Keys.ESCAPE)                            
                            break                        
                except Exception as error:
                    g_logger.error(f'{error}')
                    proceed = False
                
                self.assertTrue(proceed)

                # Click on Zenodo Upload Type
                driver.find_element(By.CLASS_NAME, 'p-select-label').click()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-select-option-label')))
                # Go through select option labels and click on data
                optionSelectElements = driver.find_elements(By.CLASS_NAME, 'p-select-option-label')
                for optionSelectElement in optionSelectElements:
                    g_logger.info(f'option: {optionSelectElement.text}')
                    if optionSelectElement.text == 'dataset':
                        optionSelectElement.click()
                        break

                # Click on upload
                uploadButton = get_bridgit_upload_project_button(driver)
                uploadButton.click()
                time.sleep(2)

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-dialog-title')))
                # Click on OSF upload button
                osfUploadButton = get_bridgit_zenodo_upload_button(driver)
                if osfUploadButton is not None:
                    osfUploadButton.click()
                else:
                    g_logger.error(f'Zenodo Upload button not found! Did you forget to connect to Zenodo?')
                    proceed = False
                
                self.assertTrue(proceed)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-toast-summary')))
                except Exception as error:
                    g_logger.info(f'Upload summary not found')
                    proceed = False
                
                self.assertTrue(proceed)

                summary = driver.find_element(By.CLASS_NAME, 'p-toast-summary')
                if summary.text == 'Job completed':
                    g_logger.info(f'Data successfully published to Zenodo')
                else:
                    g_logger.error(f'Error publishing data: {summary.text}')

                # Close the upload dialog
                closeButton = get_bridgit_upload_project_close_button(driver)
                closeButton.click()

                # Click on Overview to get the link to the data
                for legendLabelElement in driver.find_elements(By.CLASS_NAME, 'p-fieldset-legend-label'):
                    if legendLabelElement.text == 'Overview':
                        g_logger.info(f'Click on Overview')
                        legendLabelElement.click()

                try:
                    publicationLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'sandbox.zenodo.org')
                    g_logger.info(f'Data published at {publicationLink.text}')
                except Exception as error:
                    g_logger.error(f'Zenodo publication link not found')
                    proceed = False
                
                self.assertTrue(proceed)
        g_logger.info(f'Done...')
        time.sleep(5)

if __name__ == '__main__':
    if g_drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"bridgit-{g_drv.expectedResults[g_drv.target]['status']['version']}-acceptance", add_timestamp=False))
