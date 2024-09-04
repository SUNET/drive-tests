import os
import sys
import time
import logging
import pyotp
import yaml
import pyperclip

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdav3.client import Client
import requests
from requests.auth import HTTPBasicAuth
import json

# sys.path.append("..")
# import sunetnextcloud

envFile = '.env.yaml'
# g_drv = sunetnextcloud.TestTarget(envFile)
g_webdav_timeout = 30
g_driver_timeout = 20

mfaUsers=['admin','mfauser']
allUsers=mfaUsers[:]
allUsers.append('nomfauser')

envVariables = dict()
envVariables[f'global'] = dict()
envVariables[f'global']['baseUrl'] = 'localhost:8443'
for user in allUsers:
    envVariables[f'MFA_NEXTCLOUD_{user.upper()}']               = user
    envVariables[f'MFA_NEXTCLOUD_{user.upper()}_PASSWORD']      = user+'password'
    envVariables[f'MFA_NEXTCLOUD_{user.upper()}_SECRET']        = ''
    envVariables[f'MFA_NEXTCLOUD_{user.upper()}_APP_PASSWORD']  = ''

ocsheaders = { "OCS-APIRequest" : "true" } 

try:
    with open(envFile, "r") as stream:
        envVariables=yaml.safe_load(stream)
except:
    with open(envFile, "w") as stream:
        yaml.dump(envVariables, stream, default_flow_style=False)
    with open(envFile, "r") as stream:
        envVariables=yaml.safe_load(stream)

userTotpConfigured = False

g_delay = 30 # seconds webdriver delay
g_totp = None
g_logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

def get_node_login_url(node='localhost:8443', direct=True):
    if direct == True:
        return 'https://' + node + '/login?direct=1'
    else:
        return 'https://' + node

def get_security_settings_url(node='localhost:8443'):
    return 'https://' + node + '/settings/user/security'

def get_app_folder_url(node='localhost:8443', folder=''):
    return 'https://' + node + '/apps/files/files?dir=/' + folder

def get_webdav_url(node='localhost:8443', username=''):
    return 'https://' + node + '/remote.php/dav/files/' + username + '/'

def get_shares_url(node='localhost:8443'):
    return 'https://$USERNAME$:$PASSWORD$@' + node + '/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json'

def delete_cookies(driver):
    global g_logger
    cookies = driver.get_cookies()
    g_logger.info(f'Deleting all cookies: {cookies}')
    driver.delete_all_cookies()    

def prepareOcsMFaShares():
    global g_logger
    logger = g_logger
    logger.info(f'Prepare OCS Shares for localhost')
    mainfolder = 'OcsMfaTestfolder'
    subfolders = ['OcsTestFolder_NonMfaShared', 'OcsTestFolder_MfaShared']
    # users = ['_selenium_' + nextcloudnode, '_selenium_' + nextcloudnode + '_mfa']
    users = ['mfauser','nomfauser'] # Users to test

    user = 'admin'
    nodeuser        = envVariables[f'MFA_NEXTCLOUD_{user.upper()}']
    nodepassword    = envVariables[f'MFA_NEXTCLOUD_{user.upper()}_PASSWORD']
    nodetotpsecret  = envVariables[f'MFA_NEXTCLOUD_{user.upper()}_SECRET']
    nodeapppwd      = envVariables[f'MFA_NEXTCLOUD_{user.upper()}_APP_PASSWORD']

    url = get_webdav_url(username=user)

    logger.info(f'URL: {url}')
    logger.info(f'Username and password: {nodeuser}:{nodeapppwd}')
    options = {
    'webdav_hostname': url,
    'webdav_login' : nodeuser,
    'webdav_password' : nodeapppwd, 
    'webdav_timeout': g_webdav_timeout
    }
    client = Client(options)
    client.verify = False

    try:
        logger.info(client.list())    
        if not client.check(mainfolder):
            logger.info(f'Creating main test folder: {mainfolder}')
            client.mkdir(mainfolder)
        else:
            logger.info(f'Main test folder {mainfolder} already exists')
    except Exception as e:
        logger.error(f'Error checking or creating folder {mainfolder}: {e}')
        # g_failedNodes.append(nextcloudnode)
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
        # g_failedNodes.append(nextcloudnode)
        return

    sharesUrl = get_shares_url()
    logger.info(f'Preparing shares: {sharesUrl}')

    sharesUrl = sharesUrl.replace("$USERNAME$", nodeuser)
    sharesUrl = sharesUrl.replace("$PASSWORD$", nodeapppwd)

    session = requests.Session()
    try:
        r=session.get(sharesUrl, headers=ocsheaders, verify=False)
    except:
        logger.error(f'Error getting {sharesUrl}')
        # g_failedNodes.append(nextcloudnode)
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
            r = session.post(sharesUrl, headers=ocsheaders, data=data, verify=False)

    return

try:
    options = Options()
    options.add_argument('ignore-certificate-errors')
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, g_delay)
except Exception as e:
    g_logger.error(f'Error initializing Chrome driver: {e}')
    sys.exit()

