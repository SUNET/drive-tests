""" Testing OCS functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import time
import yaml
import logging

import sunetdrive

ocsheaders = { "OCS-APIRequest" : "true" } 
expectedResultsFile = 'expected.yaml'

class TestOcsCalls(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)
    with open(expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_capabilities_nouser(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_ocs_capabilities_url(fullnode)
                self.logger.info(f'{self._testMethodName} {url}')
                r=requests.get(url, headers=ocsheaders)
                try:
                    j = json.loads(r.text)
                except:
                    self.logger.info("No JSON reply received")
                    self.logger.info(r.text)

                self.assertEqual(j["ocs"]["meta"]["status"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
                self.assertEqual(j["ocs"]["meta"]["statuscode"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
                self.assertEqual(j["ocs"]["meta"]["message"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
                self.assertEqual(j["ocs"]["data"]["version"]["string"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_data_version_string'])

    def test_capabilities(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_ocs_capabilities_url(fullnode)
                self.logger.info(f'{self._testMethodName} {url}')
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserpassword(fullnode)

                r=requests.get(url, headers=ocsheaders, auth = HTTPBasicAuth(nodeuser, nodepwd))
                try:
                    j = json.loads(r.text)
                except:
                    self.logger.info("No JSON reply received")
                    self.logger.info(r.text)

                # TBD: Add assertion for GSS enabled
                # self.assertEqual(j["ocs"]["data"]["capabilities"]["globalscale"]["enabled"], ocsresult.ocs_data_capabilities_globalscale_enabled)

    def test_gssusers(self):
        drv = sunetdrive.TestTarget()
        fullnode = 'gss'
        url = drv.get_add_user_url(fullnode)
        self.logger.info(f'{self._testMethodName} {url}')
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        r = requests.get(url, headers=ocsheaders)
        try:
            j = json.loads(r.text)
            self.logger.info(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
        except:
            self.logger.info("No JSON reply received")
            self.logger.info(r.text)

    def test_nodeusers(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_add_user_url(fullnode)
                self.logger.info(f'{self._testMethodName} {url}')
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)

                r = requests.get(url, headers=ocsheaders)
                try:
                    j = json.loads(r.text)
                    self.logger.info(json.dumps(j, indent=4, sort_keys=True))
                    users = j["ocs"]["data"]["users"]
                except:
                    self.logger.info("No JSON reply received")
                    self.logger.info(r.text)

    def test_userlifecycle(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                session = requests.Session()
                url = drv.get_add_user_url(fullnode)
                self.logger.info(f'{self._testMethodName} {url}')
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)

                cliuser = "__cli_user_" + fullnode
                clipwd = sunetdrive.Helper().get_random_string(12)

                data = { 'userid': cliuser, 'password': clipwd}

                self.logger.info(f'Create cli user {cliuser}')
                r = session.post(url, headers=ocsheaders, data=data)
                try:
                    j = json.loads(r.text)
                    self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                    if (j["ocs"]["meta"]["statuscode"] == 996):
                        self.logger.info(f'Create cli user after internal server error {cliuser}')
                        r = session.post(url, headers=ocsheaders, data=data)
                        j = json.loads(r.text)
                        self.logger.info(json.dumps(j, indent=4, sort_keys=True))
                except:
                    self.logger.info("No JSON reply received")
                    self.logger.info(r.text)

                # self.assertEqual(j["ocs"]["meta"]["status"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
                # self.assertEqual(j["ocs"]["meta"]["statuscode"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
                # self.assertEqual(j["ocs"]["meta"]["message"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])

                self.logger.info(f'Disable cli user {cliuser}')
                disableuserurl = drv.get_disable_user_url(fullnode, cliuser)
                disableuserurl = disableuserurl.replace("$USERNAME$", nodeuser)
                disableuserurl = disableuserurl.replace("$PASSWORD$", nodepwd)
                r = session.put(disableuserurl, headers=ocsheaders)
                try:
                    j = json.loads(r.text)
                    self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                    if (j["ocs"]["meta"]["statuscode"] == 996):
                        self.logger.info(f'Disable cli user after internal server error {cliuser}')
                        r = session.put(disableuserurl, headers=ocsheaders)
                        j = json.loads(r.text)
                        self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                    self.assertEqual(j["ocs"]["meta"]["status"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
                    self.assertEqual(j["ocs"]["meta"]["statuscode"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
                    self.assertEqual(j["ocs"]["meta"]["message"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])

                    self.logger.info(f'Delete cli user {cliuser}')
                    userurl = drv.get_user_url(fullnode, cliuser)
                    userurl = userurl.replace("$USERNAME$", nodeuser)
                    userurl = userurl.replace("$PASSWORD$", nodepwd)
                    r = session.delete(userurl, headers=ocsheaders)
                    j = json.loads(r.text)
                    self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                    if (j["ocs"]["meta"]["statuscode"] == 996):
                        self.logger.info(f'Delete cli user after internal server error {cliuser}')
                        r = session.delete(userurl, headers=ocsheaders)
                        j = json.loads(r.text)
                        self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                    self.assertEqual(j["ocs"]["meta"]["status"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
                    self.assertEqual(j["ocs"]["meta"]["statuscode"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
                    self.assertEqual(j["ocs"]["meta"]["message"], self.expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
                except:
                    self.logger.info("No JSON reply received")
                    self.logger.info(r.text)

    def test_app_versions(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                userSamlFound = False
                gssFound = False

                session = requests.Session()
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = drv.get_all_apps_url(fullnode)

                self.logger.info(url)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)

                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserpassword(fullnode)

                r=session.get(url, headers=ocsheaders)
                nodeApps = []
                try:
                    j = json.loads(r.text)
                    # print(json.dumps(j, indent=4, sort_keys=True))
                    apps = j["ocs"]["data"]["apps"]
                except:
                    self.logger.info(f'No JSON reply received')
                    self.logger.info(r.text)

                if 'user_saml' in apps:
                    userSamlFound = True
                if 'globalsiteselector' in apps:
                    gssFound = True

                # # user_saml check
                if userSamlFound:
                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserapppassword(fullnode)
                    url = drv.get_app_url(fullnode, 'user_saml')

                    self.logger.info(url)
                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)

                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserpassword(fullnode)

                    r=session.get(url, headers=ocsheaders)
                    try:
                        j = json.loads(r.text)
                        # print(json.dumps(j, indent=4, sort_keys=True))
                        self.logger.info(j["ocs"]["data"]["id"])
                        self.logger.info(j["ocs"]["data"]["version"])
                        
                    except:
                        self.logger.info(f'No JSON reply received')
                        self.logger.info(r.text)

                    self.assertTrue(userSamlFound)
                    self.assertEqual(j["ocs"]["data"]["id"], 'user_saml')
                    self.assertEqual(j["ocs"]["data"]["version"], self.expectedResults['apps']['user_saml'][drv.target]['version'])

                # # global site selector check
                if gssFound:
                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserapppassword(fullnode)
                    url = drv.get_app_url(fullnode, 'globalsiteselector')

                    self.logger.info(url)
                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)

                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserpassword(fullnode)

                    r=session.get(url, headers=ocsheaders)
                    try:
                        j = json.loads(r.text)
                        self.logger.info(j["ocs"]["data"]["id"])
                        self.logger.info(j["ocs"]["data"]["version"])
                        # print(json.dumps(j, indent=4, sort_keys=True))
                    except:
                        self.logger.info(f'No JSON reply received')
                        self.logger.info(r.text)

                    self.assertTrue(gssFound)
                    self.assertEqual(j["ocs"]["data"]["id"], 'globalsiteselector')
                    self.assertEqual(j["ocs"]["data"]["version"], self.expectedResults['apps']['globalsiteselector'][drv.target]['version'])

                # Summary and test
                self.logger.info(f'Saml app found: {userSamlFound}')
                self.logger.info(f'Gss app found: {gssFound}')


if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
