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
import threading

import sunetnextcloud

ocsheaders = { "OCS-APIRequest" : "true" } 
expectedResultsFile = 'expected.yaml'
testThreadRunning = False

logger = logging.getLogger('TestLogger')
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

class AppVersions(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global testThreadRunning
        global logger
        global expectedResults
        testThreadRunning = True
        logger.info(f'AppVersion thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name

        userSamlFound = False
        gssFound = False

        session = requests.Session()
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = drv.get_all_apps_url(fullnode)

        logger.info(url)
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserpassword(fullnode)

        r=session.get(url, headers=ocsheaders)
        nodeApps = []
        apps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            apps = j["ocs"]["data"]["apps"]
        except:
            logger.error(f'No JSON reply received')
            logger.error(r.text)

        if 'user_saml' in apps:
            userSamlFound = True
        if 'globalsiteselector' in apps:
            gssFound = True

        # # user_saml check
        if userSamlFound:
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = drv.get_app_url(fullnode, 'user_saml')

            logger.info(url)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)

            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserpassword(fullnode)

            r=session.get(url, headers=ocsheaders)
            try:
                j = json.loads(r.text)
                # print(json.dumps(j, indent=4, sort_keys=True))
                logger.info(j["ocs"]["data"]["id"])
                logger.info(j["ocs"]["data"]["version"])
                
            except:
                logger.info(f'No JSON reply received')
                logger.info(r.text)
                testThreadRunning = False
                return

            try:
                self.TestOcsCalls.assertTrue(userSamlFound)
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["id"], 'user_saml')
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"], expectedResults['apps']['user_saml'][drv.target]['version'])
            except:
                logger.error(f'Error with user_saml app')
                testThreadRunning = False

        # # global site selector check
        if gssFound:
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = drv.get_app_url(fullnode, 'globalsiteselector')

            logger.info(url)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)

            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserpassword(fullnode)

            r=session.get(url, headers=ocsheaders)
            try:
                j = json.loads(r.text)
                logger.info(j["ocs"]["data"]["id"])
                logger.info(j["ocs"]["data"]["version"])
                # print(json.dumps(j, indent=4, sort_keys=True))
            except:
                logger.info(f'No JSON reply received')
                logger.info(r.text)
                testThreadRunning = False
                return
            
            try:
                self.TestOcsCalls.assertTrue(gssFound)
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["id"], 'globalsiteselector')
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"], expectedResults['apps']['globalsiteselector'][drv.target]['version'])
            except:
                logger.error(f'Error with GSS configuration')
                testThreadRunning = False
                return

        # Summary and test
        logger.info(f'Saml app found: {userSamlFound}')
        logger.info(f'Gss app found: {gssFound}')


        logger.info(f'AppVersion thread done for node {self.name}')
        testThreadRunning = False

