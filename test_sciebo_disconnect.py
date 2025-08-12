""" Selenium tests for Sciebo
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to the Sciebo test node, performing various operations to ensure basic operation
"""
import xmlrunner
import unittest
import sunetnextcloud

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('NextcloudTestTarget')
g_sciebourl = 'https://sns-testing.sciebo.de'
g_driverTimeout = 30

debugSleep = 3

class TestSciebo(unittest.TestCase):
    def test_sciebo_rds_disconnect(self):
        delay = g_driverTimeout # seconds
        sunetnextcloud.TestTarget(g_testtarget)
        loginurl = g_sciebourl
        print("Login url: ", loginurl)
        sciebouserenv = "SCIEBO_USER"
        sciebouser = os.environ.get(sciebouserenv)
        sciebopwdenv = "SCIEBO_USER_PASSWORD"
        nodepwd = os.environ.get(sciebopwdenv)

        osfButtonIndex = '1'
        zenodoButtonIndex = '2'
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error('Error initializing Chrome driver')
            self.assertTrue(False)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(loginurl)

        # Store the ID of the original window
        # original_window = driver.current_window_handle

        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(sciebouser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
            print("All files visible!")
        except TimeoutException:
            print("Loading of all files took too much time!")

        burgerButton = driver.find_element(by=By.CLASS_NAME, value='burger')
        burgerButton.click()

        time.sleep(1)

        rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/apps/rds/' +'"]')
        rdsAppButton.click()
        time.sleep(1)
        
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
            WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/nav/div[1]/div[2]/div/a[3]/div[2]/div'))).click()

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
                WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()
            
            if zenodoConnected:
                print("Disconnect from Zenodo")
                # Connect button for OSF
                WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span'))).click()            

            # Click on settings button
            print("Click on settings button")
            WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="v-navigation-drawer"]/div[1]/div[4]/div/div/div[2]/div'))).click()            

            print("Click remove account")
            WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[2]/div/div/div[2]/button/span/span'))).click()            
                
            print("Check box")
            WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[1]/main/div/div/div/div/div/div[1]/div/div/div[1]/div/div'))).click()            

            print("Click delete RDS account")
            WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inspire"]/div[1]/main/div/div/div/div/div/div[2]/button/span/span'))).click()            
        
        print("Done...")
        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
