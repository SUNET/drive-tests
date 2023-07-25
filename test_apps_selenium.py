""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test apps in Sunet Drive
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetdrive
import pyautogui

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
g_appnodes_test = ["sunet"]
g_appnodes_prod = ["sunet"]

g_apps_test = ['rds', 'jupyter']
g_apps_prod = []


class TestAppsSelenium(unittest.TestCase):
    def test_rds_app(self):
        delay = 30 # seconds
        drv = sunetdrive.TestTarget(g_testtarget)
        if g_testtarget == 'prod':
            nodestotest = g_appnodes_prod
            appstotest = g_apps_prod
        else:
            nodestotest = g_appnodes_test
            appstotest = g_apps_test

        


        for appnode in nodestotest:
            with self.subTest(mynode=appnode):
                loginurl = drv.get_node_login_url(appnode)
                print("Login url: ", loginurl)
                nodeuser = drv.get_seleniumuser(appnode)
                nodepwd = drv.get_seleniumuserpassword(appnode)
                
                driver = webdriver.Chrome(ChromeDriverManager().install())
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

                for app in appstotest:
                    appurl = '/index.php/apps/' + app + '/'
                    try:
                        rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ appurl +'"]')
                        rdsAppButton.click()
                        print("App {0} loaded".format(app))
                        proceed = True
                    except TimeoutException:
                        print("Loading {0} took too much time!".format(app))
                        proceed = False

                    self.assertTrue(proceed)
                    time.sleep(3)

                print('End of test!')
                time.sleep(5)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
