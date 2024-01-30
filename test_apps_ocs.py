import os
import requests
from requests.auth import HTTPBasicAuth
import json
import unittest
import yaml
import sunetdrive
import logging
import time
import threading

ocsheaders = { "OCS-APIRequest" : "true" } 
expectedResultsFile = 'expected.yaml'
testThreadRunning = False

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

class ConfiguredAppsInstalled(threading.Thread):
    def __init__(self, name, TestAppsOcs):
        threading.Thread.__init__(self)
        self.name = name
        self.TestAppsOcs = TestAppsOcs

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'ConfiguredAppsInstalled thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name    

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
            testThreadRunning = False
            self.TestAppsOcs.assertTrue(False)

        logger.info(f'Check if all apps configured in {expectedResultsFile} are installed on {fullnode}')

        for expectedApp in expectedResults['apps']:
            logger.info(f'Check if {expectedApp} is installed on {fullnode}')
            print()
            try:
                pos = nodeApps.index(expectedApp)
                logger.info(f'Found app at {pos}')    
            except:
                logger.warning(f'App {expectedApp} NOT found on {fullnode}')

        logger.info(f'ConfiguredAppsInstalled thread done for node {self.name}')
        testThreadRunning = False

class InstalledAppsConfigured(threading.Thread):
    def __init__(self, name, TestAppsOcs):
        threading.Thread.__init__(self)
        self.name = name
        self.TestAppsOcs = TestAppsOcs

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'InstalledAppsConfigured thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name

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
            logger.warning(f'No JSON reply received on {fullnode}')
            # self.logger.warning(r.text)
            testThreadRunning = False
            self.TestAppsOcs.assertTrue(False)

        logger.info(f'Check if all installed apps on {fullnode} are found in {expectedResultsFile}')
        for nodeApp in nodeApps:
            try:
                appInfo = expectedResults['apps'][nodeApp]
            except:
                logger.warning(f'{nodeApp} NOT found on {fullnode}')

        logger.info(f'InstalledAppsConfigured thread done for node {self.name}')
        testThreadRunning = False

class NumberOfAppsOnNode(threading.Thread):
    def __init__(self, name, TestAppsOcs):
        threading.Thread.__init__(self)
        self.name = name
        self.TestAppsOcs = TestAppsOcs

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'NumberOfAppsOnNode thread started for node {self.name}')
        drv = sunetdrive.TestTarget()
        fullnode = self.name

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
            testThreadRunning = False
            
        try:
            numExpectedApps = expectedResults[drv.target]['ocsapps'][fullnode]
            logger.info(f'Expected number of apps differs from default: {numExpectedApps}')
        except:
            numExpectedApps = expectedResults[drv.target]['ocsapps']['default']
            logger.info(f'Expected number of apps: {numExpectedApps}')
            testThreadRunning = False

        try:
            self.TestAppsOcs.assertEqual(len(nodeApps), numExpectedApps)
            logger.info(f'NumberOfAppsOnNode thread done for node {self.name}')
        except:
            logger.error(f'Error with number of apps for node {self.name}')
            testThreadRunning = False

        logger.info(f'Test number of apps done for node {self.name}')
        testThreadRunning = False

class TestAppsOcs(unittest.TestCase):
    def test_logger(self):
        global logger
        logger.info(f'self.logger.info test_logger')
        pass

    def test_number_of_apps_on_node(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                numberOfAppsOnNodeThread = NumberOfAppsOnNode(fullnode, self)
                numberOfAppsOnNodeThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    # Test if the apps installed on the node are found in the configuration file
    def test_installed_apps_configured(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                InstalledAppsConfiguredThread = InstalledAppsConfigured(fullnode, self)
                InstalledAppsConfiguredThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    # Test if all configured/expected apps are installed on the node
    def test_configured_apps_installed(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                ConfiguredAppsInstalledThread = ConfiguredAppsInstalled(fullnode, self)
                ConfiguredAppsInstalledThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

if __name__ == '__main__':
    # unittest.main()
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))