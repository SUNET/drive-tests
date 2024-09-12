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
import xmlrunner

import sunetnextcloud

ocsheaders = { "OCS-APIRequest" : "true" } 
expectedResultsFile = 'expected.yaml'
g_testPassed = {}
g_testThreadsRunning = 0
g_requestTimeout = 10

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
        global logger
        global expectedResults
        global g_testPassed
        global g_testThreadsRunning
        g_testThreadsRunning +=1
        logger.info(f'AppVersion thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

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

        try:
            r=session.get(url, headers=ocsheaders)
        except:
            logger.error(f'Error getting {url}')
            g_testThreadsRunning -= 1
            return
        nodeApps = []
        apps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            apps = j["ocs"]["data"]["apps"]
        except:
            logger.error(f'No or invalid JSON reply received from {fullnode}')
            logger.error(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

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
                logger.info(f'No JSON reply received from {fullnode}')
                logger.info(r.text)
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

            try:
                self.TestOcsCalls.assertTrue(userSamlFound)
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["id"], 'user_saml')
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"], expectedResults['apps']['user_saml'][drv.target]['version'])
            except:
                logger.error(f'Error with user_saml app, version {j["ocs"]["data"]["version"]} != {expectedResults["apps"]["user_saml"][drv.target]["version"]}')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

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
                logger.info(f'No JSON reply received from {fullnode}')
                logger.info(r.text)
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return
            
            try:
                self.TestOcsCalls.assertTrue(gssFound)
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["id"], 'globalsiteselector')
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"], expectedResults['apps']['globalsiteselector'][drv.target]['version'])
            except:
                logger.error(f'Error with GSS configuration, {j["ocs"]["data"]["version"]} != {expectedResults["apps"]["globalsiteselector"][drv.target]["version"]}')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        # Summary and test
        logger.info(f'Saml app found: {userSamlFound}')
        logger.info(f'Gss app found: {gssFound}')


        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'AppVersion thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class NodeUsers(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        g_testThreadsRunning += 1
        logger.info(f'NodeUsers thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

        url = drv.get_add_user_url(fullnode)
        logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        try:
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except:
            logger.error(f'Error getting {url}')
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
            # logger.info(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
            logger.info(f'Received {len(users)} from {self.name}')
        except:
            logger.info(f"No JSON reply received from {fullnode}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'NodeUsers thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class CapabilitiesNoUser(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global g_testPassed
        global g_testThreadsRunning
        global logger
        global expectedResults
        g_testThreadsRunning += 1
        logger.info(f'Capabilities no user thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

        url = drv.get_ocs_capabilities_url(fullnode)
        logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
        try:
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except:
            logger.error(f'Error getting {url}')
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
        except:
            logger.info(f"No JSON reply received from {fullnode}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        try:
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode_2'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
            self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"]["string"], expectedResults[drv.target]['ocs_capabilities']['ocs_data_version_string'])
        except:
            logger.error(f"Error with OCS capabilities assertion")
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'Capabilities no user thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class Capabilities(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global g_testPassed
        global g_testThreadsRunning
        global logger
        g_testThreadsRunning += 1
        logger.info(f'Capabilities thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

        url = drv.get_ocs_capabilities_url(fullnode)
        logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserpassword(fullnode)

        try:
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except:
            logger.error(f'Error getting {url}')
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
            logger.info(f'Node capabilities: {json.dumps(j, indent=4, sort_keys=True)}')

        except:
            logger.info(f"No JSON reply received from {fullnode}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        # TBD: Add assertion for GSS enabled
        # self.assertEqual(j["ocs"]["data"]["capabilities"]["globalscale"]["enabled"], ocsresult.ocs_data_capabilities_globalscale_enabled)
        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'Capabilities thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class UserLifeCycle(threading.Thread):
    def __init__(self, name, TestOcsCalls):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls

    def run(self):
        global g_testPassed
        global g_testThreadsRunning
        global expectedResults
        g_testThreadsRunning += 1
        logger.info(f'User lifecycle thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

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
        try:
            r = session.post(url, headers=ocsheaders, data=data)
        except:
            logger.error(f'Error posting to create cli user')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if (j["ocs"]["meta"]["statuscode"] != 100):
                logger.info(f'Retry to create cli user {cliuser} after error {j["ocs"]["meta"]["statuscode"]}')
                r = session.post(url, headers=ocsheaders, data=data)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))
        except:
            logger.info(f"No JSON reply received from {fullnode}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
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

            if (j["ocs"]["meta"]["statuscode"] != 100):
                logger.info(f'Retry to disable cli user {cliuser} after error {j["ocs"]["meta"]["statuscode"]}')
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

            if (j["ocs"]["meta"]["statuscode"] != 100):
                logger.info(f'Retry to delete cli user after {cliuser} after error {j["ocs"]["meta"]["statuscode"]}')
                r = session.delete(userurl, headers=ocsheaders)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))

            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
        except:
            logger.info(f"No or invalid JSON reply received from {fullnode}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        logger.info(f'User lifecycle thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        g_testThreadsRunning -= 1
        return

class TestOcsCalls(unittest.TestCase):
    def test_logger(self):
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_capabilities_nouser(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                capabilitiesNoUserThread = CapabilitiesNoUser(fullnode, self)
                capabilitiesNoUserThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_capabilities(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                capabilitiesThread = Capabilities(fullnode, self)
                capabilitiesThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_gssusers(self):
        drv = sunetnextcloud.TestTarget()
        logger.info(f'TestID: {self._testMethodName}')
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

        try:
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except:
            logger.error(f'Error getting {url}')
        try:
            j = json.loads(r.text)
            # logger.info(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
        except:
            logger.info(f"No JSON reply received from {fullnode}")
            logger.info(r.text)

    def test_nodeusers(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                nodeUsersThread = NodeUsers(fullnode, self)
                nodeUsersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_userlifecycle(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                userLifecycleThread = UserLifeCycle(fullnode, self)
                userLifecycleThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_app_versions(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                appVersionsThread = AppVersions(fullnode, self)
                appVersionsThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
