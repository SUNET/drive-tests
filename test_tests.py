""" Unit tests to make ensure some prerequisites for testing
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import yaml
import os
import time

import sunetnextcloud
import logging
import xmlrunner
import HtmlTestRunner

# Change to local directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

opsbase='sunet-drive-ops/'
xmlout='test-reports/archive'
htmlout='html-reports/archive'
os.makedirs(xmlout, exist_ok=True)
os.makedirs(htmlout, exist_ok=True)

globalconfigfile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
drv = sunetnextcloud.TestTarget()

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class TestTests(unittest.TestCase):
    if os.path.exists(globalconfigfile):
        with open(globalconfigfile, "r") as stream:
            data=yaml.safe_load(stream)
            allnodes=data['fullnodes'] + data['singlenodes']

            common_metadata_prodnodes = []
            common_metadata_testnodes = []
            common_multinode_mapping_nodes = []
            common_project_mapping_nodes = []
            common_fullnodes = data['fullnodes']
            common_singlenodes = data['singlenodes']
            common_full_and_single_nodes = common_fullnodes + common_singlenodes

            for entry in data['drive_metadata_files']:
                if '_saml_prod' in entry:
                    common_metadata_prodnodes.append(entry.replace('_saml_prod', ''))
                elif '_saml_test' in entry:
                    common_metadata_testnodes.append(entry.replace('_saml_test', ''))
            for entry in data['multinode_mapping']:
                common_multinode_mapping_nodes.append(entry)
            for entry in data['project_mapping']:
                common_project_mapping_nodes.append(entry)

            common_metadata_prodnodes = sorted(common_metadata_prodnodes)
            common_metadata_testnodes = sorted(common_metadata_testnodes)

    def test_logger(self):
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_common_mapping(self):
        logger.info(f'TestID: {self._testMethodName}')
        logger.info(f'Check if metadata nodes contain unusual nodes')

        self.assertTrue(self.common_metadata_prodnodes == self.common_metadata_testnodes)

        for entry in self.common_metadata_prodnodes:
            if entry not in (self.common_multinode_mapping_nodes):
                if entry not in self.common_full_and_single_nodes:
                    logger.error(f'{entry} has metadata configuration, but is neither in multinode mapping nor configured as single/full node')

        logger.info(f'Check if project mapping nodes contain unusual nodes')
        for entry in self.common_project_mapping_nodes:
            if entry not in self.common_metadata_prodnodes:
                # Check for exceptions
                if entry not in ['common', 'kau', 'scilifelab']:
                    logger.error(f'{entry} configured in project mapping, but not as metadata node')

    def test_allnodes_tested(self):
        logger.info(f'TestID: {self._testMethodName}')
        testMissing = False

        if len(drv.nodestotest) == 1:
            logger.info(f'We are only testing single nodes: {drv.nodestotest}')
            testMissing = False

        if os.path.exists(globalconfigfile) and len(drv.nodestotest) != 1:
            logger.info('Check if we are testing all nodes')


            with open(globalconfigfile, "r") as stream:
                data=yaml.safe_load(stream)
                allnodes=data['fullnodes'] + data['singlenodes']

                for configurednode in self.common_metadata_prodnodes:
                    if configurednode not in drv.allnodes:
                        logger.error(f'{configurednode} in common.yaml, but not tested!')

                for testnode in drv.allnodes:
                    if testnode not in self.common_metadata_prodnodes:
                        logger.error(f'{testnode} in tests, but not in common.yaml')

                for node in allnodes:
                    if node not in drv.nodestotest:
                        logger.warning(f'{node} in common.yaml but not tested')

                for node in drv.nodestotest:
                    if node not in allnodes:
                        logger.warning(f'{node} in tests but not in common.yaml')
        else:
            logger.info('Global config file not found, skipping test if all nodes are tested')

        self.assertFalse(testMissing)

    # Ensure user credentials to execute tests are available
    def test_required_usercredentials(self):
        logger.info(f'{self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        test_failed = False
        for fullnode in drv.allnodes:
            with self.subTest(mynode=fullnode):
                logger.info(f'TestID: {fullnode}')

                seleniumuser = drv.get_seleniumuser(fullnode, False)
                seleniumuserpwd = drv.get_seleniumuserpassword(fullnode, False)
                seleniumuserapppwd = drv.get_seleniumuserapppassword(fullnode, False)
                seleniumusertotpsecret = drv.get_seleniumusertotpsecret(fullnode, False)

                seleniummfauser = drv.get_seleniummfauser(fullnode, False)
                seleniummfauserpwd = drv.get_seleniummfauserpassword(fullnode, False)
                seleniummfauserapppwd = drv.get_seleniummfauserapppassword(fullnode, False)
                seleniummfausertotpsecret = drv.get_seleniummfausertotpsecret(fullnode, False)

                ocsuser = drv.get_ocsuser(fullnode, False)
                ocsuserpwd = drv.get_ocsuserpassword(fullnode, False)
                ocsuserapppwd = drv.get_ocsuserapppassword(fullnode, False)

                if seleniumuser is None:
                    test_failed = True
                if seleniumuserpwd is None:
                    test_failed = True
                if seleniumuserapppwd is None:
                    test_failed = True
                if seleniumusertotpsecret is None:
                    test_failed = True
                if seleniummfauser is None:
                    test_failed = True
                if seleniummfauserpwd is None:
                    test_failed = True
                if seleniummfauserapppwd is None:
                    test_failed = True
                if seleniummfausertotpsecret is None:
                    test_failed = True
                if ocsuser is None:
                    test_failed = True
                if ocsuserpwd is None:
                    test_failed = True
                if ocsuserapppwd is None:
                    test_failed = True

        self.assertFalse(test_failed)

if __name__ == '__main__':
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
                report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version'][-1]}-tests",
                add_timestamp=False,
            )
        )
