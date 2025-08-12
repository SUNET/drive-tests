""" Selenium tests for RDS Development Environment
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to the RDS test node, performing various operations to ensure basic operation
"""
import xmlrunner
import unittest
# import sunetnextcloud
import logging

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os

# Set usernames and passwords in environment variables
g_rds_dev_url               = os.environ.get('RDS_DEV_URL')
g_rds_dev_user              = os.environ.get('RDS_DEV_USER')
g_rds_dev_password          = os.environ.get('RDS_DEV_USER_PASSWORD')
g_rds_dev_app_password      = os.environ.get('RDS_DEV_USER_APP_PASSWORD')

g_rds_dev_sso_user          = os.environ.get('RDS_DEV_SSO_USER')
g_rds_dev_sso_password      = os.environ.get('RDS_DEV_SSO_USER_PASSWORD')
g_rds_dev_sso_app_password  = os.environ.get('RDS_DEV_SSO_USER_APP_PASSWORD')

class TestRdsDevConnect(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info('self.logger.info test_logger')
        pass

    def test_rds_dev_authorization(self):
        self.logger.info(f'Test RDS connect for user: {g_rds_dev_user}')
        delay = 30 # seconds

        osfuserenv = "OSF_TEST_USER"
        osfuser = os.environ.get(osfuserenv)
        osfpwdenv = "OSF_TEST_USER_PASSWORD"
        osfpwd = os.environ.get(osfpwdenv)

        # zenodouserenv = "ZENODO_TEST_USER"
        # zenodouser = os.environ.get(zenodouserenv)
        # zenodopwdenv = "ZENODO_TEST_USER_PASSWORD"
        # zenodopwd = os.environ.get(zenodopwdenv)

        osfButtonIndex = '1'
        # zenodoButtonIndex = '1'

        chromeOptions = Options()

        driver = webdriver.Chrome(options=chromeOptions)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(g_rds_dev_url)

        # Store the ID of the original window
        original_window = driver.current_window_handle
        self.logger.info(f'Window handle: {original_window}')

        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(g_rds_dev_user)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(g_rds_dev_password + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info('Page is ready!')
            proceed = True
        except TimeoutException:
            self.logger.error('Loading app-menu took too much time!')
            proceed = False

        self.assertTrue(proceed)

        try:
            # rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/rds/' +'"]')
            rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/apps/rds/' +'"]')
            rdsAppButton.click()
        except TimeoutException:
            self.logger.error('Loading RDS took too much time!')
            proceed = False
        self.assertTrue(proceed)
        
        try:
            self.logger.info('Waiting for rds frame')
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
            self.logger.info('RDS iframe loaded')
        except:
            self.logger.error('RDS iframe not loaded')
            proceed = False
        self.assertTrue(proceed)

        time.sleep(3)
        # Getting started button
        try:
            driver.find_element(by=By.XPATH, value='/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span')
            needsToConnect = True
        except:
            self.logger.info('Sciebo is already connected')
            needsToConnect = False
            pass

        if needsToConnect:
            try:
                self.logger.info('Try to find getting started button...')
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span'))).click()            
                self.logger.info('Getting started button visible!')
            except TimeoutException:
                self.logger.info('Unable to find getting started button!')

            # Loop through until we find a new window handle
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break        

            self.logger.info('Switched to authentication window')
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/input'))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="submit-wrapper"]/input'))).click()
            self.logger.info('Access granted')

            self.logger.info('Switch back to original window')
            driver.switch_to.window(original_window)

            try:
                self.logger.info('Waiting for rds frame')
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
                self.logger.info('RDS iframe loaded')
            except:
                self.logger.error('RDS iframe not loaded')
                proceed = False
            self.assertTrue(proceed)

        # Now go for the repository connections
        # Click repositories
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/nav/div[1]/div[2]/div/a[3]/div[2]/div'))).click()

        # Check if we need an OSF connection
        osfConnected = True
        try:
            print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Connect\')]'))
        except:
            self.logger.info('Already connected to OSF')

        try:
            print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Disconnect\')]'))
        except:
            self.logger.info('Connection to OSF needed')
            osfConnected=False

        # Check if we need a Zenodo connection
        # zenodoConnected = True
        # try:
        #     print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Connect\')]'))
        # except:
        #     self.logger.info(f'Already connected to Zenodo")

        # try:
        #     print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Disconnect\')]'))
        # except:
        #     self.logger.info(f'Connection to Zenodo needed")
        #     zenodoConnected=False

        print(f'Window handle before connecting: {driver.current_window_handle}')

        if not osfConnected:
            # Connect button for OSF
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()            

            # Loop through until we find a new window handle
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break

            time.sleep(3)

            wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(osfuser)
            wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(osfpwd + Keys.ENTER)

            # Allow connection
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="allow"]/span'))).click()
            print('Done connecting to OSF')

            self.logger.info('Switch back to main window and make sure that the RDS frame is active')
            driver.switch_to.window(driver.window_handles[-1])
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
            self.logger.info('RDS iframe active')
            time.sleep(3)

        # if not zenodoConnected:
        #     # Connect button for Zenodo
        #     WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()
                                                                                   
        #     # Loop through until we find a new window handle
        #     for window_handle in driver.window_handles:
        #         if window_handle != original_window:
        #             driver.switch_to.window(window_handle)
        #             break

        #     time.sleep(3)
        #     wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(zenodouser)
        #     wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(zenodopwd + Keys.ENTER)

        #     # Allow connection
        #     WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-success'))).click()

        self.logger.info('Done...')
        self.assertTrue(proceed)
        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
