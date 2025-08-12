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

debugSleep = 3

class TestRdsDevDisconnect(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info('self.logger.info test_logger')
        pass

    def test_sciebo_rds_disconnect(self):
        self.logger.info(f'Test RDS disconnect for user: {g_rds_dev_user}')
        delay = 30 # seconds

        osfButtonIndex = '2'
        zenodoButtonIndex = '1'

        # We test locally, so we need to disable some of the certificate checks
        chromeOptions = Options()

        driver = webdriver.Chrome(options=chromeOptions)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(g_rds_dev_url)

        # Store the ID of the original window
        original_window = driver.current_window_handle

        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(g_rds_dev_user)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(g_rds_dev_password + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info('Page is ready!')
            proceed = True
        except TimeoutException:
            self.logger.error('Loading took too much time!')
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

        try:
            driver.find_element(by=By.XPATH, value='//*[@id="v-navigation-drawer"]/div[1]/div[4]/div/div/div[2]/div')
            isConnected = True
        except:
            self.logger.info('Settings button not found')
            isConnected = False

        if isConnected:
            # Now go for the repository connections
            # Click repositories
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/nav/div[1]/div[2]/div/a[3]/div[2]/div'))).click()

            # Check if we need an OSF connection
            osfConnected = True
            try:
                print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Disconnect\')]'))
            except:
                osfConnected = False
                self.logger.info('Not connected to OSF')

            # Check if we need a Zenodo connection
            zenodoConnected = True
            try:
                print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Disconnect\')]'))
            except:
                zenodoConnected = False
                self.logger.info('Not connected to Zenodo')

            if osfConnected:
                self.logger.info('Disconnect from OSF')
                # Connect button for OSF
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()
            
            if zenodoConnected:
                self.logger.info('Disconnect from Zenodo')
                # Connect button for OSF
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()            

            # Click on settings button
            self.logger.info('Click on settings button')
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="v-navigation-drawer"]/div[1]/div[4]/div/div/div[2]/div'))).click()            

            self.logger.info('Click remove account')
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[2]/div/div/div[2]/button/span/span'))).click()            
                
            self.logger.info('Check box')
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[1]/main/div/div/div/div/div/div[1]/div/div/div[1]/div/div'))).click()            

            self.logger.info('Click delete RDS account')
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[1]/main/div/div/div/div/div/div[2]/button/span/span'))).click()            
        
        self.logger.info('Done...')
        self.assertTrue(proceed)

        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
