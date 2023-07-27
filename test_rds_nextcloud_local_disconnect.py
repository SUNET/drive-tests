""" Selenium tests for Sciebo
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to the Sciebo test node, performing various operations to ensure basic operation
"""
import xmlrunner
import unittest
import sunetdrive
from webdav3.client import Client

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import os
import time

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('DriveTestTarget')
g_rdslocal_nextcloud_url = 'https://test-nextcloud.localdomain.test/'

debugSleep = 3

class TestSciebo(unittest.TestCase):
    def test_sciebo_rds_disconnect(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget(g_testtarget)
        loginurl = g_rdslocal_nextcloud_url
        print("Login url: ", loginurl)
        sciebouserenv = "RDSLOCAL_NEXTCLOUD_USER"
        sciebouser = os.environ.get(sciebouserenv)
        sciebopwdenv = "RDSLOCAL_NEXTCLOUD_USER_PASSWORD"
        nodepwd = os.environ.get(sciebopwdenv)

        osfButtonIndex = '2'
        zenodoButtonIndex = '1'

        # We test locally, so we need to disable some of the certificate checks
        Options()
        chromeOptions.add_argument("--disable-web-security")
        chromeOptions.add_argument("--allow-running-insecure-content")
        chromeOptions.add_argument("--ignore-ssl-errors=yes")
        chromeOptions.add_argument("--ignore-certificate-errors")
        chromeOptions.add_argument("--allow-insecure-localhost")

        driver = webdriver.Chrome(options=chromeOptions)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(loginurl)

        # Store the ID of the original window
        original_window = driver.current_window_handle

        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(sciebouser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            print("Page is ready!")
            proceed = True
        except TimeoutException:
            print("Loading took too much time!")
            proceed = False

        self.assertTrue(proceed)

        try:
            # rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/rds/' +'"]')
            rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/apps/rds/' +'"]')
            rdsAppButton.click()
            proceed = True
        except TimeoutException:
            print("Loading RDS took too much time!")
            proceed = False
        
        try:
            print("Waiting for rds frame")
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
            print("RDS iframe loaded")
        except:
            print("RDS iframe not loaded")

        time.sleep(3)

        try:
            driver.find_element(by=By.XPATH, value='//*[@id="v-navigation-drawer"]/div[1]/div[4]/div/div/div[2]/div')
            isConnected = True
        except:
            print("Settings button not found")
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
                print("Not connected to OSF")

            # Check if we need a Zenodo connection
            zenodoConnected = True
            try:
                print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Disconnect\')]'))
            except:
                zenodoConnected = False
                print("Not connected to Zenodo")

            if osfConnected:
                print("Disconnect from OSF")
                # Connect button for OSF
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()
            
            if zenodoConnected:
                print("Disconnect from Zenodo")
                # Connect button for OSF
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()            

            # Click on settings button
            print("Click on settings button")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="v-navigation-drawer"]/div[1]/div[4]/div/div/div[2]/div'))).click()            

            print("Click remove account")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[2]/div/div/div[2]/button/span/span'))).click()            
                
            print("Check box")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[1]/main/div/div/div/div/div/div[1]/div/div/div[1]/div/div'))).click()            

            print("Click delete RDS account")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[1]/main/div/div/div/div/div/div[2]/button/span/span'))).click()            
        
        print("Done...")
        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
