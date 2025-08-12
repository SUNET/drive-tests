""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to test Collabora on a local node
"""
from datetime import datetime
import xmlrunner
import unittest
import sunetnextcloud

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os
import time
import logging
import yaml
import pyotp

# 'prod' for production environment, 'test' for test environment
g_testtarget = os.environ.get('NextcloudTestTarget')
g_rdsnodes = ["sunet","su"]
expectedResultsFile = 'expected.yaml'

class TestRDSSelenium(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    with open(expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        self.logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        self.logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_rds_app(self):
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget(g_testtarget)

        for rdsnode in g_rdsnodes:
            with self.subTest(mynode=rdsnode):
                loginurl = drv.get_node_login_url(rdsnode)
                self.logger.info("Login url: ", loginurl)
                nodeuser = drv.get_seleniumuser(rdsnode)
                nodepwd = drv.get_seleniumuserpassword(rdsnode)
                
                try:
                    options = Options()
                    driver = webdriver.Chrome(options=options)
                except Exception as error:
                    self.logger.error(f'Error initializing Chrome driver: {error}')
                    self.assertTrue(False)
                driver.maximize_window()
                # driver2 = webdriver.Firefox()
                driver.get(loginurl)

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    self.logger.info("Page is ready!")
                    proceed = True
                except TimeoutException:
                    self.logger.info("Loading took too much time!")
                    proceed = False

                self.assertTrue(proceed)

                try:
                    rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/rds/' +'"]')
                    rdsAppButton.click()
                    proceed = True
                except TimeoutException:
                    self.logger.info("Loading RDS took too much time!")
                    proceed = False

                self.assertTrue(proceed)

                self.logger.info('End of test!')
                time.sleep(5)

    def test_rds_su_saml(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        delay = 30 # seconds
        drv = sunetnextcloud.TestTarget()
        nodeName = 'su'
        if len(drv.allnodes) == 1:
            if drv.allnodes[0] != nodeName:
                self.logger.info(f'Only testing {drv.allnodes[0]}, not testing su saml')
                return

        loginurl = drv.get_gss_url()
        self.logger.info(f'URL: {loginurl}')
        samluser=drv.get_samlusername(nodeName)
        self.logger.info(f'Username: {samluser}')
        samlpassword=drv.get_samluserpassword(nodeName)
        
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
        except Exception as error:
            self.logger.error(f'Error initializing Chrome driver: {error}')
            self.assertTrue(False)
        # driver2 = webdriver.Firefox()
        self.deleteCookies(driver)
        driver.maximize_window()        
        driver.get(loginurl)

        wait = WebDriverWait(driver, delay)

        loginLinkText = 'ACCESS THROUGH YOUR INSTITUTION'

        wait.until(EC.presence_of_element_located((By.LINK_TEXT, loginLinkText))).click()
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'dsclient')))
        driver.implicitly_wait(10)
        
        wait.until(EC.presence_of_element_located((By.ID, 'searchinput'))).send_keys("su.se", Keys.RETURN)
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'label-url'))).click()
        driver.implicitly_wait(10)

        wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(samluser)
        wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(samlpassword + Keys.ENTER)
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-form-button'))).click()

        # Wait for TOTP screen
        requireTotp = False
        try:
            self.logger.info('Check if TOTP selection dialogue is visible')
            totpselect = driver.find_element(By.XPATH, '//a[@href="' + drv.indexsuffix + '/login/challenge/totp?redirect_url=' + drv.indexsuffix + '/apps/dashboard/' +'"]')
            self.logger.warning('Found TOTP selection dialogue')
            requireTotp = True
            totpselect.click()
        except Exception as error:
            self.logger.info(f'No need to select TOTP provider: {error}')

        if requireTotp:
            nodetotpsecret = drv.get_samlusertotpsecret(nodeName)
            totp = pyotp.TOTP(nodetotpsecret)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="body-login"]/div[1]/div/main/div/form/input'))).send_keys(totp.now() + Keys.ENTER)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            self.logger.info('App menu is ready!')
        except TimeoutException:
            self.logger.info('Loading of app menu took too much time!')

        driver.implicitly_wait(10) # seconds before quitting
        dashboardUrl = drv.get_dashboard_url('su')
        currentUrl = driver.current_url
        try:
            self.assertEqual(dashboardUrl, currentUrl)
        except Exception as error:       
            self.assertEqual(dashboardUrl + '#/', currentUrl)
            self.logger.warning(f'Dashboard URL contains trailing #, likely due to the tasks app: {error}')
        self.logger.info(f'{driver.current_url}')

        try:
            rdsAppButton = driver.find_element(by=By.XPATH, value='//a[@href="'+ '/index.php/apps/rds/' +'"]')
            rdsAppButton.click()
            proceed = True
        except TimeoutException:
            self.logger.error("Loading RDS took too much time!")
            proceed = False

        try:
            self.logger.info("Waiting for rds frame")
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
            self.logger.info("RDS iframe loaded")
        except Exception as error:
            self.logger.error(f"RDS iframe not loaded: {error}")
            proceed = False

        try:
            self.logger.info('Looking for active projects')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Active Projects')]"))).click()
        except Exception as error:
            self.logger.error(f'Active Projects element not found: {error}')
            proceed = False

        try:
            self.logger.info('Create new project')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'new project')]"))).click()
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:
            self.logger.error(f'New Project element not found: {error}')
            proceed = False

        try:
            self.logger.info('Input project name')
            # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Choose')]"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'input-')]" ))).send_keys('TestProject')
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:
            self.logger.error(f'Could not set project name: {error}')
            proceed = False

        try:
            self.logger.info('Pick folder')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Pick')]"))).click()
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:
            self.logger.error(f'Pick folder not found')
            proceed = False

        # We need to switch to the parent frame to use RDS here
        self.logger.info('Switch to parent frame: {error}')
        driver.switch_to.parent_frame() 

        try:
            self.logger.info('Choose source folder?')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Choose source folder')]")))
            self.logger.error('Choose source folder!')
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:        
            self.logger.error(f'Choose source folder error: {error}')
            proceed = False

        try:
            self.logger.info('Set sort order to newest first?')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Modified')]"))).click()
            self.logger.info('Set sort order to newest first!')
            # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Modified')]"))).click()
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:        
            self.logger.error(f'Could not change sort order: {error}')
            proceed = False

        try:
            self.logger.info('Select folder RDSDemo')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'RDSDemo')]"))).click()
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:        
            self.logger.error(f'RDSDemo folder not found: {error}')
            proceed = False

        try:
            self.logger.info('Click on Choose')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), ' Choose')]"))).click()
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:
            self.logger.error(f'RDSDemo folder not found: {error}')
            proceed = False

        try:
            self.logger.info("Switch back to rds iframe")
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "rds-editor")))
        except Exception as error:
            self.logger.error(f"RDS iframe not loaded: {error}")
            proceed = False

        try:
            self.logger.info('Select OSF Connector')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Open Science Framework')]"))).click()
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:        
            self.logger.error(f'OSF Connector not found: {error}')
            proceed = False

        time.sleep(3)

        try:
            self.logger.info('Continue (to describo)')
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Continue')]"))).click()
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.v-btn"))).click()
        except Exception as error:
            self.logger.error(f'Continue button not found: {error}')
            proceed = False

        time.sleep(3)

        self.logger.info("Switch to Describo frame")
        try:
            self.logger.info("Waiting for describo frame")
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "describoWindow")))
            self.logger.info("Describo iframe loaded")
        except Exception as error:
            self.logger.info(f"Describo iframe not loaded: {error}")
            proceed = False
        time.sleep(3)

        # OSF Settings
        self.logger.info("Wait for OSF Settings and click")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"tab-OSF settings\"]/span"))).click()
        time.sleep(1)

        # Check if we have to delete entries:
        checkForOsfEntries = True
        while checkForOsfEntries:
            try:
                deleteButton = driver.find_element(by=By.CLASS_NAME, value='el-button--danger')
                deleteButton.click()
                self.logger.info("Deleting existing entries")
                time.sleep(1)
            except Exception as error:
                self.logger.info(f"No more entries to delete, continue: {error}")
                checkForOsfEntries = False

        try:
            # OSF Text
            self.logger.info("Click on +Text")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pane-OSF settings"]/div/div[1]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span'))).click()

            # OSF Add Text, again random number ID
            self.logger.info("Add OSF Title")
            tsTitle = "RDS Sunet Drive Title - " + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Add text']"))).send_keys(tsTitle + Keys.ENTER)
            time.sleep(3)

            self.logger.info("Click on +Select for Osfcategory")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[2]/div/div[2]/div[1]/div[1]/div/div[1]/div/button/span"))).click()
            self.logger.info("Click on category dropdown menu")
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Select']"))).click()
            time.sleep(1)
            
            self.logger.info("Click on third entry in category list")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@id, 'el-popper-container-')]/div/div/div/div[1]/ul/li[3]"))).click()
            time.sleep(1)
    
            # self.logger.info(f"Select data category")
            # wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"el-popper-container-254\"]/div/div/div/div[1]/ul/li[3]"))).click()
            # time.sleep(1)

            self.logger.info("Click on +TextArea for OSF Description")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"pane-OSF settings\"]/div/div[3]/div/div[2]/div[1]/div[1]/div/div[1]/div/button"))).click()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'el-textarea__inner'))).send_keys("OSF Project Description")
        except Exception as error:
            self.logger.error(f'Error entering OSF metadata {error}')

        self.logger.info("Switch to parent frame")
        driver.switch_to.parent_frame() 

        self.logger.info("Click on continue button")
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Continue')]"))).click()

        self.logger.info("Click on publish button")
        # wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Publish')]"))).click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/main/div/div/main/div/div/div/div[2]/div/div/div/div[3]/div/button[2]/span'))).click()

        try:
            self.logger.info('Wait maximum 60s for success info')
            idElement = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Project created with ID')]")))
            self.logger.info(f'ID element found: {idElement.text}')

            osfUrl = 'https://test.osf.io/' + idElement.text.replace('Project created with ID','').replace(' ','') + '/'
            self.logger.info(f'OSF URL: {osfUrl}')

            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'successfully published')]")))
            self.logger.info('Dataset successfully published!')
        except Exception as error:
            self.logger.info(f'Error publishing dataset {error}')

        try:
            self.logger.info('Try to get DOI string')
            doiElement = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Published project with DOI')]")))
            self.logger.info(f'Project DOI: {doiElement.text.replace('Published project with DOI','').replace(' ','')}')
        except Exception as error:
            self.logger.warning(f'Could not get DOI information: {error}')

        self.assertTrue(proceed)

        self.logger.info('End of test!')

if __name__ == '__main__':
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
