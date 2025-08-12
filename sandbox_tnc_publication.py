""" Selenium demo to publish Berry Solar Cell dataset using Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""
from datetime import datetime
import sunetnextcloud
from webdav3.client import Client

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os
import sys
import time
import logging
import yaml
import pyotp

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('NextcloudTestTarget')
g_rdsnodes = ["sunet"]
expectedResultsFile = 'expected.yaml'
connector = 'zenodo'    # 'zenodo' or 'osf'
doifile = 'tncdoi.txt'

# Change working directory to script location
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Remove file containing doi
try:
    os.remove(doifile)
except OSError:
    pass

def deleteCookies(driver):
    cookies = driver.get_cookies()
    logger.info(f'Deleting all cookies: {cookies}')
    driver.delete_all_cookies()
    cookies = driver.get_cookies()
    logger.info(f'Cookies deleted: {cookies}')

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

delay = 30 # seconds
drv = sunetnextcloud.TestTarget()
nodeName = 'sunet'

loginurl = drv.get_node_login_url(nodeName)
logger.info(f'URL: {loginurl}')
nodeuser = os.environ.get('Nxuser')
logger.info(f'Username: {nodeuser}')
nodepwd = os.environ.get('Nxpassword')
nodeapppwd = os.environ.get('Nxapppassword')
baseurl='https://sunet.drive.test.sunet.se'
webdavurl = str(baseurl) + '/remote.php/dav/files/' + str(nodeuser) + '/'
add_repositories_url = 'https://sunet.drive.test.sunet.se/index.php/apps/rds/'
zenodouser = os.environ.get("ZENODO_TEST_USER")
zenodopwd = os.environ.get("ZENODO_TEST_USER_PASSWORD")

if nodeuser is None or nodepwd is None or nodeapppwd is None:
    logger.error('Please set all environment variables Nxuser, Nxpassword, Nxapppassword')
    sys.exit()

# Check if the target folder is available
options = {
'webdav_hostname': webdavurl,
'webdav_login' : nodeuser,
'webdav_password' : nodeapppwd,
'webdav_timeout': 30
}

client = Client(options)
target='TNC24Demo'
tsTitle = 'TNC24 - A Berry Solar Cell ' + datetime.now().strftime("%Y-%m-%d %H:%M")

try:
    logger.info(f'Check target folder: {target}')
    result = client.check(target)
    if not result:
        logger.error(f'Folder {target} does not exist on server')
        sys.exit()
except Exception as error:
    logger.error(f'Error during client.check for {target}: {error}')
    sys.exit()

# Clean temporary python folders
tmpFolder = target + '/.ipynb_checkpoints'
logger.info(f'Check temporary folder: {tmpFolder}')
result = client.check(tmpFolder)
logger.info(f'Temporary folder exists: {result}')

if (client.check(tmpFolder)):
    try:
        logger.info(f'Clean temp folder: {tmpFolder}')
        client.clean(tmpFolder)
        logger.info('Remove temp folders')
    except Exception as error:
        logger.error(f'Error removing temporary folder: {tmpFolder}: {error}')
        sys.exit()

# Remove old ro-create file if it exists
tmpFile = target + '/' + 'ro-crate-metadata.json'
logger.info(f'Check ro-crate file: {tmpFile}')
result = client.check(tmpFile)
logger.info(f'ro-crate file exists: {result}')

if (client.check(tmpFile)):
    try:
        logger.info(f'Clean temp file: {tmpFile}')
        client.clean(tmpFile)
        logger.info('Removed temp file')
    except Exception as error:
        logger.error(f'Error removing temporary file: {tmpFile} - {error}')
        sys.exit()

try:
    options = Options()
    driver = webdriver.Chrome(options=options)
except Exception as error:
    logger.error(f'Error initializing Chrome driver: {error}')
# driver2 = webdriver.Firefox()
deleteCookies(driver)
driver.maximize_window()        
driver.get(loginurl)

wait = WebDriverWait(driver, delay)
wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)
# wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

# Wait for TOTP screen
requireTotp = False
try:
    logger.info('Check if TOTP selection dialogue is visible')
    totpselect = driver.find_element(By.XPATH, '//a[@href="' + drv.indexsuffix + '/login/challenge/totp?redirect_url=' + drv.indexsuffix + '/apps/dashboard/' +'"]')
    logger.warning('Found TOTP selection dialogue')
    requireTotp = True
    totpselect.click()
except Exception as error:
    logger.info(f'No need to select TOTP provider: {error}')

if requireTotp:
    nodetotpsecret = drv.get_samlusertotpsecret(nodeName)
    totp = pyotp.TOTP(nodetotpsecret)
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

try:
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
    logger.info('App menu is ready!')
except TimeoutException:
    logger.info('Loading of app menu took too much time!')

driver.implicitly_wait(10) # seconds before quitting
dashboardUrl = drv.get_dashboard_url('sunet')
currentUrl = driver.current_url

try:
    rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/rds/' +'"]')
    rdsAppButton.click()
    proceed = True
except TimeoutException:
    logger.error("Loading RDS took too much time!")
    sys.exit()

try:
    logger.info("Waiting for rds frame")
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
    logger.info("RDS iframe loaded")
    time.sleep(1)
except Exception as error:
    logger.error(f"RDS iframe not loaded: {error}")
    sys.exit()

try:

    # Store the ID of the original window
    logger.info('Save original window handle')
    original_window = driver.current_window_handle
    logger.info(f'Window handle: {original_window}')

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Repositories')]"))).click()

    elem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH,"/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[1]/div[2]/div/div[2]/div/button/span[1]/span"))) 
    if elem.text == 'CONNECT':
        elem.click()
        time.sleep(1)

        logger.info('Loop through until we find a new window handle')
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        logger.info('Done checking window handles')

        wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(zenodouser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(zenodopwd + Keys.ENTER)

        # Allow connection
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'positive'))).click()
        time.sleep(2)
        logger.info('Switch back to original window')
        driver.switch_to.window(original_window)
except Exception as error:
    logger.error(f'Error checking repositories: {error}')
    sys.exit()

try:
    logger.info('Looking for active projects')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Active Projects')]"))).click()
    time.sleep(1)
except Exception as error:
    logger.error(f'Active Projects element not found: {error}')
    sys.exit()

try:
    logger.info('Create new project')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'new project')]"))).click()
    time.sleep(1)
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'New Project element not found: {error}')
    sys.exit()

if connector == 'zenodo':
    try:
        logger.info('Select Zenodo Connector')
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Zenodo')]"))).click()
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
    except Exception as error:
        logger.error(f'Zenodo Connector not found: {error}')
        sys.exit()
elif connector == 'osf':
    try:
        logger.info('Select OSF Connector')
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Open Science Framework')]"))).click()
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
    except Exception as error:
        logger.error(f'OSF Connector not found: {error}')
        sys.exit()
else:
    logger.error(f'Unknown connector: {connector}')
    sys.exit()

time.sleep(3)

try:
    logger.info('Input project name')
    # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Choose')]"))).click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-')]" ))).send_keys(tsTitle)
    time.sleep(1)
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'Could not set project name: {error}')
    sys.exit()

try:
    logger.info('Pick folder')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Pick')]"))).click()
    time.sleep(1)
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'Pick folder not found: {error}')
    sys.exit()

# We need to switch to the parent frame to use RDS here
logger.info('Switch to parent frame')
driver.switch_to.parent_frame() 

try:
    logger.info('Choose source folder?')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Choose source folder')]")))
    logger.error('Choose source folder!')
    time.sleep(1)
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'Choose source folder error: {error}')
    sys.exit()

try:
    logger.info('Set sort order to newest first?')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Modified')]"))).click()
    time.sleep(1)
    # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Modified')]"))).click()
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'Could not change sort order: {error}')
    sys.exit()
    sys.exit()

try:
    logger.info(f'Select folder {target}')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'TNC24Demo')]"))).click()
    time.sleep(1)
    # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '{target}')]"))).click()
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'{target} folder not found: {error}')
    sys.exit()

try:
    logger.info('Click on Choose')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), ' Choose')]"))).click()
    time.sleep(1)
   # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'{target} folder not found: {error}')
    sys.exit()

try:
    logger.info("Switch back to rds iframe")
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
except Exception as error:
    logger.error(f"RDS iframe not loaded: {error}")
    sys.exit()

try:
    logger.info('Continue (to describo)')
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Continue')]"))).click()
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
except Exception as error:
    logger.error(f'Continue button not found: {error}')
    sys.exit()

time.sleep(3)

logger.info("Switch to Describo frame")
try:
    logger.info("Waiting for describo frame")
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "describoWindow")))
    logger.info("Describo iframe loaded")
except Exception as error:
    logger.info(f"Describo iframe not loaded: {error}")
    sys.exit()
time.sleep(3)

if connector == 'zenodo':
    try:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@class='el-input__inner']")))
        elem.click()
        time.sleep(1)
        elem.send_keys(Keys.CONTROL, 'a')
        time.sleep(1)
        elem.send_keys(tsTitle)
        time.sleep(1)
        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Research Object Crate')]"))).click()
        # wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='my Research Object Crate']"))).send_keys('SOMETHING' + Keys.ENTER)
    except Exception as error:
        logger.errot(f'Unable to set project name: {error}')
        sys.exit()
else:
    # OSF Settings
    logger.info("Wait for OSF Settings and click")
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"tab-OSF settings\"]/span"))).click()
    time.sleep(1)

    # Check if we have to delete entries:
    checkForOsfEntries = True
    while checkForOsfEntries:
        try:
            deleteButton = driver.find_element(by=By.CLASS_NAME, value='el-button--danger')
            deleteButton.click()
            logger.info("Deleting existing entries")
            time.sleep(1)
        except Exception as error:
            logger.info(f"No more entries to delete, continue: {error}")
            checkForOsfEntries = False

    try:
        # OSF Text
        logger.info("Click on +Text")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pane-OSF settings"]/div/div[1]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span'))).click()

        # OSF Add OSF Title
        logger.info("Add OSF Title")
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Add text']"))).send_keys(tsTitle + Keys.ENTER)
        time.sleep(3)

        logger.info("Click on +Select for Osfcategory")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[2]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span"))).click()
        logger.info("Click on category dropdown menu")
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Select']"))).click()
        time.sleep(1)
        
        logger.info("Click on third entry in category list")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@id, 'el-popper-container-')]/div/div/div/div[1]/ul/li[3]"))).click()
        time.sleep(1)

        # logger.info(f"Select data category")
        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"el-popper-container-254\"]/div/div/div/div[1]/ul/li[3]"))).click()
        # time.sleep(1)

        logger.info("Click on +TextArea for OSF Description")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[3]/div/div[2]/div[1]/div[1]/div/div[1]/div/button"))).click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'el-textarea__inner'))).send_keys("I made a Berry Solar Cell!")
    except Exception as error:
        logger.error(f'Error entering OSF metadata: {error}')

logger.info("Switch to parent frame")
driver.switch_to.parent_frame() 

logger.info("Click on continue button")
wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Continue')]"))).click()
time.sleep(1)

logger.info("Click on publish button")
# wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Publish')]"))).click()
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button[2]/span'))).click()

try:
    logger.info('Wait maximum 90s for success info')
    idElement = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Project created with ID')]")))
    logger.info(f'ID element found: {idElement.text}')

    if connector == 'zenodo':
        publicationUrl = 'https://sandbox.zenodo.org/records/' + idElement.text.replace('Project created with ID','').replace(' ','')
    else:
        publicationUrl = 'https://test.osf.io/' + idElement.text.replace('Project created with ID','').replace(' ','') + '/'
    logger.info(f'Zenodo URL: {publicationUrl}')

    WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'successfully published')]")))
    logger.info('Dataset successfully published!')
except Exception as error:
    logger.info(f'Error publishing dataset: {error}')

# try:
#     logger.info(f'Try to get DOI string')
#     doiElement = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Published project with DOI')]")))
#     logger.info(f'Project DOI: {doiElement.text.replace('Published project with DOI','').replace(' ','')}')
# except Exception as error:
#     logger.warning(f'Could not get DOI information: {error}')

text_file = open(doifile, "w")
text_file.write(publicationUrl)
text_file.close()

logger.info('End of test!')
