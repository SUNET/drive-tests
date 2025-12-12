"""Unit tests to cross-check Sunet Drive nodes between SWAMID, common.yaml, and expected.yaml
Author: Richard Freitag <freitag@sunet.se>
"""

import logging
import os
import unittest

import requests
import yaml

import sunetnextcloud

# Change to local directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

opsbase = "sunet-drive-ops/"
xmlout = "test-reports/archive"
htmlout = "html-reports/archive"
swamidUrl = "https://metadata.swamid.se/?show=IdP"

os.makedirs(xmlout, exist_ok=True)
os.makedirs(htmlout, exist_ok=True)

swamidinstances = []
commoninstances = []

globalconfigfile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
drv = sunetnextcloud.TestTarget()

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def get_common_instances():
    global commoninstances
    logger.info(f"Get instances from common.yaml")
    with open(globalconfigfile, "r") as stream:
        data = yaml.safe_load(stream)
        commoninstances = data["fullnodes"] + data["singlenodes"]
        for entry in data["drive_metadata_files"]:
            instance = entry[: entry.find("_")]
            if instance not in commoninstances:
                commoninstances.append(instance)

        for entry in data["multinode_mapping"]:
            if entry not in commoninstances:
                commoninstances.append(entry)


def get_swamid_instances():
    global swamidinstances
    logger.info(f"Get instances from SWAMID")
    r = requests.get(swamidUrl)
    if r.status_code != 200:
        self.assertTrue(False)

    numIdps = 0
    for line in r.text.splitlines():
        if ".?showEntity=" in line:
            idpUrl = line
            startIndex = line.find("http")
            idpUrl = line[startIndex:]
            idpUrl = idpUrl.replace("</span></a></td>", "")
            numIdps += 1

            # Check if the idp is eduid or eduid connect
            if "eduid.se" in idpUrl:
                if "connect.eduid.se" in idpUrl:
                    instanceName = idpUrl.replace("https://connect.eduid.se/", "")
                    swamidinstances.append(instanceName)

            # Check other idps
            else:
                # All domains are .se except for nordu.net, which makes it easier to find the tld
                tldIndex = idpUrl.find(".se")

                # Exception for nordunet
                if tldIndex == -1 and idpUrl.find(".net"):
                    instanceName = idpUrl[: idpUrl.find(".net") + 4]
                    instanceName = instanceName.replace(".net", "net")
                # Otherwise, we just remove everything after and including the .se
                else:
                    instanceName = idpUrl[:tldIndex]

                while instanceName.count(".") > 0:
                    instanceName = instanceName[instanceName.find(".") + 1 :]
                swamidinstances.append(instanceName)


get_common_instances()
get_swamid_instances()


class TestIdpMapping(unittest.TestCase):
    def test_logger(self):
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_instancemapping(self):
        logger.info(f"TestID: {self._testMethodName}")
        for commoninstance in commoninstances:
            if (
                commoninstance not in swamidinstances
                and commoninstance not in drv.aliasnodes
            ):
                logger.warning(
                    f"Common instance {commoninstance} not found in SWAMID instances"
                )

            if (
                commoninstance not in drv.allnodes
                and commoninstance not in drv.aliasnodes
            ):
                logger.warning(
                    f"Common instance {commoninstance} not found in text expected.yaml"
                )

        for swamidinstance in swamidinstances:
            if (
                swamidinstance not in commoninstances
                and swamidinstance not in drv.aliasnodes
            ):
                logger.warning(
                    f"SWAMID instance {swamidinstance} not found in common.yaml {swamidinstance in commoninstances}"
                )
            if (
                swamidinstance not in drv.allnodes
                and swamidinstance not in drv.aliasnodes
            ):
                logger.warning(
                    f"SWAMID instance {swamidinstance} not found in test expected.yaml"
                )

        for testinstance in drv.allnodes:
            if (
                testinstance not in swamidinstances
                and testinstance not in drv.aliasnodes
            ):
                logger.warning(f"Testinstance {testinstance} not in SWAMID instances")
            if (
                testinstance not in commoninstances
                and testinstance not in drv.aliasnodes
            ):
                logger.warning(f"Testinstance {testinstance} not in common.yaml")


if __name__ == "__main__":
    drv.run_tests(os.path.basename(__file__))
