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

class TestSciebo(unittest.TestCase):
    def test_sciebo_rds_authorization(self):
        delay = 30 # seconds
        sunetnextcloud.TestTarget(g_testtarget)
        loginurl = g_sciebourl
        print("Login url: ", loginurl)
        sciebouserenv = "SCIEBO_USER"
        sciebouser = os.environ.get(sciebouserenv)
        sciebopwdenv = "SCIEBO_USER_PASSWORD"
        nodepwd = os.environ.get(sciebopwdenv)

        osfuserenv = "OSF_TEST_USER"
        osfuser = os.environ.get(osfuserenv)
        osfpwdenv = "OSF_TEST_USER_PASSWORD"
        osfpwd = os.environ.get(osfpwdenv)

        zenodouserenv = "ZENODO_TEST_USER"
        zenodouser = os.environ.get(zenodouserenv)
        zenodopwdenv = "ZENODO_TEST_USER_PASSWORD"
        zenodopwd = os.environ.get(zenodopwdenv)

        skipZenodoConnection = True

        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except Exception as error:
            self.logger.error(f'Error initializing Chrome driver: {error}')
            self.assertTrue(False)
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
        except Exception as error:
            print(f"RDS iframe not loaded: {error}")

        time.sleep(3)
        # Getting started button
        try:
            driver.find_element(by=By.XPATH, value='/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span')
            needsToConnect = True
        except Exception as error:
            print(f"Sciebo is already connected: {error}")
            needsToConnect = False

        if needsToConnect:
            try:
                print("Try to find getting started button...")
                WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/div/div[1]/div/button/span/span'))).click()            
                print("Getting started button visible!")
            except TimeoutException:
                print("Unable to find getting started button!")

            # Loop through until we find a new window handle
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break        

            print("Switched to authentication window")
            wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(sciebouser)
            wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

            # Click authorize
            WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="body-login"]/div[1]/div/span/form/button'))).click()            
            time.sleep(3)

            print("Switch back to original window")
            driver.switch_to.window(original_window)

            try:
                print("Waiting for rds frame")
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
                print("RDS iframe loaded")
            except Exception as error:
                print(f"RDS iframe not loaded: {error}")

        # Now go for the repository connections
        # Click repositories
        WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/nav/div[1]/div[2]/div/a[3]/div[2]/div'))).click()

        try:
            buttons = driver.find_elements(By.XPATH, "//button")
            for button in buttons:
                if button.text == 'CONNECT':
                    print("Connecting...")
                    button.click()

                    # Loop through until we find a new window handle
                    for window_handle in driver.window_handles:
                        if window_handle != original_window:
                            driver.switch_to.window(window_handle)
                            break

                    isZenodo = False
                    isOsf = False

                    try:
                        driver.find_element(By.ID, value='username')
                        isOsf = True
                    except Exception:
                        isZenodo = True

                    if isZenodo:
                        print("Connect to Zenodo")
                        if skipZenodoConnection:
                            driver.close()
                        else:
                            wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(zenodouser)
                            wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(zenodopwd + Keys.ENTER)
                            # Allow connection
                            WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-success'))).click()


                        print("Switch back to main window and make sure that the RDS frame is active")
                        driver.switch_to.window(driver.window_handles[-1])
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
                        print("RDS iframe active")
                        time.sleep(3)


                    if isOsf:
                        print("Connect to OSF")
                        wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(osfuser)
                        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(osfpwd + Keys.ENTER)

                        # Allow connection
                        WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="allow"]/span'))).click()
                        print('Done connecting to OSF')

                        print("Switch back to main window and make sure that the RDS frame is active")
                        driver.switch_to.window(driver.window_handles[-1])
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
                        print("RDS iframe active")
                        time.sleep(3)
                    
        except Exception as error:
            print(f"Error trying to connect to one of the repositories: {error}")

        print("All connections established")
        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
