""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests for mfa zones
* Non mfa user does not have MFA option available
* Non mfa user cannot access MFA protected folder from other user
* Non mfa users see MFA protected folders in their shares, but cannot access them
* MFA user has MFA option available
* MFA user can access MFA protected folder from other user
* MFA protected folders cannot be shared via link/anonymously
"""
import xmlrunner
import unittest
from webdav3.client import Client
import requests
from requests.auth import HTTPBasicAuth
import json
import pyotp
import pyautogui
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import FirefoxOptions
from webdav3.client import Client

import os
import yaml
import time
import logging
from datetime import datetime
import sys
# sys.path.append("..")
# import sunetnextcloud

envFile = '.env.yaml'

g_browser = 'chrome'
geckodriver_path = "/snap/bin/geckodriver"
g_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
ocsheaders = { "OCS-APIRequest" : "true" } 
g_testtarget = os.environ.get('NextcloudTestTarget')
g_driver_timeout = 20
g_webdav_timeout = 30
g_wait={}
g_driver=None
g_logger={}
g_drv={}
g_loggedInNodes={}
g_failedNodes = []

use_driver_service = False
if os.environ.get('SELENIUM_DRIVER_SERVICE') == 'True':
    use_driver_service = True

def prepareOcsMFaShares(nextcloudnode):
    global g_logger, g_drv
    logger = g_logger
    logger.info(f'Prepare OCS Shares for {nextcloudnode}')
    mainfolder = 'OcsMfaTestfolder'
    subfolders = ['OcsTestFolder_NonMfaShared', 'OcsTestFolder_MfaShared']
    users = ['_selenium_' + nextcloudnode, '_selenium_' + nextcloudnode + '_mfa']
    nodeuser = g_drv.get_ocsuser(nextcloudnode)
    nodepwd = g_drv.get_ocsuserapppassword(nextcloudnode)
    url = g_drv.get_webdav_url(nextcloudnode, nodeuser)

    logger.info(f'URL: {url}')
    options = {
    'webdav_hostname': url,
    'webdav_login' : nodeuser,
    'webdav_password' : nodepwd, 
    'webdav_timeout': g_webdav_timeout
    }
    client = Client(options)

    try:
        logger.info(client.list())    
        if not client.check(mainfolder):
            logger.info(f'Creating main test folder: {mainfolder}')
            client.mkdir(mainfolder)
        else:
            logger.info(f'Main test folder {mainfolder} already exists')
    except Exception as e:
        logger.error(f'Error checking or creating folder {mainfolder}: {e}')
        g_failedNodes.append(nextcloudnode)
        return

    try:
        subfolder = ''
        logger.info(client.list(mainfolder))
        for folder in subfolders:
            subfolder = mainfolder + '/' + folder
            if not client.check(subfolder):
                logger.info(f'Creating subfolder {subfolder}')
                client.mkdir(subfolder)
    except Exception as e:
        logger.error(f'Error creating subfolder {subfolder}: {e}')        
        g_failedNodes.append(nextcloudnode)
        return

    sharesUrl = g_drv.get_shares_url(nextcloudnode)
    logger.info(f'Preparing shares: {sharesUrl}')

    sharesUrl = sharesUrl.replace("$USERNAME$", nodeuser)
    sharesUrl = sharesUrl.replace("$PASSWORD$", nodepwd)

    session = requests.Session()
    try:
        r=session.get(sharesUrl, headers=ocsheaders)
    except:
        logger.error(f'Error getting {sharesUrl}')
        g_failedNodes.append(nextcloudnode)
        return

    j = json.loads(r.text)
    logger.info(json.dumps(j, indent=4, sort_keys=True))

    numShares = len(j["ocs"]["data"])
    logger.info(f'{numShares} shares found!')

    for folder in subfolders:
        subfolder = mainfolder + '/' + folder
        for user in users:
            data = {'shareType': 0, 'path': subfolder, 'shareWith': user}
            logger.info(f'Create share: {data}')
            r = session.post(sharesUrl, headers=ocsheaders, data=data)

    # for share in j["ocs"]["data"]:
    #     shareId = share["id"]
    #     deleteShareUrl = g_drv.get_delete_share_url(nextcloudnode, shareId)
    #     logger.info(f'Delete share: {deleteShareUrl}')
    #     deleteShareUrl = deleteShareUrl.replace("$USERNAME$", nodeuser)
    #     deleteShareUrl = deleteShareUrl.replace("$PASSWORD$", nodepwd)
    #     r = session.delete(deleteShareUrl, headers=ocsheaders)

    return

def get_node_login_url(node='localhost:8443', direct=True):
    if direct == True:
        return 'https://' + node + '/login?direct=1'
    else:
        return 'https://' + node

def get_security_settings_url(node='localhost:8443'):
    return 'https://' + node + '/settings/user/security'

def get_webdav_url(node='localhost:8443', username=''):
    return 'https://' + node + '/remote.php/dav/files/' + username + '/'

def delete_cookies(driver):
    global g_logger
    cookies = driver.get_cookies()
    g_logger.info(f'Deleting all cookies: {cookies}')
    driver.delete_all_cookies()    

def nodelogin(nextcloudnode='localhost:8443',user='selenium'):
    global g_wait, g_envConfig, g_driver, g_wait
    delete_cookies(g_driver)
    g_logger.info(f'Logging in to {nextcloudnode}')
    loginurl = get_node_login_url()
    g_logger.info(f'Login url: {loginurl}')

    nodeuser        = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}']
    nodepassword    = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_PASSWORD']
    nodetotpsecret  = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_SECRET']
    nodeapppwd      = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_APP_PASSWORD']

    # if user == 'selenium':
    #     nodeuser = g_drv.get_seleniumuser(nextcloudnode)
    #     nodepwd = g_drv.get_seleniumuserpassword(nextcloudnode)
    # elif user == 'selenium_mfa':
    #     nodeuser = g_drv.get_seleniummfauser(nextcloudnode)
    #     nodepwd = g_drv.get_seleniummfauserpassword(nextcloudnode)
    #     nodetotpsecret = g_drv.get_seleniummfausertotpsecret(nextcloudnode)
    # else:
    #     g_logger.error(f'Unknown user type {user}')
    #     return

    g_isLoggedIn = True
    g_loggedInNodes[nextcloudnode] = True

    g_driver.maximize_window()
    # actions = ActionChains(g_driver)
    # driver2 = webdriver.Firefox()
    g_driver.get(loginurl)

    g_wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
    g_wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepassword + Keys.ENTER)

    if user == 'mfauser':
        # Try totp to save some time
        try:
            totp = pyotp.TOTP(nodetotpsecret)
            time.sleep(3)
            g_wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)
            checkForTotp=False
        except:
            checkForTotp=True

        # Wait for TOTP screen
        if checkForTotp:
            try:
                g_logger.info(f'Check if TOTP selection dialogue is visible')
                g_wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="'+ '/index.php/login/challenge/totp' +'"]')))
                totpselect = g_driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/login/challenge/totp' +'"]')
                g_logger.warning(f'Found TOTP selection dialogue')
                totpselect.click()
            except:
                g_logger.info(f'No need to select TOTP provider')

            totp = pyotp.TOTP(nodetotpsecret)
            time.sleep(3)
            g_wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)
    return

class TestMfaZonesSelenium(unittest.TestCase):
    global g_envConfig, g_driver, g_logger
    # drv = sunetnextcloud.TestTarget(g_testtarget)
    # g_drv=drv
    logger = logging.getLogger(__name__)
    g_logger = logger
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    with open(envFile, "r") as stream:
        g_envConfig=yaml.safe_load(stream)

    mainFolder = 'MfaZones'
    testfolders = ['SeleniumCollaboraTest', 'selenium-system', 'selenium-personal']

    # Some class names of icons changed from Nextcloud 27 to 28
    # version = expectedResults[drv.target]['status']['version']
    homeIcon = 'home-icon'
    addIcon = 'plus-icon'

    try:
        if g_browser == 'chrome':
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument('ignore-certificate-errors')
            driver = webdriver.Chrome(options=options)
        elif g_browser == 'firefox':
            options = FirefoxOptions()
            # options.add_argument("--headless")
            driver = webdriver.Firefox(options=options)
        else:
            g_logger.error(f'Unknown browser {g_browser}')
        g_driver=driver

    except Exception as error:
        logger.error(f'Error initializing driver: {error}')

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')

    def test_mfazones_no_mfauser(self):
        delay = 30 # seconds

        global g_isLoggedIn, g_loggedInNodes, g_wait, g_testtarget
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait

        user = 'nomfauser'
        nodeuser        = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}']
        nodepassword    = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_PASSWORD']
        nodetotpsecret  = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_SECRET']
        nodeapppwd      = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_APP_PASSWORD']

        self.logger.info(f'TestID: Testing node localhost')
        nodelogin('localhost', user=user)

        try:
            myElem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time, saving screenshot')
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshots/" + g_filename + ".png")

        files = g_driver.find_element(By.XPATH, '//a[@href="' + '/apps/files/' +'"]')
        files.click()

        try:
            myElem = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
            self.logger.info(f'All files visible!')
        except TimeoutException:
            self.logger.info(f'Loading of all files took too much time!')

        # Click on first sharing icon in list
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app-content-vue"]/div[3]/table/tbody/tr[1]/td[3]/div/button[2]/span')))
            g_driver.implicitly_wait(g_driver_timeout)
            sharingIcon = g_driver.find_element(By.XPATH, '//*[@id="app-content-vue"]/div[3]/table/tbody/tr[1]/td[3]/div/button[2]/span')
            sharingIcon.click()
        except Exception as e:
            self.logger.error(f'Error for node localhost: {e}')
            return

        # Click on MFA Zone
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-button-mfazone"]')))
            g_driver.implicitly_wait(g_driver_timeout)
            mfaZone = g_driver.find_element(By.XPATH, '//*[@id="tab-button-mfazone"]')
            mfaZone.click()
        except Exception as e:
            self.logger.error(f'Error for node localhost: {e}')
            return

        # Find by text
        try:
            wait.until(EC.presence_of_element_located((By.ID, 'need-mfa')))
            g_driver.implicitly_wait(g_driver_timeout)
        except Exception as e:
            self.logger.error(f'Error for node localhost: {e}')
            return

        self.logger.info(f'Subtest done for localhost')

    def test_mfazones_mfauser(self):
        delay = 30 # seconds

        global g_envConfig, g_wait
        wait = WebDriverWait(self.driver, delay)
        g_wait = wait

        user = 'mfauser'
        nodeuser        = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}']
        nodepassword    = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_PASSWORD']
        nodetotpsecret  = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_SECRET']
        nodeapppwd      = g_envConfig[f'MFA_NEXTCLOUD_{user.upper()}_APP_PASSWORD']

        # Make sure test folder exists
        # nodeuser = g_drv.get_seleniummfauser(fullnode)
        self.logger.info(f'Username: {nodeuser}')
        # nodeapppwd = g_drv.get_seleniummfauserapppassword(fullnode)

        # Create folder for testing using webdav
        url = get_webdav_url(username=nodeuser)
        self.logger.info(f'Url: {url}')
        options = {
        'webdav_hostname': url,
        'webdav_login' : nodeuser,
        'webdav_password' : nodeapppwd 
        }

        client = Client(options)
        client.verify = False
        dir = 'MfaTestFolder'
        self.logger.info(f'Make and check directory: {dir}')
        client.mkdir(dir)
        self.assertEqual(client.list().count(dir + '/'), 1)

        # Log in to the node
        nodelogin('localhost', user=user)
        try:
            myElem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'App menu is ready!')
        except TimeoutException:
            self.logger.info(f'Loading of app menu took too much time, saving screenshot')
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshots/" + 'localhost' + g_filename + ".png")

        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="' + '/apps/files/' +'"]')))
            files = g_driver.find_element(By.XPATH, '//a[@href="' + '/apps/files/' +'"]')
            files.click()
        except:
            self.logger.error(f'Files app icon not found, current url is {g_driver.current_url}')
            self.assertTrue(False)

        try:
            wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
            self.logger.info(f'All files visible!')
        except TimeoutException:
            self.logger.info(f'Loading of all files took too much time, current url is {g_driver.current_url}')

        # Right click on MFA test folder
        actions = ActionChains(g_driver)
        try:
            g_wait.until(EC.presence_of_element_located((By.XPATH, f"//*[@class='files-list__row-name-' and text()='{dir}']")))
            mfaFolder = g_driver.find_element(By.XPATH, f"//*[@class='files-list__row-name-' and text()='{dir}']")
            actions.context_click(mfaFolder).perform()
            time.sleep(1)
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Open details')]"))).click()
            # g_driver.find_element((By.XPATH, "//*[contains(text(), 'MfaTestFolder')]")).context_click()
        except Exception as e:
            self.logger.error(f'Error for node localhost: {e}')
            return

        # Click on MFA Zone
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-button-mfazone"]')))
            g_driver.implicitly_wait(g_driver_timeout)
            mfaZone = g_driver.find_element(By.XPATH, '//*[@id="tab-button-mfazone"]')
            mfaZone.click()
        except Exception as e:
            self.logger.error(f'Error for node localhost: {e}')
            return

        # Check if folder already has MFA so we can deactivate it before the first test
        try:
            g_logger.info(f'List folder before MFA Zone: {client.list(dir)}')
            deactivateMfaBeforeStart=False
        except Exception as e:
            error_message = str(e)
            if "403" in error_message:
                deactivateMfaBeforeStart=True
            else:
                g_logger.error(f'Error checking MFA zone for localhost: {e}')
                self.assertTrue(False)
                return

        # Find by checkbox ID and click it twice to activate/deactivate
        try:
            g_logger.info(f'Wait for MFA checkbox')
            wait.until(EC.presence_of_element_located((By.ID, 'checkbox-radio-switch-mfa')))
            g_logger.info(f'MFA checkbox found')
            wait.until(EC.presence_of_element_located((By.ID, 'have-mfa')))
        except Exception as e:
            g_logger.error(f'Unable to locate mfa zone menus: {e}')

        # Click to deactivate MFA Zone if it is already enabled
        if deactivateMfaBeforeStart:
            try:
                haveMfa = g_driver.find_element(by=By.ID, value='checkbox-radio-switch-mfa')
                actions.move_to_element(haveMfa)
                actions.move_by_offset(50, 10)
                time.sleep(1)
                g_logger.info(f'Klick to deactivate MFA')
                actions.click().perform()
                time.sleep(3)
            except Exception as e:
                g_logger.error(f'Error deactivating previously activated MFA zone: {e}')

        # List files before activating MFA Zone
        try:
            g_logger.info(f'List folder before MFA Zone: {client.list(dir)}')
            time.sleep(3)
        except Exception as e:
            g_logger.error(f'Error before activating MFA zone on node localhost: {e}')
            self.assertTrue(False)
            return

        # Activate MFA Zone and ensure we cannot access the files via WebDAV
        try:
            # g_logger.info(f'Activate MFA')
            haveMfa = g_driver.find_element(by=By.ID, value='checkbox-radio-switch-mfa')
            actions.move_to_element(haveMfa)
            actions.move_by_offset(50, 10)
            time.sleep(1)
            g_logger.info(f'Klick to activate MFA')
            actions.click().perform()
            time.sleep(3)
            content=client.list(dir)
            g_logger.info(f'List after activating MFA Zone: {content}')
            g_logger.error(f'We should not be able to list folders in an active MFA zone!')
            self.assertTrue(False)
        except Exception as e:
            g_logger.info(f'Check if this exception is expected or not')
            error_message = str(e)
            if "failed with code 403" in error_message:
                g_logger.info(f'Expected 403 has occurred')
                self.assertTrue(True)
            elif "False is not true" in error_message:
                g_logger.error(f'MFA Zones do not seem to work on webdav for localhost: {error_message}')
                self.assertTrue(False)
                return
            else:
                g_logger.error(f'Unexpected error on localhost: {error_message}')
                self.assertTrue(False)
                return

        # Deactivate MFA Zone again
        try:
            g_logger.info(f'Deactivate MFA and wait for 3 seconds')
            actions.click().perform()
            time.sleep(3)
            g_logger.info(f'List after deactivating MFA Zone again: {client.list(dir)}')
        except Exception as e:
            g_logger.error(f'Error after deactivating MFA zone: {e}')
            self.assertTrue(False)
            return

        self.logger.info(f'Subtest done for localhost')

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
