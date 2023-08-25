import os
import requests
from requests.auth import HTTPBasicAuth
import json
import unittest
import yaml
import sunetdrive
import logging

ocsheaders = { "OCS-APIRequest" : "true" } 
appsConfigurationFile = 'expected.yaml'

class TestAppsOcs(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_number_of_apps_on_node(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                session = requests.Session()
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = drv.get_all_apps_url(fullnode)

                self.logger.info(f'{url}')
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
                    self.logger.info(f'Number of apps on {fullnode}: {len(nodeApps)}')
                except:
                    self.logger.warning(f'No JSON reply received')
                    self.logger.warning(r.text)
                    
                with open(appsConfigurationFile, "r") as stream:
                    expectedApps=yaml.safe_load(stream)
                    try:
                        numExpectedApps = expectedApps[drv.target]['ocsapps'][fullnode]
                        self.logger.info(f'Expected number of apps differs from default: {numExpectedApps}')
                    except:
                        numExpectedApps = expectedApps[drv.target]['ocsapps']['default']
                        self.logger.info(f'Expected number of apps: {numExpectedApps}')

                    self.assertEqual(len(nodeApps), numExpectedApps)
    # Test if the apps installed on the node are found in the configuration file
    def test_installed_apps_configured(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                session = requests.Session()
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = drv.get_all_apps_url(fullnode)

                self.logger.info(f'{url}')
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
                    self.logger.warning(f'No JSON reply received on {fullnode}')
                    # self.logger.warning(r.text)
                    self.assertTrue(False)

                with open(appsConfigurationFile, "r") as stream:
                    expectedApps=yaml.safe_load(stream)

                    self.logger.info(f'Check if all installed apps on {fullnode} are found in {appsConfigurationFile}')
                    for nodeApp in nodeApps:
                        try:
                            appInfo = expectedApps['apps'][nodeApp]
                        except:
                            self.logger.warning(f'{nodeApp} NOT found on {fullnode}')

    # Test if all configured/expected apps are installed on the node
    def test_configured_apps_installed(self):
        drv = sunetdrive.TestTarget()

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                session = requests.Session()
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = drv.get_all_apps_url(fullnode)

                self.logger.info(f'{url}')
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
                    self.logger.warning(f'No JSON reply received on node {fullnode}')
                    # self.logger.warning(r.text)
                    self.assertTrue(False)

                with open(appsConfigurationFile, "r") as stream:
                    expectedApps=yaml.safe_load(stream)

                    self.logger.info(f'Check if all apps configured in {appsConfigurationFile} are installed on {fullnode}')

                    for expectedApp in expectedApps['apps']:
                        self.logger.info(f'Check if {expectedApp} is installed on {fullnode}')
                        print()
                        try:
                            pos = nodeApps.index(expectedApp)
                            self.logger.info(f'Found app at {pos}')    
                        except:
                            self.logger.warning(f'App {expectedApp} NOT found on {fullnode}')

if __name__ == '__main__':
    # unittest.main()
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))