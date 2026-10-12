"""Clean up test automation users on Sunet Drive
Author: Richard Freitag <freitag@sunet.se>

Deletes user accounts that the test automation created but did not
delete, for example because a test was interrupted. Only users whose ID
starts with one of g_userPrefixes are deleted. When the ID contains a
creation timestamp (YYYY_MM_DD_HH_MM_SS, local time of the machine that
ran the test), the user is only deleted if it is older than
g_minUserAge, so users of tests that are still running are left alone.
Users without a timestamp in their ID are deleted regardless of age.

A node fails if its users cannot be listed or if any deletion fails.

Environment variables:
- NextcloudTestTarget: test target passed to sunetnextcloud.TestTarget
"""

import json
import logging
import os
import re
import threading
import unittest
from datetime import datetime, timedelta

import requests

import sunetnextcloud

g_testtarget = os.environ.get("NextcloudTestTarget")
g_requestTimeout = 10
# ID prefixes of the users created by the test automation
g_userPrefixes = ("__cli_user_", "__performance_user_", "__lifecycle_user_")
# Users with a creation timestamp in their ID must be at least this old
g_minUserAge = timedelta(hours=1)
g_timestampPattern = re.compile(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}")
g_cleaningResults = []
g_testPassed = {}

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def user_creation_time(user):
    """Return the creation time encoded in a test user ID, or None if it has none."""
    match = g_timestampPattern.search(user)
    if match is None:
        return None
    try:
        return datetime.strptime(match.group(0), "%Y_%m_%d_%H_%M_%S")
    except ValueError:
        return None


def is_test_user(user):
    """Return True if the user ID belongs to a user created by the test automation."""
    return user.startswith(g_userPrefixes)


def is_old_enough(user, now):
    """Return True if the user has no creation timestamp or is older than g_minUserAge."""
    created = user_creation_time(user)
    return created is None or now - created >= g_minUserAge


class CleanTestautomationUsers(threading.Thread):
    """Thread that deletes the leftover test automation users on a node.

    Confirms the OCS user's app password, lists the users matching the
    test user prefixes and deletes those that are old enough. Each
    deletion is checked; the node passes only if all deletions succeed.
    """

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        node = self.name
        g_testPassed[node] = False
        logger.info(f"Testautomation user cleaning thread started: {node}")

        try:
            drv = sunetnextcloud.TestTarget(g_testtarget)
            nodeuser = drv.get_ocsuser(node)
            nodepwd = drv.get_ocsuserpassword(node)
            nodeapppwd = drv.get_ocsuserapppassword(node)
            session = requests.Session()
            session.headers.update(drv.ocsheaders)
        except Exception as error:
            logger.error(f"Error setting up the cleaning for {node}: {error}")
            return

        # Without a confirmed app password, deleting users can be refused; try anyway
        try:
            url = drv.get_confirm_apppassword_url(node)
            url = url.replace("$USERNAME$", nodeuser).replace("$PASSWORD$", nodeapppwd)
            r = session.put(url, json={"password": nodepwd}, timeout=g_requestTimeout, verify=drv.verify)
            logger.info(f"Confirm app password for {nodeuser} on {node}: {r.status_code}")
        except Exception as error:
            logger.warning(f"Error confirming app password for {nodeuser} on {node}: {error}")

        try:
            url = drv.get_users_url(node)
            url = url.replace("$USERNAME$", nodeuser).replace("$PASSWORD$", nodeapppwd)
            # The server-side search narrows the list; the prefix check below is what counts
            r = session.get(url, params={"search": "__"}, timeout=g_requestTimeout, verify=drv.verify)
            users = json.loads(r.text)["ocs"]["data"]["users"]
        except Exception as error:
            logger.error(f"Unable to list the users of {node}: {error}")
            return

        now = datetime.now()
        deleted = failed = skipped = 0
        startTime = datetime.now()
        for user in users:
            if not is_test_user(user):
                continue
            if not is_old_enough(user, now):
                logger.info(f"Skipping {user} on {node}: younger than {g_minUserAge}")
                skipped += 1
                continue

            logger.info(f"Deleting user {user} on {node}")
            try:
                url = drv.get_user_url(node, user)
                url = url.replace("$USERNAME$", nodeuser).replace("$PASSWORD$", nodeapppwd)
                r = session.delete(url, timeout=g_requestTimeout, verify=drv.verify)
                meta = json.loads(r.text)["ocs"]["meta"]
            except Exception as error:
                logger.error(f"Error deleting {user} on {node}: {error}")
                failed += 1
                continue

            # OCS v2 reports success as 200, v1 as 100
            if meta["statuscode"] in (100, 200):
                deleted += 1
            else:
                logger.error(
                    f"Deleting {user} on {node} failed - Status: {meta['status']} - Code: {meta['statuscode']} - Message: {meta['message']}"
                )
                failed += 1

        totalTime = (datetime.now() - startTime).total_seconds()
        message = f"{node} - {deleted} deleted, {failed} failed, {skipped} skipped as too young"
        if deleted > 0:
            message += f" - {totalTime:.1f}s at {totalTime / deleted:.2f} s/user"
        g_cleaningResults.append(message)
        logger.info(f"Testautomation user cleaning thread done: {message}")
        g_testPassed[node] = failed == 0


class TestCleanAllTestautomationUsers(unittest.TestCase):
    """Deletes leftover test automation users on all nodes under test."""

    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        logger.info(f"TestID: {self._testMethodName}")

    def test_clean_testautomation_users(self):
        """Delete leftover test automation users on all nodes; fail nodes where this does not fully work."""
        logger.info(f"Target: {g_testtarget}")
        drv = sunetnextcloud.TestTarget(g_testtarget)
        threads = []
        for node in drv.nodestotest:
            thread = CleanTestautomationUsers(node)
            thread.start()
            threads.append(thread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        for message in g_cleaningResults:
            logger.info(message)

        for node in drv.nodestotest:
            with self.subTest(mynode=node):
                self.assertTrue(g_testPassed.get(node, False))


if __name__ == "__main__":
    import xmlrunner

    unittest.main(testRunner=xmlrunner.XMLTestRunner(output="test-reports"))
