"""Prerequisite checks for the Sunet Drive test suite
Author: Richard Freitag <freitag@sunet.se>

Checks that the test configuration matches the deployed infrastructure
before the other tests run. The node lists of the test target and
expected.yaml are compared with the sunet-drive-ops repository
(common.yaml, cosmos-rules.yaml and the SAML metadata of the IdP
proxies), and the credentials needed by the other tests are checked
for every node.

Most mismatches are only logged as warnings or errors. Only missing
user credentials make a test fail.
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

common_config_file = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
cosmos_rules_file = opsbase + "/cosmos-rules.yaml"
drv = sunetnextcloud.TestTarget()

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class TestTests(unittest.TestCase):
    """Consistency checks between the test configuration and sunet-drive-ops."""
    global cosmos_rules
    def setUp(self):
        """Load the node lists from sunet-drive-ops.

        Reads common.yaml (full, single, multinode and project mapping nodes),
        the prod and test IdP proxy metadata directories and cosmos-rules.yaml
        (full node and multinode names). Missing files are logged as warnings.
        """
        if os.path.exists(common_config_file):
            with open(common_config_file, "r") as stream:
                data=yaml.safe_load(stream)
                # self.fullnodes = data['fullnodes']
                # self.singlenodes = data['singlenodes']
                self.allnodes=data['fullnodes'] + data['singlenodes']

                self.common_metadata_prodnodes = []
                self.common_metadata_testnodes = []
                self.common_multinode_mapping_nodes = []
                self.common_project_mapping_nodes = []
                self.common_fullnodes = data['fullnodes']
                self.common_singlenodes = data['singlenodes']
                self.common_full_and_single_nodes = self.common_fullnodes + self.common_singlenodes

                prod_dir = os.fsencode(f'{opsbase}idpproxy-prod-common/overlay/etc/satosa/metadata/')
                test_dir = os.fsencode(f'{opsbase}idpproxy-test-common/overlay/etc/satosa/metadata/')

                for file in os.listdir(prod_dir):
                    metadata_file = os.fsdecode(file)
                    self.common_metadata_prodnodes.append(metadata_file.replace('_saml_prod.xml', ''))
                for file in os.listdir(test_dir):
                    metadata_file = os.fsdecode(file)
                    self.common_metadata_testnodes.append(metadata_file.replace('_saml_test.xml', ''))

                for entry in data['multinode_mapping']:
                    logger.info(f'Add {entry} to multinode mapping')
                    self.common_multinode_mapping_nodes.append(entry)
                for entry in data['project_mapping']:
                    logger.info(f'Add {entry} to project mapping')
                    self.common_project_mapping_nodes.append(entry)

                self.common_metadata_prodnodes = sorted(self.common_metadata_prodnodes)
                self.common_metadata_testnodes = sorted(self.common_metadata_testnodes)
        else:
            logger.warning(f'Global config file not found at {common_config_file}')

        if os.path.exists(cosmos_rules_file):
            with open(cosmos_rules_file, "r") as stream:
                self.cosmos_rules=yaml.safe_load(stream)


                self.cosmos_fullnode_names = []
                self.cosmos_multinode_names = []

                # Extract full nodes and multinodes from cosmos rules
                for key, value in self.cosmos_rules.items():
                    if "node[" in key:
                        node_name = key.split(".")[1].replace("\\","")
                        if node_name not in self.cosmos_fullnode_names:
                            self.cosmos_fullnode_names.append(node_name)

                    if "multinode" in key:
                        # logger.info(f'Check sites for {key}')

                        if 'sunet::frontend::register_sites_array' in value.keys():
                            sites = value['sunet::frontend::register_sites_array']['sites']
                            for site in sites:
                                # Convert keys into a list to get first entry and split to get node name
                                node_name = list(site.keys())[0].split('.')[0]
                                if node_name not in self.cosmos_multinode_names:
                                    self.cosmos_multinode_names.append(node_name)

            logger.info(f'Cosmos rules loaded')
        else:
            logger.warning(f'Cosmos rules file not found at {cosmos_rules_file}')


    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_cosmos_mapping(self):
        """Warn about cosmos-rules.yaml nodes missing from common.yaml or expected.yaml.

        Checks both full nodes and multinodes. Only logs warnings; never fails.
        Skipped if common.yaml or cosmos-rules.yaml is not found.
        """
        logger.info(f'TestID: {self._testMethodName}')
        if not os.path.exists(common_config_file) or not os.path.exists(cosmos_rules_file):
            self.skipTest(f'{common_config_file} or {cosmos_rules_file} not found')
        logger.info(f'Test cosmos rules mapping')

        # Check if cosmos full nodes are mapped in common.yaml and expected.yaml
        for cosmos_fullnode in self.cosmos_fullnode_names:
            if cosmos_fullnode not in self.common_fullnodes:
                logger.warning(f'{cosmos_fullnode} full node in cosmos_rules, but not in common.yaml')
            if cosmos_fullnode not in drv.redundantnodes:
                logger.warning(f'{cosmos_fullnode} full node in cosmos_rules, but not in expected.yaml')

        for cosmos_multinode in self.cosmos_multinode_names:
            if cosmos_multinode not in self.common_multinode_mapping_nodes:
                logger.warning(f'{cosmos_multinode} multinode in cosmos_rules, but not in common.yaml')
            if cosmos_multinode not in drv.multinodes:
                logger.warning(f'{cosmos_multinode} multinode in cosmos_rules, but not in expected.yaml')

    def test_common_mapping(self):
        """Check the node mappings in common.yaml against the IdP proxy metadata.

        Warns about nodes with SAML metadata in only prod or only test. Logs an
        error for metadata nodes that are neither in the multinode mapping nor
        a full/single node, and for project mapping entries without metadata
        (except common, kau, scilifelab, sp and sics). Only logs; never fails.
        Skipped if common.yaml is not found.
        """
        logger.info(f'TestID: {self._testMethodName}')
        if not os.path.exists(common_config_file):
            self.skipTest(f'{common_config_file} not found')
        logger.info(f'Check if metadata nodes contain unusual nodes')

        if self.common_metadata_prodnodes != self.common_metadata_testnodes:
            for prodentry in self.common_metadata_prodnodes:
                if prodentry not in self.common_metadata_testnodes:
                    logger.warning(f'{prodentry} not found in list of test nodes')

            for testentry in self.common_metadata_testnodes:
                if testentry not in self.common_metadata_prodnodes:
                    logger.warning(f'{testentry} not found in list of prod nodes')
        # self.assertTrue(self.common_metadata_prodnodes == self.common_metadata_testnodes)

        for entry in self.common_metadata_prodnodes:
            if entry not in (self.common_multinode_mapping_nodes):
                if entry not in self.common_full_and_single_nodes:
                    logger.error(f'{entry} has metadata configuration, but is neither in multinode mapping nor configured as single/full node')

        logger.info(f'Check if project mapping nodes contain unusual nodes')
        for entry in self.common_project_mapping_nodes:
            if entry not in self.common_metadata_prodnodes:
                if entry not in ['common', 'kau', 'scilifelab', 'sp', 'sics']:
                    logger.error(f'{entry} configured in project mapping, but not as metadata node')

    def test_allnodes_tested(self):
        """Warn about differences between the configured and the tested nodes.

        Compares common.yaml with the nodes of the test target in both
        directions. Skipped when only one node is tested. Only logs warnings;
        never fails.
        """
        logger.info(f'TestID: {self._testMethodName}')
        testMissing = False

        if len(drv.nodestotest) == 1:
            logger.info(f'We are only testing single nodes: {drv.nodestotest}')
            testMissing = False

        if os.path.exists(common_config_file) and len(drv.nodestotest) != 1:
            logger.info('Check if we are testing all nodes')

            for configurednode in self.common_metadata_prodnodes:
                if configurednode not in drv.allnodes:
                    logger.warning(f'{configurednode} in common.yaml, but not tested!')

            for testnode in drv.allnodes:
                if testnode not in self.common_metadata_prodnodes:
                    logger.warning(f'{testnode} in tests, but not in common.yaml')

            for node in self.allnodes:
                if node not in drv.nodestotest:
                    logger.warning(f'{node} in common.yaml but not tested')

            for node in drv.nodestotest:
                if node not in self.allnodes:
                    logger.warning(f'{node} in tests but not in common.yaml')
        else:
            logger.info('Global config file not found, skipping test if all nodes are tested')

        self.assertFalse(testMissing)

    def test_required_usercredentials(self):
        """Check that all test user credentials are available for every node.

        Fails if the Selenium user, the Selenium MFA user or the OCS user is
        missing a username, password or app password, or if a Selenium user is
        missing its TOTP secret.
        """
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
                report_name=f"nextcloud-{drv.target}-{drv.expectedResults[drv.target]['status']['version'][-1]}-{os.path.basename(__file__)}",
                add_timestamp=False,
            )
        )
