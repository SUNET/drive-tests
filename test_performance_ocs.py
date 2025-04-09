""" Performance test create, disable, delete user
Author: Richard Freitag <freitag@sunet.se>
"""

import xmlrunner
import unittest
import HtmlTestRunner
import requests
import threading
from requests.auth import HTTPBasicAuth
import json
import logging
import os
import time
from datetime import datetime

import sunetnextcloud

nodes = 1
users = 10
offset = 0
createusers=True
deleteusers=True
disableusers=True
calls = 100

g_testThreadsRunning = 0
g_ocsPerformanceResults = []
g_testPassed = {}

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults

ocsheaders = { "OCS-APIRequest" : "true" } 

logger = logging.getLogger('TestLogger')
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class NodeOcsUserLifecycle(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global logger, g_testPassed, g_testThreadsRunning, g_ocsPerformanceResults
        g_testThreadsRunning += 1
        logger.info(f'NodeOcsUserLifecycle thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name

        url = drv.get_add_user_url(fullnode)
        # logger.info(self._testMethodName, url)
        startTime = datetime.now()
        for nodeindex in range(1, nodes+1):
            logger.info(f'Node: {str(nodeindex)}')

            for userindex in range(offset, offset+users+1):
                try:
                    logger.info(f'{drv.target} - User: {str(userindex)}')
                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserapppassword(fullnode)

                    usersuffix = str(nodeindex) + "_" + str(userindex)
                    cliuser = "__performance_user_" + usersuffix + "_" + fullnode


                    if (createusers==True):
                        url = url.replace("$USERNAME$", nodeuser)
                        url = url.replace("$PASSWORD$", nodepwd)
                        clipwd = sunetnextcloud.Helper().get_random_string(12)

                        data = { 'userid': cliuser, 'password': clipwd}

                        r = requests.post(url, headers=ocsheaders, data=data)
                        j = json.loads(r.text)
                        # logger.info(json.dumps(j, indent=4, sort_keys=True))
                        logger.info(j["ocs"]["meta"]["status"])

                    if (disableusers==True):
                        logger.info("Disable cli user " + cliuser)
                        disableuserurl = drv.get_disable_user_url(fullnode, cliuser)
                        disableuserurl = disableuserurl.replace("$USERNAME$", nodeuser)
                        disableuserurl = disableuserurl.replace("$PASSWORD$", nodepwd)
                        r = requests.put(disableuserurl, headers=ocsheaders)
                        j = json.loads(r.text)
                        logger.info(j["ocs"]["meta"]["status"])
                        # logger.info(json.dumps(j, indent=4, sort_keys=True))

                    if (deleteusers==True):
                        logger.info("Delete cli user " + cliuser)
                        userurl = drv.get_user_url(fullnode, cliuser)
                        userurl = userurl.replace("$USERNAME$", nodeuser)
                        userurl = userurl.replace("$PASSWORD$", nodepwd)
                        r = requests.delete(userurl, headers=ocsheaders)
                        j = json.loads(r.text)
                        logger.info(j["ocs"]["meta"]["status"])
                except Exception as e:
                    logger.error(f'Unable to test user lifecycle for {fullnode}')
                    g_testPassed[fullnode] = False
                    g_testThreadsRunning -= 1
                    return
        totalTime = (datetime.now() - startTime).total_seconds()
        g_ocsPerformanceResults.append(f'{fullnode:<15} - Handling {nodes*users} users took {totalTime:<3.1f}s')

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'NodeOcsUserLifecycle thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class NodeOcsUserPerformance(threading.Thread):
    def __init__(self, name, TestOcsCalls, newSession, verify=True):
        threading.Thread.__init__(self)
        self.name = name
        self.TestOcsCalls = TestOcsCalls
        self.verify = verify
        self.newSession = newSession

    def run(self):
        global logger, g_testPassed, g_testThreadsRunning, g_ocsPerformanceResults
        g_testThreadsRunning += 1
        logger.info(f'NodeOcsUserPerformance thread started for node {self.name}')
        drv = sunetnextcloud.TestTarget()
        fullnode = self.name
        isMultinode = drv.is_multinode(fullnode)
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        g_testPassed[fullnode] = False
        logger.info(f'Setting passed for {fullnode} to {g_testPassed.get(fullnode)}')

        try:
            url = drv.get_status_url(fullnode)
            nodebaseurl = drv.get_node_base_url(fullnode)
            url = drv.get_add_user_url(fullnode)
            url = url.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
            message = f'{calls} calls to {nodebaseurl:<30}'

            if self.newSession:
                info = 'Main URL without cookie, new session'
                totalTime = 0.0
                for call in range(0,calls):
                    s = requests.Session()
                    s.headers.update(ocsheaders)
                    startTime = datetime.now()
                    r = s.get(url, headers=ocsheaders)
                    totalTime += (datetime.now() - startTime).total_seconds()
                    # logger.info(f'SERVERID cookie: {s.cookies.get_dict()["SERVERID"]}')

                message += f' - {totalTime:<3.1f}s'
                logger.info(f'{calls} request to {nodebaseurl} took {totalTime:<3.1f}s - {info}')
            else:
                info = 'Main URL without cookie, same session'
                totalTime = 0.0
                s = requests.Session()
                s.headers.update(ocsheaders)
                lastServerId = ''
                for call in range(0,calls):
                    startTime = datetime.now()
                    r = s.get(url, headers=ocsheaders)
                    totalTime += (datetime.now() - startTime).total_seconds()
                    if call == 0:
                        lastServerId = s.cookies.get_dict()['SERVERID']
                    newServerId = s.cookies.get_dict()['SERVERID']
                    if lastServerId != newServerId:
                        logger.warning(f'SERVERID for the session has changed! {lastServerId} != {newServerId}')
                    lastServerId = newServerId

                message += f' - {totalTime:<3.1f}s'
                logger.info(f'{calls} request to {nodebaseurl} took {totalTime:<3.1f}s - {info}')

            if self.newSession:
                info = 'Main URL with cookie, new session'
                if isMultinode:
                    totalTime = 0.0
                    serverid = f'{drv.get_multinode(fullnode)}.{drv.get_base_url()}'
                    for call in range(0,calls):
                        s = requests.Session()
                        s.headers.update(ocsheaders)
                        s.cookies.set('SERVERID', serverid)
                        startTime = datetime.now()
                        r = s.get(url, headers=ocsheaders)
                        totalTime += (datetime.now() - startTime).total_seconds()
                    message += f' - {totalTime:<3.1f}s'
                    logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')
                else:
                    for fe in range(1,4):
                        totalTime = 0.0
                        for call in range(0,calls):
                            s = requests.Session()
                            s.headers.update(ocsheaders)
                            serverid = f'node{fe}.{nodebaseurl}'
                            s.cookies.set('SERVERID', serverid)
                            startTime = datetime.now()
                            r = s.get(url, headers=ocsheaders)
                            totalTime += (datetime.now() - startTime).total_seconds()
                        message += f' - {totalTime:<3.1f}s'
                        logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')
            else:
                info = 'Main URL with cookie, same session'
                if isMultinode:
                    serverid = f'{drv.get_multinode(fullnode)}.{drv.get_base_url()}'
                    logger.info(f'Test multinode {fullnode} on {serverid}')
                    totalTime = 0.0
                    s = requests.Session()
                    s.headers.update(ocsheaders)
                    s.cookies.set('SERVERID', serverid)
                    for call in range(0,calls):
                        startTime = datetime.now()
                        r = s.get(url, headers=ocsheaders)
                        totalTime += (datetime.now() - startTime).total_seconds()
                    message += f' - {totalTime:<3.1f}s'
                    logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')
                else:
                    for fe in range(1,4):
                        totalTime = 0.0
                        s = requests.Session()
                        s.headers.update(ocsheaders)
                        for call in range(0,calls):
                            serverid = f'node{fe}.{nodebaseurl}'
                            s.cookies.set('SERVERID', serverid)
                            startTime = datetime.now()
                            r = s.get(url, headers=ocsheaders)
                            totalTime += (datetime.now() - startTime).total_seconds()
                        message += f' - {totalTime:<3.1f}s'
                        logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')


            if self.newSession:
                logger.info(f'Direct url(s), new session')
                if isMultinode:
                    info = 'Multinode url, new session'
                    totalTime = 0.0
                    url = drv.get_add_user_multinode_url(fullnode)
                    logger.info(f'Test direct call to {url}')

                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)

                    for call in range(0,calls):
                        s = requests.Session()
                        s.headers.update(ocsheaders)
                        startTime = datetime.now()
                        r = s.get(url, headers=ocsheaders, verify=False)
                        totalTime += (datetime.now() - startTime).total_seconds()
                    message += f' - {totalTime:<3.1f}s'
                    logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')
                
                else:
                    info = 'Full node fe urls, new session'
                    for fe in range(1,4):
                        totalTime = 0.0
                        url = drv.get_add_user_fe_url(fullnode, fe)
                        logger.info(f'Test direct call to {url}')

                        url = url.replace("$USERNAME$", nodeuser)
                        url = url.replace("$PASSWORD$", nodepwd)

                        for call in range(0,calls):
                            s = requests.Session()
                            s.headers.update(ocsheaders)
                            startTime = datetime.now()
                            r = s.get(url, headers=ocsheaders, verify=False)
                            totalTime += (datetime.now() - startTime).total_seconds()
                        message += f' - {totalTime:<3.1f}s'
                        logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')

            else: # Same session
                logger.info(f'Direct url(s), same session')
                if isMultinode:
                    info = 'Multinode url, same session'
                    totalTime = 0.0
                    s = requests.Session()
                    s.headers.update(ocsheaders)
                    url = drv.get_add_user_multinode_url(fullnode)
                    logger.info(f'Test direct call to {url}')

                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)

                    for call in range(0,calls):
                        startTime = datetime.now()
                        r = s.get(url, headers=ocsheaders, verify=False)
                        totalTime += (datetime.now() - startTime).total_seconds()
                    message += f' - {totalTime:<3.1f}s'
                    logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')
                else:
                    info = 'Full node fe urls, same session'
                    for fe in range(1,4):
                        totalTime = 0.0
                        s = requests.Session()
                        s.headers.update(ocsheaders)
                        url = drv.get_add_user_fe_url(fullnode, fe)
                        logger.info(f'Test direct call to {url}')

                        url = url.replace("$USERNAME$", nodeuser)
                        url = url.replace("$PASSWORD$", nodepwd)

                        for call in range(0,calls):
                            startTime = datetime.now()
                            r = s.get(url, headers=ocsheaders, verify=False)
                            totalTime += (datetime.now() - startTime).total_seconds()
                        message += f' - {totalTime:<3.1f}s'
                        logger.info(f'{calls} request to {serverid} took {totalTime:<3.1f}s - {info}')

            g_ocsPerformanceResults.append(message)
        except Exception as error:
            logger.error(f'{error}')
            g_testPassed[fullnode] = False
            g_testThreadsRunning -= 1
            return

        g_testPassed[fullnode] = True
        g_testThreadsRunning -= 1
        logger.info(f'NodeOcsUserPerformance thread done for node {self.name}, test passed: {g_testPassed[fullnode]}')
        return

