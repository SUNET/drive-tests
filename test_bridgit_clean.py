""" Clean BridgIT project
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to clean all BridgIT data
"""
import xmlrunner
import HtmlTestRunner
import unittest
import sunetnextcloud
from webdav3.client import Client

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging

drv = sunetnextcloud.TestTarget()

class TestBridgitClean(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def deleteCookies(self, driver):
        cookies = driver.get_cookies()
        self.logger.info(f'Deleting all cookies: {cookies}')
        driver.delete_all_cookies()
        cookies = driver.get_cookies()
        self.logger.info(f'Cookies deleted: {cookies}')

    def test_logger(self):
        self.logger.info('self.logger.info test_logger')
        pass
    
    def test_Bridgit_delete_projects(self):
        delay = 30 # seconds
        logger = self.logger
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                loginurl = drv.get_node_login_url(fullnode)
                logger.info(f'URL: {loginurl}')
                nodeuser = drv.get_seleniumuser(fullnode)
                logger.info(f'Username: {nodeuser}')
                nodepwd = drv.get_seleniumuserpassword(fullnode)

                try:
                    options = Options()
                    driver = webdriver.Chrome(options=options)
                except Exception as error:
                    logger.error(f'Error initializing Chrome driver: {error}')
                    self.assertTrue(False)
                driver.set_window_size(1920, 1152)
                # driver2 = webdriver.Firefox()
                driver.get(loginurl)
                # Store the ID of the original window for authorization window
                original_window = driver.current_window_handle

                wait = WebDriverWait(driver, delay)
                wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
                wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    logger.info('App menu is ready!')
                except TimeoutException:
                    logger.info('Loading of app menu took too much time!')

                bridgit = driver.find_element(By.XPATH, '//a[@href="'+ '/apps/rdsng/' +'"]')
                bridgit.click()

                try:
                    logger.info('Waiting for BridgIT iframe')
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'app-frame')))
                    logger.info('BridgIT iframe loaded')
                    proceed = True
                except Exception as error:
                    logger.error(f'BridgIT iframe not loaded: {error}')
                    proceed = False
                self.assertTrue(proceed)

                time.sleep(3)

                logger.info(f'Find and delete all projects')
                # wait for projects-listbox
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'projects-listbox')))
                time.sleep(3)

                logger.info(f'Find options button for project')
                action = ActionChains(driver)
                buttons = driver.find_elements(By.CLASS_NAME, 'p-button')

                buttons = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'Options')]")
                logger.info(f'Found {len(buttons)} projects')
                while len(buttons) > 0:
                    button = buttons[0]
                    action.click(on_element=button).perform()
                    time.sleep(.2)
                    driver.find_element(By.XPATH, "//*[contains(text(), 'Delete project')]").click()
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-button-danger')))
                    driver.find_element(By.CLASS_NAME, 'p-button-danger').click()

                    # Wait for deleted toast message
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'p-toast-message')))
                    message = driver.find_element(By.CLASS_NAME, 'p-toast-message')
                    logger.info(f'Message: {message.text}')
                    if 'has been deleted' in message.text:
                        logger.info(f'Project successfully deleted')
                    else:
                        logger.error(f'Delete project failed: {message.text}')

                    buttons = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'Options')]")

                logger.info('Done...')
                time.sleep(2)

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"bridgit-{drv.expectedResults[drv.target]['status']['version']}-acceptance", add_timestamp=False))
