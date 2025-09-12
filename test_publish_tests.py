""" Unit tests to make ensure some prerequisites for testing
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import os
import subprocess

import sunetnextcloud
import logging
import junit2htmlreport

# Change to local directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

opsbase='sunet-drive-ops/'
xmlout='test-reports/archive'
htmlout='html-reports/archive'
os.makedirs(xmlout, exist_ok=True)
os.makedirs(htmlout, exist_ok=True)

drv = sunetnextcloud.TestTarget()

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

class TestTests(unittest.TestCase):
    def test_logger(self):
        logger.info(f'TestID: {self._testMethodName}')
        pass

    def test_publish(self):
        job_name = os.environ.get('JOB_NAME')
        if job_name is None:
            job_name = 'None'

        merge_cmd = f'junit2html "test-reports/*.xml" --merge "html-reports/latest.xml"'
        make_html_cmd = f'junit2html "html-reports/latest.xml" "html-reports/latest.html"'
        upload_cmd = f'rclone copy -P html-reports/latest.html "testautomation:testautomation/results/{drv.target}/{job_name}"'

        logger.info(merge_cmd)
        subprocess.call(merge_cmd, shell=True)
        logger.info(make_html_cmd)
        subprocess.call(make_html_cmd, shell=True)
        logger.info(upload_cmd)
        subprocess.call(upload_cmd, shell=True)

if __name__ == '__main__':
    drv.run_tests(os.path.basename(__file__))
    