class TestPerformanceOcs(unittest.TestCase):
    def test_performance_ocs_userlist_samesession(self):
        global g_ocsPerformanceResults
        g_ocsPerformanceResults.append(f'Result of test_performance_ocs_userlist_samesession')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                nodeUsersThread = NodeOcsUserPerformance(fullnode, self, newSession=False, verify=drv.verify)
                nodeUsersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

        logger.info(f'Result of test_performance_ocs_userlist_samesession')
        for message in g_ocsPerformanceResults:
            logger.info(f'{message}')

    def test_performance_ocs_userlist_newsession(self):
        global g_ocsPerformanceResults
        g_ocsPerformanceResults.append(f'Result of test_performance_ocs_userlist_newsession')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                nodeUsersThread = NodeOcsUserPerformance(fullnode, self, newSession=True, verify=drv.verify)
                nodeUsersThread.start()

        while(g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

        logger.info(f'Result of test_performance_ocs_userlist_newsession')
        for message in g_ocsPerformanceResults:
            logger.info(f'{message}')

    def test_performance_ocs_userlifecycle(self):
        global g_ocsPerformanceResults
        g_ocsPerformanceResults.append(f'Result of test_performance_ocs_userlifecycle')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')
                userLifecycleThread = NodeOcsUserLifecycle(fullnode)
                userLifecycleThread.start()

        while (g_testThreadsRunning > 0):
            time.sleep(1)

        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.assertTrue(g_testPassed[fullnode])

        logger.info(f'Result of test_performance_ocs_userlifecycle')
        for message in g_ocsPerformanceResults:
            logger.info(f'{message}')
                
if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-performance", add_timestamp=False))
