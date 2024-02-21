""" Selenium tests for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
Selenium tests to log on to a Sunet Drive node, and performing various operations to ensure basic operation of a node
"""
import xmlrunner
import unittest
import sunetnextcloud
from webdav3.client import Client

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import os
import time
import logging

g_testtarget = os.environ.get('DriveTestTarget')
g_loggedInNodes={}
g_logger={}
g_driver={}
g_drv={}
g_wait={}

g_testfolders = ['SeleniumCollaboraTest', 'selenium-system', 'selenium-personal']

def nodelogin(fullnode):
    global g_wait, g_loggedInNodes
    g_logger.info(f'Logging in to {fullnode}')
    loginurl = g_drv.get_node_login_url(fullnode)
    g_logger.info(f'Login url: {loginurl}')
    nodeuser = g_drv.get_seleniumuser(fullnode)
    nodepwd = g_drv.get_seleniumuserpassword(fullnode)
    g_loggedInNodes[fullnode] = True

    g_driver.maximize_window()
    actions = ActionChains(g_driver)
    # driver2 = webdriver.Firefox()
    g_driver.get(loginurl)

    g_wait.until(EC.presence_of_element_located((By.ID, 'user'))).send_keys(nodeuser)
    g_wait.until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)

    return


class TestSearchSelenium(unittest.TestCase):
    global g_driver, g_drv, g_logger, g_wait, g_loggedInNodes
    delay = 30
    g_logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
    
    g_logger.info(f'Logger initialized')

    g_drv = sunetnextcloud.TestTarget(g_testtarget)
    try:
        options = Options()
        # options.add_argument("--headless")
        g_driver = webdriver.Chrome(options=options)
    except:
        g_logger.error(f'Error initializing Chrome driver')
    g_wait = WebDriverWait(g_driver, delay)

    for fullnode in g_drv.fullnodes:
        g_loggedInNodes[fullnode] = False

    def test_logger(self):
        g_logger.info(f'g_logger.info test_logger')
        pass

    def test_folder_search(self):
        global g_isLoggedIn, g_wait, g_loggedInNodes, g_drv, g_logger
        g_logger.info(f'Start test test_folder_search {g_loggedInNodes}')

        for fullnode in g_drv.fullnodes:
            g_logger.info(f'Testing node {fullnode}')
            with self.subTest(mynode=fullnode):
                if g_loggedInNodes.get(fullnode) == False:
                    nodelogin(fullnode)
                self.assertTrue(g_loggedInNodes.get(fullnode))

                loginurl = g_drv.get_node_login_url(fullnode)
                g_logger.info(f'URL: {loginurl}')
                nodeuser = g_drv.get_seleniumuser(fullnode)
                g_logger.info(f'Username: {nodeuser}')
                nodepwd = g_drv.get_seleniumuserpassword(fullnode)

                # Create folder for testing using webdav
                url = g_drv.get_webdav_url(fullnode, nodeuser)
                options = {
                'webdav_hostname': url,
                'webdav_login' : nodeuser,
                'webdav_password' : nodepwd 
                }

                client = Client(options)
                dir = 'SharedFolder'
                g_logger.info(f'Make and check directory: {dir}')
                client.mkdir(dir)
                self.assertEqual(client.list().count('SharedFolder/'), 1)
                g_driver.maximize_window()

                try:
                    g_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
                    g_logger.info(f'App menu is ready!')
                except TimeoutException:
                    g_logger.info(f'Loading of app menu took too much time!')

                # Check URLs after login
                dashboardUrl = g_drv.get_dashboard_url(fullnode)
                currentUrl = g_driver.current_url
                # self.assertEqual(dashboardUrl, currentUrl)                

                files = g_driver.find_element(By.XPATH, '//a[@href="'+ '/index.php/apps/files/' +'"]')
                files.click()

                try:
                    g_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu-entry')))
                    g_logger.info(f'All files visible!')
                except TimeoutException:
                    g_logger.info(f'Loading of all files took too much time!')

                for testfolder in g_testfolders:
                    g_logger.info(f'Testing {testfolder}')

                    try:
                        g_logger.info(f'Click on search button')
                        g_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'unified-search__trigger')))
                        searchbutton = g_driver.find_element(By.CLASS_NAME, 'unified-search__trigger')
                        searchbutton.click()

                        g_logger.info(f'Typing {testfolder} into search bar')
                        g_wait.until(EC.presence_of_element_located((By.ID, 'unified-search__input'))).send_keys(testfolder)

                        # We need to wait for a 'literal' second until the results are in
                        time.sleep(1)

                        dirinfo = g_driver.find_element(By.CLASS_NAME, 'dirinfo')
                        self.assertEqual(dirinfo.text, '1 folder')

                        filter = g_driver.find_element(By.CLASS_NAME, 'filter')
                        self.assertEqual(filter.text, 'matches "{testfolder}"')

                    except:
                        g_logger.warning(f'Search resulted in an error')

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
