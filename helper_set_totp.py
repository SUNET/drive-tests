
import sunetnextcloud
import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pyotp

drv = sunetnextcloud.TestTarget()
if drv.target == 'prod':
    prefix = "PROD"
else:
    prefix = "TEST"

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
logger.info('Set totp for selenium user')
delay = 30

envvars = []

logger.info(f'Testing {drv.allnodes}')

try:
    for fullnode in drv.allnodes:
        usertypes = ['SELENIUM', 'SELENIUM_MFA']

        for usertype in usertypes:

            logger.info(f'Config TOTP for {fullnode}')
            # if fullnode == 'nordunet' or fullnode == 'vinnova':
            #     logger.info(f'Skipping {fullnode} for now')
            #     continue # with next node

            if usertype == 'SELENIUM_MFA':
                otpsecret = drv.get_seleniummfausertotpsecret(fullnode, False)
            else:
                otpsecret = drv.get_seleniumusertotpsecret(fullnode, False)

            if otpsecret != '':
                logger.info(f'Skip setting OTP for {fullnode} since it is already set to {otpsecret}')
                continue # with next node

            sel = sunetnextcloud.SeleniumHelper("chrome", fullnode)
            sel.delete_cookies()
            if usertype == 'SELENIUM_MFA':
                sel.nodelogin(sel.UserType.SELENIUM_MFA, skipAppMenuCheck=True, mfaUser=False)
            else:
                sel.nodelogin(sel.UserType.SELENIUM, skipAppMenuCheck=True, mfaUser=False)
            time.sleep(3)

            driver = sel.driver
            wait = WebDriverWait(driver, delay)

            try:
                totpselect = driver.find_element(By.XPATH, '//a[@href="'+ drv.indexsuffix + '/login/setupchallenge/totp' +'"]')
            except Exception as error:
                logger.info(f'Skipping TOTP setup for {fullnode}')
                continue # with next node

            totpselect.click()
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'setup-confirmation__secret')))
            except Exception as error:
                logger.warning(f'Retry totp challenge')
                driver.get(driver.current_url)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'setup-confirmation__secret')))

            otpsecret = driver.find_element(By.CLASS_NAME, 'setup-confirmation__secret').text.split(' ')[-1]

            message=f'export NEXTCLOUD_{usertype}_SECRET_{fullnode.upper()}_{prefix}={otpsecret}'
            logger.info(f'{message}')
            envvars.append(message)

            totp = pyotp.TOTP(otpsecret)
            currentOtp = totp.now()

            wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(currentOtp + Keys.ENTER)

            # totp = pyotp.TOTP(nodetotpsecret)

            time.sleep(5)
except Exception as error:
    logger.warning(f"Some error, print vars and quit: {error}")


for message in envvars:
    print(message)
