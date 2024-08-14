""" Performance test create, disable, delete user
Author: Richard Freitag <freitag@sunet.se>
"""

import xmlrunner
import unittest
import requests
from requests.auth import HTTPBasicAuth
import json
import logging
import os
import time

import sunetnextcloud

nodes = 1
users = 25
offset = 0
createusers=True
deleteusers=True
disableusers=True

# g_testtarget = 'test'
# drv = sunetnextcloud.TestTarget(g_testtarget)

ocsheaders = { "OCS-APIRequest" : "true" } 

class TestPerformanceOcs(unittest.TestCase):

    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_performance_userlifecycle(self):
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_add_user_url(fullnode)
                # self.logger.info(self._testMethodName, url)
                for nodeindex in range(1, nodes+1):
                    self.logger.info(f'Node: {str(nodeindex)}')

                    for userindex in range(offset, offset+users+1):
                        self.logger.info(f'{drv.target} - User: {str(userindex)}')
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
                            # self.logger.info(json.dumps(j, indent=4, sort_keys=True))
                            self.logger.info(j["ocs"]["meta"]["status"])

                        if (disableusers==True):
                            self.logger.info("Disable cli user " + cliuser)
                            disableuserurl = drv.get_disable_user_url(fullnode, cliuser)
                            disableuserurl = disableuserurl.replace("$USERNAME$", nodeuser)
                            disableuserurl = disableuserurl.replace("$PASSWORD$", nodepwd)
                            r = requests.put(disableuserurl, headers=ocsheaders)
                            j = json.loads(r.text)
                            self.logger.info(j["ocs"]["meta"]["status"])
                            # self.logger.info(json.dumps(j, indent=4, sort_keys=True))

                        if (deleteusers==True):
                            self.logger.info("Delete cli user " + cliuser)
                            userurl = drv.get_user_url(fullnode, cliuser)
                            userurl = userurl.replace("$USERNAME$", nodeuser)
                            userurl = userurl.replace("$PASSWORD$", nodepwd)
                            r = requests.delete(userurl, headers=ocsheaders)
                            j = json.loads(r.text)
                            self.logger.info(j["ocs"]["meta"]["status"])
                
if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
