"""Testing OCS functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>

test_get_configuration reads the app configuration of every node through
the OCS API. If provisioning_config/<node>.<target>.json does not exist,
the configuration is saved there as reference. If it exists, the current
configuration is compared with it: the node fails if any app or value was
added, removed or changed, and the differences are listed per node. Values
in g_ignoredKeys change on their own and are not compared. The
reference files are never overwritten; delete a file to save a new one.
"""

import json
import logging
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import HtmlTestRunner
import requests
import xmlrunner

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
ocsheaders = drv.ocsheaders
expectedResults = drv.expectedResults

g_testPassed = {}
g_differences = {}
g_requestTimeout = 10
# Parallel requests per node
g_parallelRequests = 4
g_localDirectory = "./provisioning_config"
# app.key values that change on their own (timestamps, caches) and are not compared
g_ignoredKeys = [
    "circles.maintenance_run",
    "circles.maintenance_update",
    "contacts.federations_cache",
]

logger = logging.getLogger("TestLogger")
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def shorten(value, length=200):
    """Return value as text, cut to length characters."""
    text = json.dumps(value) if not isinstance(value, str) else value
    return text if len(text) <= length else text[:length] + "..."


def compare_configuration(reference, current):
    """Return the differences between two app configurations as a list of lines.

    Both are dictionaries of app -> key -> value.
    """
    differences = []
    for app in sorted(set(reference) | set(current)):
        if app not in current:
            differences.append(f"{app}: app removed")
            continue
        if app not in reference:
            differences.append(f"{app}: app added")
            continue
        for key in sorted(set(reference[app]) | set(current[app])):
            if f"{app}.{key}" in g_ignoredKeys:
                continue
            if key not in current[app]:
                differences.append(f"{app}.{key}: removed (was {shorten(reference[app][key])})")
            elif key not in reference[app]:
                differences.append(f"{app}.{key}: added ({shorten(current[app][key])})")
            elif reference[app][key] != current[app][key]:
                differences.append(
                    f"{app}.{key}: {shorten(reference[app][key])} -> {shorten(current[app][key])}"
                )
    return differences


class GetConfiguration(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global logger
        global g_testPassed
        node = self.name

        g_testPassed[node] = False
        logger.info(f"Setting passed for {node} to {g_testPassed.get(node)}")

        node_configuration = {}

        node_config_path = f"{g_localDirectory}/{node}.{drv.target}.json"
        node_config_file = Path(node_config_path)
        reference = None
        if node_config_file.is_file():
            try:
                with open(node_config_path) as f:
                    reference = json.load(f).get(node, {})
            except Exception as error:
                logger.error(f"Unable to read {node_config_path}: {error}")
                return

        key = "none"
        logger.info(f"Execute for {node}")
        nodeuser = drv.get_ocsuser(node)
        nodepwd = drv.get_ocsuserapppassword(node)

        try:
            rawurl = drv.get_all_apps_url(node)
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
            session = requests.Session()
            r = session.get(url, headers=ocsheaders, timeout=g_requestTimeout)
        except Exception as error:
            logger.error(f"Unable to get the app list from {node}: {error}")
            return

        # 503 usually means that the node is in maintenance mode
        if r.status_code != 200:
            logger.error(
                f"Unable to get the app list from {node}: HTTP {r.status_code} - {r.text[:200]}"
            )
            return

        try:
            j = json.loads(r.text)
            apps = j["ocs"]["data"]["apps"]
        except Exception as error:
            logger.error(f"No or invalid apps JSON reply received from {node}:{error}")
            return

        # Each worker thread uses its own session
        local = threading.local()

        def get_json(url):
            if not hasattr(local, "session"):
                local.session = requests.Session()
            url = url.replace("$USERNAME$", nodeuser).replace("$PASSWORD$", nodepwd)
            r = local.session.get(url, headers=ocsheaders, timeout=g_requestTimeout)
            return json.loads(r.text)["ocs"]["data"]["data"]

        def get_keys(app):
            try:
                return app, get_json(drv.get_app_config_keys_url(node, app)), None
            except Exception as error:
                return app, None, error

        def get_value(item):
            app, key = item
            try:
                return app, key, get_json(drv.get_app_config_value_url(node, app, key)), None
            except Exception as error:
                return app, key, None, error

        failedApps = []
        with ThreadPoolExecutor(max_workers=g_parallelRequests) as executor:
            items = []
            for app, keys, error in executor.map(get_keys, apps):
                if error is not None:
                    logger.error(f"No or invalid JSON reply received from node: {node} - app: {app}: {error}")
                    failedApps.append(app)
                    continue
                items.extend((app, key) for key in keys)
            logger.info(f"Get {len(items)} app config values for {node}")

            for app, key, value, error in executor.map(get_value, items):
                if error is not None:
                    logger.error(f"No or invalid JSON reply received from node: {node} - app: {app} - {key}: {error}")
                    if app not in failedApps:
                        failedApps.append(app)
                    continue
                node_configuration.setdefault(node, {}).setdefault(app, {})[key] = value

        # An incomplete configuration would be skipped by later runs, so do not save it
        if failedApps:
            logger.error(
                f"Done: {node} - configuration not saved, failed apps: {failedApps}"
            )
            return

        # logger.info(f'Full node configuration: {json.dumps(node_configuration, indent=4)}')

        # Without a reference, save the configuration as the new reference
        if reference is None:
            Path(g_localDirectory).mkdir(parents=True, exist_ok=True)
            with open(node_config_path, "w") as f:
                logger.info(f"Save node configuration file to {node_config_path}")
                json.dump(node_configuration, f, indent=4, sort_keys=True)
            logger.info(f"Done: {node} - configuration saved")
            g_testPassed[node] = True
            return

        differences = compare_configuration(reference, node_configuration.get(node, {}))
        g_differences[node] = differences
        if differences:
            logger.error(f"Done: {node} - {len(differences)} differences to {node_config_path}")
            return

        logger.info(f"Done: {node} - configuration unchanged")
        g_testPassed[node] = True
        return


class TestOcsConfigAll(unittest.TestCase):
    def test_logger(self):
        logger.info(f"TestID: {self._testMethodName}")
        pass

    def test_get_configuration(self):
        logger.info(f"TestID: {self._testMethodName}")

        threads = []
        for node in drv.allnodes:
            with self.subTest(mynode=node):
                logger.info(f"TestID: {node}")
                getConfigurationThread = GetConfiguration(node)
                getConfigurationThread.start()
                threads.append(getConfigurationThread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        changedNodes = [node for node in drv.allnodes if g_differences.get(node)]
        for node in changedNodes:
            logger.warning(f"Configuration changes on {node}:")
            for difference in g_differences[node]:
                logger.warning(f"    {difference}")
        logger.info(f"Nodes with configuration changes: {changedNodes if changedNodes else 'none'}")

        for node in drv.allnodes:
            with self.subTest(mynode=node):
                self.assertTrue(
                    g_testPassed.get(node, False),
                    "\n".join(g_differences.get(node, [])),
                )


if __name__ == "__main__":
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
