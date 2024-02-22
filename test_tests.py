""" Unit tests to make ensure some prerequisites for testing
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import yaml
import os

import sunetnextcloud
import logging

opsbase='sunet-drive-ops/'
globalconfigfile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"

class TestTests(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_allnodes_tested(self):
        self.logger.info(f'{self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        # print(len(drv.fullnodes))

        testMissing = False
        if os.path.exists(globalconfigfile):
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
            self.logger.info(f'Global config file not found, skipping test if all nodes are tested')

        self.assertFalse(testMissing)

    # Ensure user credentials to execute tests are available
    def test_required_usercredentials(self):
        self.logger.info(f'{self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_ocs_capabilities_url(fullnode)
                # print(self._testMethodName, url)
                ocsuser = drv.get_ocsuser(fullnode)
                if ocsuser is None:
                    ocsuser = ''
                ocsuserpwd = drv.get_ocsuserpassword(fullnode)
                if ocsuserpwd is None:
                    ocsuserpwd = ''
                seleniumuser = drv.get_seleniumuser(fullnode)
                if seleniumuser is None:
                    seleniumuser = ''
                seleniumuserpwd = drv.get_seleniumuserpassword(fullnode)
                if seleniumuserpwd is None:
                    seleniumuserpwd = ''
                seleniumuserapppwd = drv.get_seleniumuserapppassword(fullnode)
                if seleniumuserapppwd is None:
                    seleniumuserapppwd = ''

                # print(len(nodeuser))
                # print(len(nodepwd))

                self.assertGreater(len(ocsuser), 0)
                self.assertGreater(len(ocsuserpwd), 0)
                self.assertGreater(len(seleniumuser), 0)
                self.assertGreater(len(seleniumuserpwd), 0)
                self.assertGreater(len(seleniumuserapppwd), 0)

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
