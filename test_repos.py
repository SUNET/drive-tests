""" Unit tests that can be run against other Sunet Drive repos for cross-verification
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import yaml

import sunetnextcloud
import os
import logging
import filecmp

opsbase='sunet-drive-ops/'
puppetbase='drive-puppet/'

puppetfile = './drive-puppet/templates/application/mappingfile-' + os.environ.get('NextcloudTestTarget') + '.json.erb'
referencefile = './mappingfile-' + os.environ.get('NextcloudTestTarget') + '.json'

class TestRepos(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info('self.logger.info test_logger')
        pass

    # Ensure that the mapping files are the same as the reference files
    def test_mappingfiles(self):
        self.logger.info(f'{self._testMethodName}')
        sunetnextcloud.TestTarget()
        self.assertTrue(filecmp.cmp(puppetfile, referencefile))

    def test_allnodes_tested(self):
        self.logger.info(f'{self._testMethodName}')
        drv = sunetnextcloud.TestTarget()
        # print(len(drv.nodestotest))

        testMissing = False
        # testWrongNode = False
        globalconfigfile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
        with open(globalconfigfile, "r") as stream:
            data=yaml.safe_load(stream)
            allnodes=data['fullnodes'] + data['singlenodes']

            for node in allnodes:
                if node not in drv.nodestotest:
                    print(f'{node} in common.yaml but not tested')

            for node in drv.nodestotest:
                if node not in allnodes:
                    print(f'{node} in tests but not in common.yaml')


        self.assertFalse(testMissing)

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
