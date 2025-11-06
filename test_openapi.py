"""Testing OpenAPI calls for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import xmlrunner
import logging
import json
import requests
import time

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
expectedResults = drv.expectedResults


ocsheaders = {"OCS-APIRequest": "true"}
openApiSource = f"resources/nextcloud/document{expectedResults[drv.target]['status']['major_version']}.json"
logger = sunetnextcloud.logger
g_requestTimeout = 10


class TestOpenApi(unittest.TestCase):
    def test_logger(self):
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_load_openapi(self):
        with open(openApiSource) as f:
            openApiSpec = json.load(f)
            # print(json.dumps(openApiSpec, indent=4, sort_keys=True))
        pass

    def test_path_get(self):
        with open(openApiSource) as f:
            openApiSpec = json.load(f)

        logger.info(
            f"Testing {openApiSpec['info']['title']} - {openApiSpec['info']['description']} - {openApiSpec['info']['version']}"
        )

        failedFunctions = {}
        return_json = True
        for path in openApiSpec["paths"]:
            # logger.info(path)
            fullnode = "sunet"
            for method in openApiSpec["paths"][path].keys():
                if method == "get":
                    logger.info(f"Get found for {path}")
                    cleanUrl = drv.get_openapi_url(
                        fullnode, path, return_json=return_json
                    )
                    secretUrl = cleanUrl
                    logger.info(f"Clean url: {cleanUrl}")

                    if "{" in cleanUrl:
                        logger.info(f"Skip parametrized get: {cleanUrl}")
                        continue

                    try:
                        nodeuser = drv.get_ocsuser(fullnode)
                        nodepwd = drv.get_ocsuserapppassword(fullnode)
                        secretUrl = secretUrl.replace("$USERNAME$", nodeuser)
                        secretUrl = secretUrl.replace("$PASSWORD$", nodepwd)

                        r = requests.get(
                            secretUrl,
                            headers=ocsheaders,
                            timeout=g_requestTimeout,
                        )
                        if return_json:
                            j = json.loads(r.text)
                            logger.info(f"Called get on {cleanUrl}")

                            if j["ocs"]["meta"]["statuscode"] != 200:
                                failedFunctions[cleanUrl] = j["ocs"]["meta"][
                                    "statuscode"
                                ]
                                print(json.dumps(j, indent=4, sort_keys=True))
                            else:
                                logger.info(f"Good call on {cleanUrl}")

                        if (
                            return_json and j["ocs"]["meta"]["statuscode"] >= 500
                        ):  # Get reply from non-json call
                            cleanUrl = drv.get_openapi_url(
                                fullnode, path, return_json=False
                            )
                            secretUrl = cleanUrl
                            logger.warning(
                                f"Retry non-json call to {cleanUrl} due to {j['ocs']['meta']['statuscode']}"
                            )
                            secretUrl = secretUrl.replace("$USERNAME$", nodeuser)
                            secretUrl = secretUrl.replace("$PASSWORD$", nodepwd)

                            r = requests.get(
                                secretUrl,
                                headers=ocsheaders,
                                timeout=g_requestTimeout,
                            )
                            logger.warning(f"Non-json reply to {cleanUrl}: {r.text}")
                        else:
                            logger.info(f"Good call on {cleanUrl}")

                            # if "997" in r.text:
                            #     logger.error(f"Bad call on {cleanUrl}")
                            #     logger.error(f"{r.text}")
                            #     failedFunctions[cleanUrl] = "997"
                            # else:
                            #     logger.info(f"Good call on {cleanUrl}")
                            # logger.info(f"Returned: {r.text}")
                    except Exception as error:
                        logger.error(f"Error calling get from {cleanUrl}: {error}")
                        failedFunctions[cleanUrl] = error

        logger.info(f"Done with {len(failedFunctions)} errors")
        for failedFunction in failedFunctions:
            logger.info(f"{failedFunction} - {failedFunctions.get(failedFunction)}")
        pass


if __name__ == "__main__":
    if drv.testrunner == "xml":
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output="test-reports"))
    else:
        unittest.main(
            testRunner=HtmlTestRunner.HTMLTestRunner(
                output="test-reports-html",
                combine_reports=True,
                report_name=f"nextcloud-{drv.expectedResults[drv.target]['status']['version']}-userlifecycle",
                add_timestamp=False,
            )
        )
