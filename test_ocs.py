""" Testing OCS functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import HtmlTestRunner
import requests
import json
import time
import logging
import threading
import xmlrunner

import sunetnextcloud

ocsheaders = { "OCS-APIRequest" : "true" } 

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

g_testPassed = {}
g_testThreadsRunning = 0
g_requestTimeout = 10

logger = logging.getLogger('TestLogger')
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class AppVersions(threading.Thread):
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

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

        try:    
            userSamlFound = False
            session = requests.Session()
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = drv.get_all_apps_url(fullnode)

            logger.info(url)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception as error:
            logger.error(f'Error getting credentials for {url}:{error}')
            g_testThreadsRunning -= 1
            return

        try:
            r=session.get(url, headers=ocsheaders, verify=self.verify)
        except Exception as error:
            logger.error(f'Error getting {url}:{error}')
            g_testThreadsRunning -= 1
            return
        # nodeApps = []   # TODO: Check for apps installed on node
        apps = []
        try:
            j = json.loads(r.text)
            # print(json.dumps(j, indent=4, sort_keys=True))
            apps = j["ocs"]["data"]["apps"]
        except Exception as error:
            logger.error(f'No or invalid JSON reply received from {fullnode}:{error}')
            logger.error(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        if 'user_saml' in apps:
            userSamlFound = True

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

            try:
                r=session.get(url, headers=ocsheaders, verify=self.verify)
            except Exception as error:
                logger.error(f'Error getting {url}:{error}')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

            try:
                j = json.loads(r.text)
                # print(json.dumps(j, indent=4, sort_keys=True))
                logger.info(j["ocs"]["data"]["id"])
                logger.info(j["ocs"]["data"]["version"])
                
            except Exception as error:
                logger.info(f'No JSON reply received from {fullnode}:{error}')
                logger.info(r.text)
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

            try:
                self.TestOcsCalls.assertTrue(userSamlFound)
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["id"], 'user_saml')
                self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"], expectedResults['apps']['user_saml'][drv.target]['version'])
            except Exception as error:
                logger.error(f'{error}')
                g_testPassed[fullnode] = False
                g_testThreadsRunning -= 1
                return

        # Summary and test
        logger.info(f'Saml app found: {userSamlFound}')

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'AppVersion thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class NodeUsers(threading.Thread):
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

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

        try:
            url = drv.get_add_user_url(fullnode)
            logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception as error:
            logger.error(f'Error getting credentials for {url}:{error}')
            g_testThreadsRunning -= 1
            return

        try:
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
        except Exception as error:
            logger.error(f'Error getting {url}:{error}')
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
            # logger.info(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
            logger.info(f'Received {len(users)} from {self.name}')
        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}:{error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'NodeUsers thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class NodeGroups(threading.Thread):
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

    def run(self):
        global logger
        global g_testPassed
        global g_testThreadsRunning
        g_testThreadsRunning += 1
        logger.info(f'NodeGroups thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

        try:
            url = drv.get_add_group_url(fullnode)
            logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception as error:
            logger.error(f'Error getting credentials for {url}:{error}')
            g_testThreadsRunning -= 1
            return

        try:
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
        except Exception as error:
            logger.error(f'Error getting {url}:{error}')
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
            # logger.info(json.dumps(j, indent=4, sort_keys=True))
            groups = j["ocs"]["data"]["groups"]
            logger.info(f'Received {len(groups)} from {self.name}')
        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}:{error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        
        # Test for forcemfa group
        # logger.info(json.dumps(j, indent=4, sort_keys=True))
        if "forcemfa" in j["ocs"]["data"]["groups"]:
            logger.info(f'Found forcemfa on {fullnode}')
        else:
            logger.info(f"Group forcemfa does not exist on {fullnode}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'NodeUsers thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class CapabilitiesNoUser(threading.Thread):
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

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
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
        except Exception as error:
            logger.error(f'Error getting {url}: {error}')
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}: {error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        try:
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode_2'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
            self.TestOcsCalls.assertEqual(j["ocs"]["data"]["version"]["string"], expectedResults[drv.target]['ocs_capabilities']['ocs_data_version_string'])
        except Exception as error:
            logger.error(f"Error with OCS capabilities assertion: {error}")
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'Capabilities no user thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class Capabilities(threading.Thread):
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

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

        try:
            r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=self.verify)
        except Exception as error:
            logger.error(f'Error getting {url}: {error}')
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
            logger.info(f'Node capabilities: {json.dumps(j, indent=4, sort_keys=True)}')

        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}: {error}")
            logger.info(r.text)
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'Capabilities thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class UserLifeCycle(threading.Thread):
    def __init__(self, name, TestOcsCalls, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify

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

        try:
            session = requests.Session()
            url = drv.get_add_user_url(fullnode)
            logger.info(f'{self.TestOcsCalls._testMethodName} {url}')
            nodeuser = drv.get_ocsuser(fullnode)
            nodepwd = drv.get_ocsuserapppassword(fullnode)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
        except Exception as error:
            logger.error(f'Error getting credentials for {url}:{error}')
            g_testThreadsRunning -= 1
            return

        cliuser = "__cli_user_" + fullnode
        clipwd = sunetnextcloud.Helper().get_random_string(12)

        data = { 'userid': cliuser, 'password': clipwd}

        logger.info(f'Create cli user {cliuser}')
        try:
            r = session.post(url, headers=ocsheaders, data=data, verify=self.verify)
        except Exception as error:
            logger.error(f'Error posting to create cli user: {error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return
        try:
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if (j["ocs"]["meta"]["statuscode"] != 100):
                logger.info(f'Retry to create cli user {cliuser} after error {j["ocs"]["meta"]["statuscode"]}')
                r = session.post(url, headers=ocsheaders, data=data, verify=self.verify)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))
        except Exception as error:
            logger.info(f"No JSON reply received from {fullnode}: {error}")
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
        try:
            r = session.put(disableuserurl, headers=ocsheaders, verify=self.verify)
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if (j["ocs"]["meta"]["statuscode"] != 100):
                logger.info(f'Retry to disable cli user {cliuser} after error {j["ocs"]["meta"]["statuscode"]}')
                r = session.put(disableuserurl, headers=ocsheaders, verify=self.verify)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))

            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])

            logger.info(f'Delete cli user {cliuser}')
            userurl = drv.get_user_url(fullnode, cliuser)
            userurl = userurl.replace("$USERNAME$", nodeuser)
            userurl = userurl.replace("$PASSWORD$", nodepwd)
            r = session.delete(userurl, headers=ocsheaders, verify=drv.verify)
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4, sort_keys=True))

            if (j["ocs"]["meta"]["statuscode"] != 100):
                logger.info(f'Retry to delete cli user after {cliuser} after error {j["ocs"]["meta"]["statuscode"]}')
                r = session.delete(userurl, headers=ocsheaders, verify=self.verify)
                j = json.loads(r.text)
                logger.info(json.dumps(j, indent=4, sort_keys=True))

            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["status"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["statuscode"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode'])
            self.TestOcsCalls.assertEqual(j["ocs"]["meta"]["message"], expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message'])
        except Exception as error:
            logger.info(f"No or invalid JSON reply received from {fullnode}: {error}")
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
                capabilitiesNoUserThread = CapabilitiesNoUser(fullnode, self, verify=drv.verify)
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
                capabilitiesThread = Capabilities(fullnode, self, verify=drv.verify)
                capabilitiesThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_nodeusers(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                nodeUsersThread = NodeUsers(fullnode, self, verify=drv.verify)
                nodeUsersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

    def test_nodegroups(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                nodeUsersThread = NodeGroups(fullnode, self, verify=drv.verify)
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
                userLifecycleThread = UserLifeCycle(fullnode, self, verify=drv.verify)
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
                appVersionsThread = AppVersions(fullnode, self, verify=drv.verify)
                appVersionsThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-acceptance", add_timestamp=False))
