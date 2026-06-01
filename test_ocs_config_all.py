"""Testing OCS functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import json
import logging
import os
import threading
import time
import unittest
from urllib.parse import quote
from pathlib import Path

import requests
import xmlrunner
import HtmlTestRunner

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
ocsheaders = drv.ocsheaders
expectedResults = drv.expectedResults

g_testPassed = {}
g_testThreadsRunning = 0
g_requestTimeout = 10
g_localDirectory = "./provisioning_config"

logger = logging.getLogger("TestLogger")
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

class TestOcsConfigAll(unittest.TestCase):
    def test_logger(self):
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_get_configuration(self):
        logger.info(f"TestID: {self._testMethodName}")

        Path(g_localDirectory).mkdir(parents=True, exist_ok=True)

        node_configuration = {}
        for node in drv.allnodes:

            node_config_path = f'{g_localDirectory}/{node}.{drv.target}.json'

            logger.info(f'Execute for {node}')
            nodeuser = drv.get_ocsuser(node)
            nodepwd = drv.get_ocsuserapppassword(node)

            rawurl = drv.get_all_apps_url(node)
            logger.info(rawurl)
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
            session = requests.Session()
            r = session.get(url, headers=ocsheaders)

            try:
                j = json.loads(r.text)
                apps = j["ocs"]["data"]["apps"]
            except Exception as error:
                logger.error(f"No or invalid apps JSON reply received from {node}:{error}")
                continue

            for app in apps:
                logger.info(f'Get configuration for {app}')

                try:
                    rawurl = drv.get_app_url(node, app)
                    url = rawurl.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)
                    r = session.get(url, headers=ocsheaders)
                    j = json.loads(r.text)
                    # logger.info(json.dumps(j, indent=4))

                    logger.info(f'Get configuration keys for {app}')

                    rawurl = drv.get_app_config_keys_url(node, app)
                    url = rawurl.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)
                    r = session.get(url, headers=ocsheaders)
                    j = json.loads(r.text)
                    # logger.info(json.dumps(j, indent=4))

                    key = 'none'
                    for key in j['ocs']['data']['data']:
                        logger.info(f'Get app config value for node: {node} - app: {app} - key: {key}')
                        # key = 'auto_groups'
                        # app = 'stepupauth'
                        rawurl = drv.get_app_config_value_url(node, app, key)

                        url = rawurl.replace("$USERNAME$", nodeuser)
                        url = url.replace("$PASSWORD$", nodepwd)
                        r = session.get(url, headers=ocsheaders)
                        j = json.loads(r.text)

                        # logger.info(f'Append node configuration ')
                        node_configuration.setdefault(node, {}).setdefault(app, {})[key] = j['ocs']['data']['data']

                    # r = session.post(url, headers=ocsheaders)
                    # j = json.loads(r.text)
                    # logger.info(json.dumps(j, indent=4))
                except Exception as error:
                    logger.error(f"No or invalid JSON reply received from node: {node} - app: {app} - {key}:{error}")
                    continue


            # logger.info(f'Full node configuration: {json.dumps(node_configuration, indent=4)}')

            # Check if the file exists and write configuration into it
            node_config_file = Path(node_config_path)
            if node_config_file.is_file():
                logger.info(f'Do not overwrite existing configuration file')
                # file exists
            else:
                with open(node_config_path, 'w') as f:
                    logger.info(f'Save node configuration file to {node_config_path}')
                    json.dump(node_configuration, f, indent=4, sort_keys=True)

if __name__ == "__main__":
    if drv.testrunner == "xml":
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output="test-reports"))
    elif drv.testrunner == "txt":
        unittest.main(
            testRunner=unittest.TextTestRunner(
                resultclass=sunetnextcloud.NumbersTestResult
            )
        )
    else:
        unittest.main(
            testRunner=HtmlTestRunner.HTMLTestRunner(
                output="test-reports-html",
                combine_reports=True,
                report_name=f"nextcloud-{drv.target}-{drv.expectedResults[drv.target]['status']['version'][-1]}-{os.path.basename(__file__)}",
                add_timestamp=False,
            )
        )
