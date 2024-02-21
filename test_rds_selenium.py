""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test Collabora on a local node
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetnextcloud
import pyautogui

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
g_rdsnodes = ["sunet"]



class TestRDSSelenium(unittest.TestCase):
    def test_rds_app(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget(g_testtarget)

        for rdsnode in g_rdsnodes:
            with self.subTest(mynode=rdsnode):
                loginurl = drv.get_node_login_url(rdsnode)
                print("Login url: ", loginurl)
                nodeuser = drv.get_seleniumuser(rdsnode)
                nodepwd = drv.get_seleniumuserpassword(rdsnode)
                
                try:
                    options = Options()
                    driver = webdriver.Chrome(options=options)
                except:
                    self.logger.error(f'Error initializing Chrome driver')
                    self.assertTrue(False)
                driver.maximize_window()
                actions = ActionChains(driver)
                # driver2 = webdriver.Firefox()
                driver.get(loginurl)

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
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
                    rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/rds/' +'"]')
                    rdsAppButton.click()
                    proceed = True
                except TimeoutException:
                    print("Loading RDS took too much time!")
                    proceed = False

                self.assertTrue(proceed)

                print('End of test!')
                time.sleep(5)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
