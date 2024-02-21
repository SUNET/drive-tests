""" Selenium tests for Sciebo
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to the Sciebo test node, performing various operations to ensure basic operation
"""
import xmlrunner
import unittest
import sunetnextcloud
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
g_testtarget = os.environ.get('NextcloudTestTarget')
g_sciebourl = 'https://sns-testing.sciebo.de'
g_driverTimeout = 30

class TestSciebo(unittest.TestCase):
    def test_sciebo_rds_delete_projects(self):
        drv = sunetnextcloud.TestTarget(g_testtarget)
        loginurl = g_sciebourl
        print("Login url: ", loginurl)
        sciebouserenv = "SCIEBO_USER"
        sciebouser = os.environ.get(sciebouserenv)
        sciebopwdenv = "SCIEBO_USER_PASSWORD"
        nodepwd = os.environ.get(sciebopwdenv)
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except:
            self.logger.error(f'Error initializing Chrome driver')
            self.assertTrue(False)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(loginurl)

        wait = WebDriverWait(driver, g_driverTimeout)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(sciebouser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

        try:
            myElem = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'All files')))
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

        # Projects
        print("Select projects from menu")
        WebDriverWait(driver, g_driverTimeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/nav/div[1]/div[2]/div/a[2]/div[2]/div[contains(text(),\'Projects\')]'))).click()

        time.sleep(3)

        deleteProjects = True
        while deleteProjects == True:
            try:
                projectElement = driver.find_element(by=By.CLASS_NAME, value='my-1')
                projectElement.click()

                deleteButton = driver.find_element(by=By.XPATH, value='/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button/span')  
                deleteButton.click()
                print("Deleting existing entries")
                time.sleep(1)
            except:
                print("No more entries to delete, continue")
                deleteProjects = False

        print("Done...")
        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
