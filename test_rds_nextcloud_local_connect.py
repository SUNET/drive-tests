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
from webdriver_manager.chrome import ChromeDriverManager
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

class TestRdsNextcloudLocal(unittest.TestCase):
    def test_rds_nextcloud_local_authorization(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget(g_testtarget)
        loginurl = g_rdslocal_nextcloud_url
        print("Login url: ", loginurl)
        sciebouserenv = "RDSLOCAL_NEXTCLOUD_USER"
        sciebouser = os.environ.get(sciebouserenv)
        sciebopwdenv = "RDSLOCAL_NEXTCLOUD_USER_PASSWORD"
        nodepwd = os.environ.get(sciebopwdenv)

        osfuserenv = "OSF_TEST_USER"
        osfuser = os.environ.get(osfuserenv)
        osfpwdenv = "OSF_TEST_USER_PASSWORD"
        osfpwd = os.environ.get(osfpwdenv)

        zenodouserenv = "ZENODO_TEST_USER"
        zenodouser = os.environ.get(zenodouserenv)
        zenodopwdenv = "ZENODO_TEST_USER_PASSWORD"
        zenodopwd = os.environ.get(zenodopwdenv)

        osfButtonIndex = '2'
        zenodoButtonIndex = '1'

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("--disable-web-security")
        chromeOptions.add_argument("--allow-running-insecure-content")
        chromeOptions.add_argument("--ignore-ssl-errors=yes")
        chromeOptions.add_argument("--ignore-certificate-errors")
        chromeOptions.add_argument("--allow-insecure-localhost")



        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chromeOptions)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(loginurl)

        # Store the ID of the original window
        original_window = driver.current_window_handle
        print(f'Window handle: {original_window}')

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
        # Getting started button
        try:
            driver.find_element(by=By.XPATH, value='/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span')
            needsToConnect = True
        except:
            print("Sciebo is already connected")
            needsToConnect = False

        if needsToConnect:
            try:
                print("Try to find getting started button...")
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span'))).click()            
                print("Getting started button visible!")
            except TimeoutException:
                print("Unable to find getting started button!")

            # Loop through until we find a new window handle
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break        

            print("Switched to authentication window")
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]/input'))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="submit-wrapper"]/input'))).click()
            print("Access granted")

            print("Switch back to original window")
            driver.switch_to.window(original_window)

            try:
                print("Waiting for rds frame")
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
                print("RDS iframe loaded")
            except:
                print("RDS iframe not loaded")

        # Now go for the repository connections
        # Click repositories
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/nav/div[1]/div[2]/div/a[3]/div[2]/div'))).click()

        # Check if we need an OSF connection
        osfConnected = True
        try:
            print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Connect\')]'))
        except:
            print("Already connected to OSF")

        try:
            print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{osfButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Disconnect\')]'))
        except:
            print("Connection to OSF needed")
            osfConnected=False

        # Check if we need a Zenodo connection
        # zenodoConnected = True
        # try:
        #     print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Connect\')]'))
        # except:
        #     print("Already connected to Zenodo")

        # try:
        #     print(driver.find_element(by=By.XPATH, value=f'//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[{zenodoButtonIndex}]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Disconnect\')]'))
        # except:
        #     print("Connection to Zenodo needed")
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
            print(f'Done connecting to OSF')

            print("Switch back to main window and make sure that the RDS frame is active")
            driver.switch_to.window(driver.window_handles[-1])
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
            print("RDS iframe active")
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

        print("Done...")
        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
