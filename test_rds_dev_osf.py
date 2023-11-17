""" Selenium tests for RDS Development Environment
Author: Richard Freitag <freitag@sunet.se>
Selenium test to publish data through the OSF connector
"""
import xmlrunner
import unittest
# import sunetdrive
import logging
from webdav3.client import Client

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
from datetime import datetime

# Set usernames and passwords in environment variables
g_rds_dev_url               = os.environ.get('RDS_DEV_URL')
g_rds_dev_user              = os.environ.get('RDS_DEV_USER')
g_rds_dev_password          = os.environ.get('RDS_DEV_USER_PASSWORD')
g_rds_dev_app_password      = os.environ.get('RDS_DEV_USER_APP_PASSWORD')

g_rds_dev_sso_user          = os.environ.get('RDS_DEV_SSO_USER')
g_rds_dev_sso_password      = os.environ.get('RDS_DEV_SSO_USER_PASSWORD')
g_rds_dev_sso_app_password  = os.environ.get('RDS_DEV_SSO_USER_APP_PASSWORD')
g_driverTimeout = 30

class TestRdsNextcloudLocal(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_rds_nextcloud_local_login(self):
        chromeOptions = Options()

        driver = webdriver.Chrome(options=chromeOptions)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(g_rds_dev_url)

        wait = WebDriverWait(driver, g_driverTimeout)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(g_rds_dev_user)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(g_rds_dev_password + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'Page is ready!')
            proceed = True
        except TimeoutException:
            self.logger.info(f'Loading took too much time!')
            proceed = False

        self.assertTrue(proceed)

    def test_rds_nextcloud_local_project(self):
        chromeOptions = Options()

        driver = webdriver.Chrome(options=chromeOptions)
        driver.maximize_window()
        # driver2 = webdriver.Firefox()
        driver.get(g_rds_dev_url)

        wait = WebDriverWait(driver, g_driverTimeout)
        wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(g_rds_dev_user)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(g_rds_dev_password + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info(f'Page is ready!')
            proceed = True
        except TimeoutException:
            self.logger.info(f'Loading took too much time!')
            proceed = False

        self.assertTrue(proceed)

        try:
            # rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/rds/' +'"]')
            rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/apps/rds/' +'"]')
            rdsAppButton.click()
            proceed = True
        except TimeoutException:
            self.logger.info(f'Loading RDS took too much time!')
            proceed = False

       
        try:
            self.logger.info(f'Waiting for rds frame')
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
            self.logger.info(f'RDS iframe loaded')
        except:
            self.logger.info(f'RDS iframe not loaded')

        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, ''))).click()

        # Projects
        # print(driver.find_element(by=By.XPATH, value='//*[@id="inspire"]/div/main/div/div/main/div/div/div[2]/div[2]/div[2]/div/div[2]/div/button/span/span[contains(text(),\'Connect\')]'))
        # /html/body/div/div/div/nav/div[1]/div[2]/div/a[2]/div[2]/div[contains(text(),\'Projects\')]
        self.logger.info(f'Select projects from menu')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/nav/div[1]/div[2]/div/a[2]/div[2]/div[contains(text(),\'Projects\')]'))).click()

        # New project
        # /html/body/div/div/div/main/div/div/main/div/div/div/div[1]/div[3]/button/span
        self.logger.info(f'New project')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[1]/div[3]/button/span'))).click()

        # Pick folder
        # /html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[2]/button/span
        self.logger.info(f'Click on pick folder')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[2]/button/span'))).click()

        # Folder RDSTest
        # /html/body/div[5]/div[1]/ul/li[2]/div/span[1][contains(text(),\'RDSTest\')]
        
        time.sleep(3)

        # Span class is called 'filename'

        # folderPickerFrame = driver.find_element(By.XPATH, '//iframe[1]')
        # driver.switch_to.frame(folderPickerFrame)

        # We need to switch to the parent frame to use RDS here
        self.logger.info(f'Switch to parent frame')
        driver.switch_to.parent_frame() 
        self.logger.info(f'Wait for folder RDSTest to be visible')
        WebDriverWait(driver, 20).until(EC.text_to_be_present_in_element((By.CLASS_NAME, "oc-dialog-title"), "Choose source folder"))
        self.logger.info(f'Visible!')

        
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/div/table/tbody/tr[3]/td[1]')))
        # wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div[1]/ul/li[2]/div/span[1]')))
        self.logger.info(f'Select folder RDSTest')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div/table/tbody/tr[3]/td[1]'))).click()
        self.logger.info(f'Choose folder')

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="body-user"]/div[1]/div[2]/button'))).click()

        self.logger.info(f'Switch back to RDS frame')
        try:
            self.logger.info(f'Waiting for rds frame')
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
            self.logger.info(f'RDS iframe loaded')
        except:
            self.logger.info(f'RDS iframe not loaded')

        # Input field always has a random ID
        # //*[@id="input-101"]
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, ''))).click()
        self.logger.info(f'Input project name')

        # projectInput = driver.find_element(By.XPATH, "//*[contains(@id, 'input-')]")
        # print(projectInput)
        # self.logger.info(f'Here...")

        tsProject = "Sunet Drive Test Project - " + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-')]"))).send_keys(tsProject)

        # OSF repository
        self.logger.info(f'Select OSF to publish')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[4]/div/div/div[2]/div[3]/div/div/div/div[3]'))).click()

        # Continue button
        self.logger.info(f'Continue')
        # /html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/div/button/span
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/div/button/span'))).click()

        self.logger.info(f'Switch back to Describo frame')
        try:
            self.logger.info(f'Waiting for describo frame')
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "describoWindow")))
            self.logger.info(f'Describo iframe loaded')
        except:
            self.logger.info(f'Describo iframe not loaded')
        time.sleep(3)

        # OSF Settings
        self.logger.info(f'Wait for OSF Settings and click')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"tab-OSF settings\"]/span"))).click()
        time.sleep(1)

        # Check if we have to delete entries:
        checkForOsfEntries = True
        while checkForOsfEntries == True:
            try:
                deleteButton = driver.find_element(by=By.CLASS_NAME, value='el-button--danger')
                deleteButton.click()
                self.logger.info(f'Deleting existing entries')
                time.sleep(1)
            except:
                self.logger.info(f'No more entries to delete, continue')
                checkForOsfEntries = False

        # OSF Text
        # /html/body/div[1]/div/div/div[2]/div[2]/div[2]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span
        self.logger.info(f'Click on +Text')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pane-OSF settings"]/div/div[1]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span'))).click()

        # OSF Add Text, again random number ID
        self.logger.info(f'Add OSF Title')
        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'el-id-')]"))).send_keys("OSF Title")

        tsTitle = "RDS Sunet Drive Title - " + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Add text']"))).send_keys(tsTitle + Keys.ENTER)
        # //*[@id="el-id-4106-2"]
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="el-id-2110-7"]'))).click()

        time.sleep(3)

        self.logger.info(f'Click on +Select for Osfcategory')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[2]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span"))).click()
                                                                               
        self.logger.info(f'Click on category dropdown menu')
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Select']"))).click()
        time.sleep(1)
        
        self.logger.info(f'Click on third entry in category list')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@id, 'el-popper-container-')]/div/div/div/div[1]/ul/li[3]"))).click()
        time.sleep(1)
 
        # self.logger.info(f'Select data category")
        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"el-popper-container-254\"]/div/div/div/div[1]/ul/li[3]"))).click()
        # time.sleep(1)

        self.logger.info(f'Click on +TextArea for OSF Description')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[3]/div/div[2]/div[1]/div[1]/div/div[1]/div/button"))).click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'el-textarea__inner'))).send_keys("OSF Project Description")

        self.logger.info(f'Switch to parent frame')
        driver.switch_to.parent_frame() 

        self.logger.info(f'Click on continue button')
        # /html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button[2]/span
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button[2]/span'))).click()

        self.logger.info(f'Click on publish button')
        # /html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button[2]/span
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button[2]/span'))).click()


        try:
            self.logger.info(f'Waiting for publication notification')
            WebDriverWait(driver, 60).until(EC.text_to_be_present_in_element((By.CLASS_NAME, "v-snack__content"), "successfully published"))
            self.logger.info(f'Looks like the data has been published! Well done!')
        except:
            self.logger.info(f'Timeout while waiting for publication')

        self.logger.info(f'Done...')
        time.sleep(3)

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
