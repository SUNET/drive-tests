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

        allPaths = {}
        testedPaths = {}
        failedPaths = {}
        return_json = True
        add_required_parameters = True

        for path in openApiSpec["paths"]:
            # logger.info(path)
            fullnode = "sunet"
            for method in openApiSpec["paths"][path].keys():
                allPaths[
                    drv.get_openapi_url(fullnode, path, return_json=return_json)
                ] = method

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

                    # Check if we require additional parameters
                    requireParameters = False
                    requireSecurity = True
                    customHeader = ocsheaders

                    if "security" not in openApiSpec["paths"][path]["get"]:
                        logger.info(f"{method} does not require security")
                        requireSecurity = False

                    parameterSuffix = ""  # url parameter suffix for functions requiring additional input
                    if "parameters" not in openApiSpec["paths"][path]["get"]:
                        logger.info(f"{path} does not require additional parameters")
                        customHeader = {}
                    else:
                        for parameter in openApiSpec["paths"][path]["get"][
                            "parameters"
                        ]:
                            # OCS-APIRequest is always required, so we skip this
                            if parameter["name"] == "OCS-APIRequest":
                                continue

                            # Check if other parameters are required
                            try:
                                requireParameters = parameter["required"]
                            except:
                                requireParameters = False

                            # Add required (empty) parameters
                            if requireParameters:
                                logger.info(
                                    f"Adding required header: {parameter['name']}"
                                )
                                parameterSuffix = f"{parameterSuffix}&{parameter['name']}=testautomation"
                                # customHeader[parameter["name"]] = "testautomation"
                                # logger.info(f"Call with custom header: {customHeader}")

                    try:
                        nodeuser = drv.get_ocsuser(fullnode)
                        nodepwd = drv.get_ocsuserapppassword(fullnode)
                        if requireSecurity:
                            secretUrl = secretUrl.replace("$USERNAME$", nodeuser)
                            secretUrl = secretUrl.replace("$PASSWORD$", nodepwd)
                        else:  # remove username and password call if it is not required
                            secretUrl = secretUrl.replace("$USERNAME$:$PASSWORD$@", "")

                        # Only add parameters if it is configured to do so
                        if add_required_parameters:
                            secretUrl = f"{secretUrl}{parameterSuffix}"
                            cleanUrl = f"{cleanUrl}{parameterSuffix}"

                        r = requests.get(
                            secretUrl,
                            headers=customHeader,
                            timeout=g_requestTimeout,
                        )
                        testedPaths[cleanUrl] = "Failed"

                        if return_json:
                            j = json.loads(r.text)
                            logger.info(f"Called get on {cleanUrl}")

                            if "ocs" in cleanUrl:
                                if j["ocs"]["meta"]["statuscode"] != 200:
                                    failedPaths[cleanUrl] = j["ocs"]["meta"][
                                        "statuscode"
                                    ]
                                    logger.error(
                                        json.dumps(j, indent=4, sort_keys=True)
                                    )
                                else:
                                    logger.info(f"Good call on {cleanUrl}")
                                    testedPaths[cleanUrl] = "Passed"

                            else:
                                logger.info(
                                    f"Non-ocs method {cleanUrl} returned {json.dumps(j, indent=4, sort_keys=True)}"
                                )
                        if (
                            "ocs" in cleanUrl
                            and return_json
                            and j["ocs"]["meta"]["statuscode"] >= 500
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
                            # Replace the first & of the parameter suffix with a ?
                            # Do so only  if we want to test with added parameters
                            if len(parameterSuffix) > 0 and add_required_parameters:
                                parameterSuffix = parameterSuffix.replace("&", "?", 1)
                                secretUrl = f"{secretUrl}{parameterSuffix}"
                                cleanUrl = f"{cleanUrl}{parameterSuffix}"

                            r = requests.get(
                                secretUrl,
                                headers=ocsheaders,
                                timeout=g_requestTimeout,
                            )
                            logger.warning(f"Non-json reply to {cleanUrl}: {r.text}")
                            failedPaths[cleanUrl] = f"Non-json reply: {len(r.text)}"
                        else:
                            logger.info(f"Good call on {cleanUrl}")
                            testedPaths[cleanUrl] = "Passed"

                    except Exception as error:
                        logger.error(f"Error calling get from {cleanUrl}: {error}")
                        failedPaths[cleanUrl] = error

                        if return_json:
                            logger.warning(
                                f"Retry non-json call to {cleanUrl} due to {error}"
                            )

                            cleanUrl = drv.get_openapi_url(
                                fullnode, path, return_json=False
                            )
                            secretUrl = cleanUrl
                            secretUrl = secretUrl.replace("$USERNAME$", nodeuser)
                            secretUrl = secretUrl.replace("$PASSWORD$", nodepwd)
                            # Replace the first & of the parameter suffix with a ?
                            if len(parameterSuffix) > 0:
                                parameterSuffix = parameterSuffix.replace("&", "?", 1)
                                secretUrl = f"{secretUrl}{parameterSuffix}"
                                cleanUrl = f"{cleanUrl}{parameterSuffix}"

                            r = requests.get(
                                secretUrl,
                                headers=ocsheaders,
                                timeout=g_requestTimeout,
                            )
                            logger.warning(f"Non-json reply to {cleanUrl}: {r.text}")
                            failedPaths[cleanUrl] = f"Non-json reply: {len(r.text)}"

                        # input("Press Enter to continue after non-json retry...")

        logger.info(f"All paths: {len(allPaths)}")
        for allPath in allPaths:
            logger.info(f"{allPath} - {allPaths.get(allPath)}")

        logger.info(f"Tested paths: {len(testedPaths)}")
        for testedPath in testedPaths:
            logger.info(f"{testedPath} - {testedPaths.get(testedPath)}")

        logger.info(f"Done with {len(failedPaths)} errors")
        for failedPath in failedPaths:
            logger.info(f"{failedPath} - {failedPaths.get(failedPath)}")
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