class NodeUsers(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'NodeUsers thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name

        url = drv.get_add_user_url(fullnode)
        logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        r = requests.get(url, headers=ocsheaders)
        try:
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
        except:
            logger.info("No JSON reply received")
            logger.info(r.text)
            testThreadRunning = False
            return

        logger.info(f'NodeUsers thread done for node {self.name}')
        testThreadRunning = False

class CapabilitiesNoUser(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global testThreadRunning
        global logger
        global expectedResults
        testThreadRunning = True
        logger.info(f'Capabilities no user thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name

        url = drv.get_ocs_capabilities_url(fullnode)
        logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
        r=requests.get(url, headers=ocsheaders)
        try:
            j = json.loads(r.text)
        except:
            logger.info("No JSON reply received")
            logger.info(r.text)
            testThreadRunning = False
            return

        try:
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
            self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"]["string"], expectedResults[drv.target]['ocs_capabilities']['ocs_data_version_string'])
        except:
            logger.error(f"Error with OCS capabilities assertion")
            testThreadRunning = False
            return

        testThreadRunning = False

        logger.info(f'Capabilities no user thread done for node {self.name}')


class Capabilities(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global testThreadRunning
        global logger
        testThreadRunning = True
        logger.info(f'Capabilities thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name

        url = drv.get_ocs_capabilities_url(fullnode)
        logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserpassword(fullnode)

        r=requests.get(url, headers=ocsheaders, auth = HTTPBasicAuth(nodeuser, nodepwd))
        try:
            j = json.loads(r.text)
        except:
            logger.info("No JSON reply received")
            logger.info(r.text)
            testThreadRunning = False
            return

        # TBD: Add assertion for GSS enabled
        # self.assertEqual(j["ocs"]["data"]["capabilities"]["globalscale"]["enabled"], ocsresult.ocs_data_capabilities_globalscale_enabled)
        logger.info(f'Capabilities thread done for node {self.name}')
        testThreadRunning = False

class UserLifeCycle(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global testThreadRunning
        global expectedResults
        testThreadRunning = True
        logger.info(f'User lifecycle thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name

        session = requests.Session()
        url = drv.get_add_user_url(fullnode)
        logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        cliuser = "__cli_user_" + fullnode
        clipwd = sunetnextcloud.Helper().get_random_string(12)

        data = { 'userid': cliuser, 'password': clipwd}

        logger.info(f'Create cli user {cliuser}')
        r = session.post(url, headers=ocsheaders, data=data)
        try:
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if (j["ocs"]["meta"]["statuscode"] == 996):
                logger.info(f'Create cli user after internal server error {cliuser}')
                r = session.post(url, headers=ocsheaders, data=data)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))
        except:
            logger.info("No JSON reply received")
            logger.info(r.text)
            testThreadRunning = False
            return

        # self.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
        # self.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
        # self.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])

        logger.info(f'Disable cli user {cliuser}')
        disableuserurl = drv.get_disable_user_url(fullnode, cliuser)
        disableuserurl = disableuserurl.replace("$USERNAME$", nodeuser)
        disableuserurl = disableuserurl.replace("$PASSWORD$", nodepwd)
        r = session.put(disableuserurl, headers=ocsheaders)
        try:
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if (j["ocs"]["meta"]["statuscode"] == 996):
                logger.info(f'Disable cli user after internal server error {cliuser}')
                r = session.put(disableuserurl, headers=ocsheaders)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))

            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])

            logger.info(f'Delete cli user {cliuser}')
            userurl = drv.get_user_url(fullnode, cliuser)
            userurl = userurl.replace("$USERNAME$", nodeuser)
            userurl = userurl.replace("$PASSWORD$", nodepwd)
            r = session.delete(userurl, headers=ocsheaders)
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if (j["ocs"]["meta"]["statuscode"] == 996):
                logger.info(f'Delete cli user after internal server error {cliuser}')
                r = session.delete(userurl, headers=ocsheaders)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))

            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
        except:
            logger.info("No JSON reply received")
            logger.info(r.text)
            testThreadRunning = False
            return

        logger.info(f'User lifecycle thread done for node {self.name}')
        testThreadRunning = False

class TestOcsCalls(unittest.TestCase):
    def test_logger(self):
        logger.info(f'logger.info test_logger')
        pass

    def test_capabilities_nouser(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                capabilitiesNoUserThread = CapabilitiesNoUser(fullnode, self)
                capabilitiesNoUserThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def test_capabilities(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                capabilitiesThread = Capabilities(fullnode, self)
                capabilitiesThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def test_gssusers(self):
        drv = sunetnextcloud.TestTarget()
        if drv.testgss == False:
            logger.info(f'Not testing gss')
            return

        fullnode = 'gss'
        url = drv.get_add_user_url(fullnode)
        logger.info(f'{self._testMethodName} {url}')
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        r = requests.get(url, headers=ocsheaders)
        try:
            j = json.loads(r.text)
            # logger.info(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
        except:
            logger.info("No JSON reply received")
            logger.info(r.text)

    def test_nodeusers(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                nodeUsersThread = NodeUsers(fullnode, self)
                nodeUsersThread.start()

        while(testThreadRunning == True):
            time.sleep(1)


    def test_userlifecycle(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                userLifecycleThread = UserLifeCycle(fullnode, self)
                userLifecycleThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

    def test_app_versions(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                appVersionsThread = AppVersions(fullnode, self)
                appVersionsThread.start()

        while(testThreadRunning == True):
            time.sleep(1)

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