for user in mfaUsers:
    prefix = user.upper()
    userMfaSecret = envVariables[f'MFA_NEXTCLOUD_{prefix}_SECRET']
    if len(userMfaSecret) > 0:
        userTotpConfigured = True
    else:
        g_logger.warning(f'TOTP secret for {user} not set')

    nodeuser=envVariables[f'MFA_NEXTCLOUD_{prefix}']
    nodepwd=envVariables[f'MFA_NEXTCLOUD_{prefix}_PASSWORD']

    delete_cookies(driver)
    driver.get(get_node_login_url())

    wait.until(EC.element_to_be_clickable((By.ID, 'user'))).send_keys(nodeuser)
    wait.until(EC.element_to_be_clickable((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

    # Wait for add TOTP challenge screen
    otp = 0
    if userTotpConfigured == False:
        try:
            g_logger.info(f'Wait for MFA selection dialogue to add TOTP')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="/login/setupchallenge/totp"]'))).click()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME,"setup-confirmation__secret")))
            otpInfo = driver.find_element(By.CLASS_NAME,"setup-confirmation__secret")
            otpSecret = otpInfo.text.replace('Your new TOTP secret is: ','')
            g_logger.info(f'OTP Secret found: {otpSecret}')
            envVariables[f'MFA_NEXTCLOUD_{prefix}_SECRET'] = otpSecret
            with open(envFile, "w") as stream:
                yaml.dump(envVariables, stream, default_flow_style=False)

            g_totp = pyotp.TOTP(otpSecret)
            otp = g_totp.now()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(otp + Keys.ENTER)

        except Exception as e:
            g_logger.error(f'{e}')

    # Wait for TOTP screen
    try:
        if g_totp is None:
            g_totp = pyotp.TOTP(userMfaSecret)    
        else:
            g_logger.info(f'TOTP already initialized')
            while otp == g_totp.now():
                g_logger.info(f'Wait until unused OTP has been issued')
                time.sleep(3)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="/login/challenge/totp?redirect_url=/login/setupchallenge/totp"]'))).click()

        g_logger.info(f'Wait for MFA selection dialogue')
        otp = g_totp.now()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(otp + Keys.ENTER)

    except Exception as e:
        g_logger.error(f'{e}')

    # Open security settings to generate application password
    try:
        driver.get(get_security_settings_url())
        # Scroll to bottom of page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        # Enter application name
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="App name"]'))).send_keys('testautomation' + Keys.ENTER)
        # Get newly generated app password
        wait.until(EC.presence_of_element_located((By.XPATH, '//*//input[@placeholder="Password"]')))
        appPasswordField = driver.find_element(By.XPATH, '//*//input[@placeholder="Password"]')
        appPasswordField.send_keys(Keys.CONTROL + 'c')
        appPassword = pyperclip.paste()
        g_logger.info(f'App password generated: {appPassword}')

        envVariables[f'MFA_NEXTCLOUD_{prefix}_APP_PASSWORD'] = appPassword
        with open(envFile, "w") as stream:
            yaml.dump(envVariables, stream, default_flow_style=False)

    except Exception as e:
        g_logger.error(f'Error creating app password for {user}: {e}')

    # We prepare the OCS shares from the admin account
    if user == 'admin':
        g_logger.info(f'Prepare OCS Shares for {user}')
        prepareOcsMFaShares()
        driver.get(get_app_folder_url(folder='OcsMfaTestfolder'))
        dir = 'OcsTestFolder_MfaShared'      

        # Right click on MFA test folder
        actions = ActionChains(driver)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, f"//*[@class='files-list__row-name-' and text()='{dir}']")))
            mfaFolder = driver.find_element(By.XPATH, f"//*[@class='files-list__row-name-' and text()='{dir}']")
            actions.context_click(mfaFolder).perform()
            time.sleep(1)
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Open details')]"))).click()
            # driver.find_element((By.XPATH, "//*[contains(text(), 'MfaTestFolder')]")).context_click()
        except Exception as e:
            g_logger.error(f'Error for node localhost: {e}')

        # Click on MFA Zone
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-button-mfazone"]')))
            driver.implicitly_wait(g_driver_timeout)
            mfaZone = driver.find_element(By.XPATH, '//*[@id="tab-button-mfazone"]')
            mfaZone.click()
            haveMfa = driver.find_element(by=By.ID, value='checkbox-radio-switch-mfa')
            actions.move_to_element(haveMfa)
            actions.move_by_offset(50, 10)
            time.sleep(1)
            g_logger.info(f'Klick to activate MFA')
            actions.click().perform()
            time.sleep(3)

        except Exception as e:
            g_logger.error(f'Error for node localhost: {e}')

    try:
        wait.until(EC.element_to_be_clickable((By.ID, 'user-menu'))).click()
        logoutLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Log out')
        logoutLink.click()
        g_logger.info(f'Logout complete')
    except Exception as e:
        g_logger.error(f'Error logging out user {user}')

    g_totp = None
    g_logger.info(f'Prepare MFA for {user} done')
    
g_logger.info(f'Done...')
