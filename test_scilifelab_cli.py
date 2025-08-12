""" Command line unit tests for Sunet Drive, testing status pages and information
Author: Richard Freitag <freitag@sunet.se>
Simple test for retrieving all status.php pages from Sunet Drive nodes and comparing the output to the expected result.
"""

import unittest
import requests
import logging
from xml.etree.ElementTree import fromstring

import sunetnextcloud

class TestSciLifeLabCli(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

    def test_logger(self):
        self.logger.info('self.logger.info test_logger')
        pass

    def test_metadata(self):
        node = 'scilifelab'
        drv = sunetnextcloud.TestTarget()
        expectedEntityId = ''
        url = drv.get_metadata_url(node)
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
        except:
            self.logger.error('Metadata is not valid XML')

        self.assertEqual(expectedEntityId, drv.get_node_entity_id(node))
        self.logger.info('GSS metadata test done')

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
