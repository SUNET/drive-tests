""" Generate expected_localhost.yaml file
Author: Richard Freitag <freitag@sunet.se>
Read the expected_localhost_template.yaml file and replace the values with the values from the locally installed instance
"""
import yaml
import sunetnextcloud
import requests
import logging
import time
import sys
import json

g_requestTimeout=10
verify = False
node = 'localhost'
ocsheaders = { "OCS-APIRequest" : "true" } 

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

expectedResultsFile = 'expected_localhost_template.yaml'
with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

drv = sunetnextcloud.TestTarget()

# Set expected values from status.php
url = drv.get_status_url(node)
logger.info(f'Get status values from {url}')
try:
    r =requests.get(url, timeout=g_requestTimeout, verify=verify)
except Exception as error:
    logger.error(f'Error getting frontend status data from {url}: {error}')
    sys.exit(1)
try:
    j = json.loads(r.text)
    expectedResults[drv.target]['status']['version']        = j["version"]
    expectedResults[drv.target]['status']['versionstring']  = j["versionstring"]
    expectedResults[drv.target]['status']['edition']        = j["edition"]
    expectedResults[drv.target]['status']['productname']    = j["productname"]
    expectedResults[drv.target]['status']['extendedSupport']    = j["extendedSupport"]
    logger.info(f'Status information received from: {url}')
except Exception as error:
    logger.info(f'No valid JSON reply received for {url}: {error}')
    logger.info(r.text)
    sys.exit(1)

# Set expected values from ocs capabilities
url = drv.get_ocs_capabilities_url(node)
logger.info(f'Get status values from {url}')

try:
    r = requests.get(url, headers=ocsheaders, timeout=g_requestTimeout, verify=verify)
except Exception as error:
    logger.error(f'Error getting {url}: {error}')
    sys.exit(1)
try:
    j = json.loads(r.text)
except Exception as error:
    logger.info(f"No JSON reply received from {node}: {error}")
    logger.info(r.text)
    sys.exit(1)

try:
    expectedResults[drv.target]['ocs_capabilities']['ocs_meta_status']          = j["ocs"]["meta"]["status"]
    expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode']      = 100
    expectedResults[drv.target]['ocs_capabilities']['ocs_meta_statuscode_2']    = j["ocs"]["meta"]["statuscode"]
    expectedResults[drv.target]['ocs_capabilities']['ocs_meta_message']         = j["ocs"]["meta"]["message"]
    expectedResults[drv.target]['ocs_capabilities']['ocs_data_version_string']  = j["ocs"]["data"]["version"]["string"]
except Exception as error:
    logger.error(f"Error with OCS capabilities assertion: {error}")
    sys.exit(1)

with open('expected_localhost.yaml', 'w') as outfile:
    yaml.dump(expectedResults, outfile, default_flow_style=False)
