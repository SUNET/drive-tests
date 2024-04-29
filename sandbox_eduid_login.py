
from datetime import datetime
import sunetnextcloud
import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import time

drv = sunetnextcloud.TestTarget()
logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
logger.info(f'Start eduid.se login test')
delay = 30

loginurl = "https://dashboard.eduid.se"
logger.info(f'Login url: {loginurl}')

samluser=drv.get_samlusername("eduidtest")              # From environment variable NEXTCLOUD_SAML_USER_EDUIDTEST_TEST
samlpassword=drv.get_samluserpassword("eduidtest")      # From environment variable NEXTCLOUD_SAML_PASSWORD_EDUIDTEST_TEST
logger.info(f'Logging in with {samluser}')

options = Options()
# options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

for i in range(0,101):
    logger.info(f'Login test {i}')
    driver.get(loginurl)
    wait = WebDriverWait(driver, delay)
    try:
        if i == 0:
            wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(samluser)
        wait.until(EC.presence_of_element_located((By.ID, 'currentPassword'))).send_keys(samlpassword + Keys.ENTER)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'header-user'))).click()
        wait.until(EC.presence_of_element_located((By.ID, 'logout'))).click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-secondary')))
        currentUrl = driver.current_url
        logger.info(f'Logut successful: {currentUrl}')
    except:
        logger.error(f'Something wrong')
        time.sleep(600)

logger.info(f'DONE!')
