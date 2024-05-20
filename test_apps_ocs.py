import os
import requests
from requests.auth import HTTPBasicAuth
import json
import unittest
import yaml
import sunetnextcloud
import logging
import time
import threading
import xmlrunner

ocsheaders = { "OCS-APIRequest" : "true" } 
expectedResultsFile = 'expected.yaml'
g_testThreadsRunning = 0
testThreadRunning = False
g_testPassed = {}

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

class ConfiguredAppsInstalled(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global testThreadRunning, logger, g_testPassed, g_testThreadsRunning
        g_testThreadsRunning += 1
        logger.info(f'ConfiguredAppsInstalled thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        session = requests.Session()
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = drv.get_all_apps_url(fullnode)

        logger.info(f'{url}')
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserpassword(fullnode)

        r=session.get(url, headers=ocsheaders)
        nodeApps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            nodeApps = j["ocs"]["data"]["apps"]
        except:
            logger.warning(f'No JSON reply received on node {fullnode}')
            # self.logger.warning(r.text)
            g_testThreadsRunning -= 1
            return

        logger.info(f'Check if all apps configured in {expectedResultsFile} are installed on {fullnode}')

        for expectedApp in expectedResults['apps']:
            logger.info(f'Check if {expectedApp} is installed on {fullnode}')
            print()
            try:
                pos = nodeApps.index(expectedApp)
                logger.info(f'Found app at {pos}')
                g_testPassed[fullnode] = True
            except:
                logger.warning(f'App {expectedApp} NOT found on {fullnode}')
                g_testThreadsRunning -= 1
                return

        logger.info(f'ConfiguredAppsInstalled thread done for node {self.name}')
        g_testThreadsRunning -= 1

class InstalledAppsConfigured(threading.Thread):
    def __init__(self, name, app='all', checkEnabled=False):
        threading.Thread.__init__(self)
        self.name = name
        self.app = app
        self.checkEnabled = checkEnabled

    def run(self):
        global testThreadRunning, logger, g_testPassed, g_testThreadsRunning
        g_testThreadsRunning += 1
        logger.info(f'InstalledAppsConfigured thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False

        session = requests.Session()
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = drv.get_all_apps_url(fullnode)

        logger.info(f'{url}')
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        r=session.get(url, headers=ocsheaders)
        nodeApps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            nodeApps = j["ocs"]["data"]["apps"]
        except:
            logger.warning(f'No JSON reply received on {fullnode}')
            # self.logger.warning(r.text)
            g_testThreadsRunning -= 1
            return

        if self.app == 'all':
            logger.info(f'Check if all installed apps on {fullnode} are found in {expectedResultsFile}')
            for nodeApp in nodeApps:
                try:
                    appInfo = expectedResults['apps'][nodeApp]
                    g_testPassed[fullnode] = True
                except:
                    logger.warning(f'{nodeApp} NOT found on {fullnode}')
                    g_testThreadsRunning -= 1
                    return
                
        else: # Check if specific app is installed/active
            try:
                installed = self.app in nodeApps
                logger.info(f'App {self.app} is installed: {installed} on {fullnode}')
                g_testPassed[fullnode] = self.app in nodeApps
            except:
                logger.error(f'{self.app} NOT found on {fullnode}')
                logger.info(f'Apps found are: {nodeApps}')
                g_testThreadsRunning -= 1
                return       

        logger.info(f'InstalledAppsConfigured thread done for node {self.name}')
        g_testThreadsRunning -= 1

class NumberOfAppsOnNode(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global testThreadRunning, logger, g_testPassed, g_testThreadsRunning
        g_testThreadsRunning += 1
        logger.info(f'NumberOfAppsOnNode thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False

        session = requests.Session()
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = drv.get_all_apps_url(fullnode)

        logger.info(f'{url}')
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserpassword(fullnode)

        r=session.get(url, headers=ocsheaders)
        nodeApps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            nodeApps = j["ocs"]["data"]["apps"]
            logger.info(f'Number of apps on {fullnode}: {len(nodeApps)}')
        except:
            logger.warning(f'No JSON reply received')
            logger.warning(r.text)
            g_testThreadsRunning -= 1
            return
            
        try:
            numExpectedApps = expectedResults[drv.target]['ocsapps'][fullnode]
            logger.info(f'Expected number of apps differs from default for {fullnode}: {numExpectedApps}')
        except:
            numExpectedApps = expectedResults[drv.target]['ocsapps']['default']
            logger.info(f'Expected number of apps: {numExpectedApps}')

        if len(nodeApps) != numExpectedApps:
            logger.error(f'Fail: Number of apps {len(nodeApps)} != {numExpectedApps} for {self.name}')
            g_testThreadsRunning -= 1
            return
        else:
            logger.info(f'Pass: Number of apps {len(nodeApps)} == {numExpectedApps} for {self.name}')
            g_testPassed[fullnode] = True

        logger.info(f'Test number of apps done for node {self.name}')
        g_testThreadsRunning -= 1

class TestAppsOcs(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_number_of_apps_on_node(self):
        drv = sunetnextcloud.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                numberOfAppsOnNodeThread = NumberOfAppsOnNode(fullnode)
                numberOfAppsOnNodeThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    # Test if the apps installed on the node are found in the configuration file
    def test_installed_apps_configured(self):
        drv = sunetnextcloud.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                InstalledAppsConfiguredThread = InstalledAppsConfigured(fullnode)
                InstalledAppsConfiguredThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    # Test if all configured/expected apps are installed on the node
    def test_configured_apps_installed(self):
        drv = sunetnextcloud.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                ConfiguredAppsInstalledThread = ConfiguredAppsInstalled(fullnode)
                ConfiguredAppsInstalledThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    # Test if the apps installed on the node are found in the configuration file
    def test_app_announcementcenter(self):
        drv = sunetnextcloud.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                InstalledAppsConfiguredThread = InstalledAppsConfigured(fullnode, app='announcementcenter', checkEnabled=True)
                InstalledAppsConfiguredThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'Passed: {g_testPassed[fullnode]} for {fullnode}')
                self.assertTrue(g_testPassed[fullnode])

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))