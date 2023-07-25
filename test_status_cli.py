""" Command line unit tests for Sunet Drive, testing status pages and information
Author: Richard Freitag <freitag@sunet.se>
Simple test for retrieving all status.php pages from Sunet Drive nodes and comparing the output to the expected result.
"""

import unittest
import requests
import json
import logging
import hashlib
from xml.etree.ElementTree import XML, fromstring
import xmltodict

import sunetdrive
import os

class TestStatus(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info(f'self.logger.info test_logger')
        pass

    def test_status_gss(self):
        drv = sunetdrive.TestTarget()
        url = drv.get_gss_url()
        print(self._testMethodName, url)
        r=requests.get(url)
        self.assertEqual(r.status_code, 200)
        self.logger.info(f'GSS Status tested')

    def test_statusinfo_gss(self):
        drv = sunetdrive.TestTarget()
        if drv.target == 'prod':
            statusResult = sunetdrive.StatusResultGss()
        else:
            statusResult = sunetdrive.StatusResultGssTest()
        url=drv.get_gss_url() + "/status.php"
        print(self._testMethodName, url)
        r =requests.get(url)
        j = json.loads(r.text)
        self.assertEqual(j["maintenance"], statusResult.maintenance)
        self.assertEqual(j["needsDbUpgrade"], statusResult.needsDbUpgrade)
        self.assertEqual(j["version"], statusResult.version)
        self.assertEqual(j["versionstring"], statusResult.versionstring)
        self.assertEqual(j["edition"], statusResult.edition)
        # self.assertEqual(j["productname"], statusResult.productname)
        self.assertEqual(j["extendedSupport"], statusResult.extendedSupport)
        self.logger.info(f'GSS Status information tested')

    def test_status(self):
        drv = sunetdrive.TestTarget()
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                r=requests.get(url)
                self.assertEqual(r.status_code, 200)
                self.logger.info(f'Status tested: {url}')


    def test_statusinfo(self):
        drv = sunetdrive.TestTarget()
        if drv.target == 'prod':
            statusResult = sunetdrive.StatusResult()
        else:
            statusResult = sunetdrive.StatusResultTest()
        for url in drv.get_allnode_status_urls():
            with self.subTest(myurl=url):
                r =requests.get(url)
                j = json.loads(r.text)
                self.assertEqual(j["maintenance"], statusResult.maintenance)
                self.assertEqual(j["needsDbUpgrade"], statusResult.needsDbUpgrade)
                self.assertEqual(j["version"], statusResult.version)
                self.assertEqual(j["versionstring"], statusResult.versionstring)
                self.assertEqual(j["edition"], statusResult.edition)
                # self.assertEqual(j["productname"], statusResult.productname)
                self.assertEqual(j["extendedSupport"], statusResult.extendedSupport)
                self.logger.info(f'Status information tested: {url}')

    def test_metadata_gss(self):
        drv = sunetdrive.TestTarget()
        url = drv.get_gss_metadata_url()
        expectedEntityId = ''
        certMd5 = ''
        self.logger.info(f'Verify metadata for {url}')
        r = requests.get(url)

        try:
            metadataXml = fromstring(r.text)
            items = metadataXml.items()
            for item in items:
                name = item[0]
                if name == 'entityID':
                    expectedEntityId = item[1]
                    self.logger.info("entityID checked")

            metadataDict = xmltodict.parse(r.text)
            jsonString = json.dumps(metadataDict)
            j = json.loads(jsonString)
            certString = j["md:EntityDescriptor"]["md:SPSSODescriptor"]["md:KeyDescriptor"]["ds:KeyInfo"]["ds:X509Data"]["ds:X509Certificate"]
            certMd5 = hashlib.md5(certString.encode('utf-8')).hexdigest()

            if drv.target == 'prod':
                metadataResult = sunetdrive.GssMetadataResult()
            else:
                metadataResult = sunetdrive.GssMetadataResultTest()
        except:
            self.logger.error(f'Metadata is not valid XML')

        self.assertEqual(expectedEntityId, drv.get_gss_entity_id())
        self.assertEqual(metadataResult.certMd5, certMd5)
        self.logger.info(f'GSS metadata test done')

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
