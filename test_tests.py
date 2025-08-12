""" Unit tests to make ensure some prerequisites for testing
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import yaml
import os

import sunetnextcloud
import logging
import xmlrunner
import HtmlTestRunner

opsbase='sunet-drive-ops/'
globalconfigfile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
drv = sunetnextcloud.TestTarget()

class TestTests(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_allnodes_tested(self):
        self.logger.info(f'TestID: {self._testMethodName}')
        # print(len(drv.fullnodes))
        testMissing = False

        if drv.singlenodetesting == True:
            self.logger.info(f'We are only testing single nodes: {drv.allnodes}')
            testMissing = False

        if os.path.exists(globalconfigfile) and drv.singlenodetesting == False:
            self.logger.info('Check if we are testing all nodes')
            with open(globalconfigfile, "r") as stream:
                data=yaml.safe_load(stream)
                allnodes=data['fullnodes'] + data['singlenodes']

                for node in allnodes:
                    if node not in drv.fullnodes:
                        self.logger.error(f'{node} in common.yaml but not tested')
                        testMissing = True

                for node in drv.fullnodes:
                    if node not in allnodes:
                        self.logger.error(f'{node} in tests but not in common.yaml')
                        testMissing = True
        else:
            self.logger.info('Global config file not found, skipping test if all nodes are tested')

        self.assertFalse(testMissing)

    # Ensure user credentials to execute tests are available
    def test_required_usercredentials(self):
        self.logger.info(f'{self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        test_failed = False
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                self.logger.info(f'TestID: {fullnode}')
                ocsuser = drv.get_ocsuser(fullnode, False)
                ocsuserpwd = drv.get_ocsuserpassword(fullnode, False)
                ocsuserapppwd = drv.get_ocsuserapppassword(fullnode, False)
                seleniumuser = drv.get_seleniumuser(fullnode, False)
                seleniumuserpwd = drv.get_seleniumuserpassword(fullnode, False)
                seleniumuserapppwd = drv.get_seleniumuserapppassword(fullnode, False)
                seleniummfauser = drv.get_seleniummfauser(fullnode, False)
                seleniummfauserpwd = drv.get_seleniummfauserpassword(fullnode, False)
                seleniummfauserapppwd = drv.get_seleniummfauserapppassword(fullnode, False)
                seleniummfausertotpsecret = drv.get_seleniummfausertotpsecret(fullnode, False)

                if ocsuser is None:
                    test_failed = True
                if ocsuserpwd is None:
                    test_failed = True
                if ocsuserapppwd is None:
                    test_failed = True
                if seleniumuser is None:
                    test_failed = True
                if seleniumuserpwd is None:
                    test_failed = True
                if seleniumuserapppwd is None:
                    test_failed = True
                if seleniummfauser is None:
                    test_failed = True
                if seleniummfauserpwd is None:
                    test_failed = True
                if seleniummfauserapppwd is None:
                    test_failed = True
                if seleniummfausertotpsecret is None:
                    test_failed = True

        self.assertFalse(test_failed)

if __name__ == '__main__':
    if drv.testrunner == 'xml':
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
    else:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='test-reports-html', combine_reports=True, report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-acceptance", add_timestamp=False))
