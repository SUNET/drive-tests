""" Unit tests to make ensure some prerequisites for testing
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import yaml

import sunetdrive
import os
import filecmp

opsbase='sunet-drive-ops/'
puppetbase='drive-puppet/'

puppetfile = './drive-puppet/templates/application/mappingfile-' + os.environ.get('DriveTestTarget') + '.json.erb'
referencefile = './mappingfile-' + os.environ.get('DriveTestTarget') + '.json'

class TestTests(unittest.TestCase):
    # Ensure that the mapping files are the same as the reference files
    def test_mappingfiles(self):
        drv = sunetdrive.TestTarget()
        self.assertTrue(filecmp.cmp(puppetfile, referencefile))

    def test_allnodes_tested(self):
        drv = sunetdrive.TestTarget()
        # print(len(drv.fullnodes))

        testMissing = False
        testWrongNode = False
        globalconfigfile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
        with open(globalconfigfile, "r") as stream:
            data=yaml.safe_load(stream)
            allnodes=data['fullnodes'] + data['singlenodes']

            for node in allnodes:
                if node not in drv.fullnodes:
                    print(f'{node} in common.yaml but not tested')

            for node in drv.fullnodes:
                if node not in allnodes:
                    print(f'{node} in tests but not in common.yaml')


        self.assertFalse(testMissing)

    # Ensure user credentials to execute tests are available
    def test_required_usercredentials(self):
        drv = sunetdrive.TestTarget()
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
