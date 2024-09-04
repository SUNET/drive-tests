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

# sys.path.append("..")
# import sunetnextcloud

envFile = '.env.yaml'
# g_drv = sunetnextcloud.TestTarget(envFile)

mfaUsers=['admin','mfauser']
allUsers=mfaUsers[:]
allUsers.append('nomfauser')

data = dict()
data[f'global'] = dict()
data[f'global']['baseUrl'] = 'localhost:8443'
for user in allUsers:
    data[f'MFA_NEXTCLOUD_{user.upper()}']               = user
    data[f'MFA_NEXTCLOUD_{user.upper()}_PASSWORD']      = user+'password'
    data[f'MFA_NEXTCLOUD_{user.upper()}_SECRET']        = ''
    data[f'MFA_NEXTCLOUD_{user.upper()}_APP_PASSWORD']  = ''

try:
    with open(envFile, "r") as stream:
        envVariables=yaml.safe_load(stream)
except:
    with open(envFile, "w") as stream:
        yaml.dump(data, stream, default_flow_style=False)
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

def get_webdav_url(node='localhost:8443', username=''):
    return 'https://' + node + '/remote.php/dav/files/' + username + '/'

def delete_cookies(driver):
    global g_logger
    cookies = driver.get_cookies()
    g_logger.info(f'Deleting all cookies: {cookies}')
    driver.delete_all_cookies()    

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
            data[f'MFA_NEXTCLOUD_{prefix}_SECRET'] = otpSecret
            with open(envFile, "w") as stream:
                yaml.dump(data, stream, default_flow_style=False)

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

        data[f'MFA_NEXTCLOUD_{prefix}_APP_PASSWORD'] = appPassword
        with open(envFile, "w") as stream:
            yaml.dump(data, stream, default_flow_style=False)

    except Exception as e:
        g_logger.error(f'Error creating app password for {user}: {e}')



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
