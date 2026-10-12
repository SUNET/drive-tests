"""Clean up the Selenium user's WebDAV files on Sunet Drive
Author: Richard Freitag <freitag@sunet.se>

Deletes everything in the Selenium test user's home folder, except the
mounts in g_excludeList, whose contents are deleted instead. Only items
that have not been modified for g_minAge are deleted, so files and
folders that a running test is using are left alone. Nextcloud updates
a folder's modification time when something inside it changes, so a
folder in use counts as recently modified. Items without a readable
modification time are skipped.

A node fails if its home folder cannot be listed or if a listing or
deletion fails.

Environment variables:
- NextcloudTestTarget: test target passed to sunetnextcloud.TestTarget
"""

import logging
import os
import threading
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import unquote, urlsplit

from webdav3.client import Client

import sunetnextcloud

g_testtarget = os.environ.get("NextcloudTestTarget")
# Mounts that are kept; only their contents are deleted
g_excludeList = ["selenium-system/", "selenium-personal/", "projectbucket/"]
# Items must not have been modified for this long
g_minAge = timedelta(hours=1)
g_webdav_timeout = 30
g_cleaningResults = []
g_testPassed = {}

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def modification_time(info):
    """Return the modification time of a WebDAV list entry as aware datetime, or None."""
    try:
        return parsedate_to_datetime(info["modified"])
    except (KeyError, TypeError, ValueError):
        return None


def list_folder(client, basepath, folder=""):
    """List a WebDAV folder with modification times.

    Returns (relative path, modification time) for every item in folder,
    without the folder itself. Relative paths are relative to the
    user's WebDAV root and end with '/' for folders.
    """
    folderpath = basepath + folder
    items = []
    for info in client.list(folder, get_info=True):
        path = info["path"]
        # webdav3 only drops the folder itself if the host URL has no path, so check here
        if path.rstrip("/") == folderpath.rstrip("/") or not path.startswith(basepath):
            continue
        relpath = path[len(basepath):]
        if info.get("isdir") and not relpath.endswith("/"):
            relpath += "/"
        items.append((relpath, modification_time(info)))
    return items


class CleanWebDAV(threading.Thread):
    """Thread that deletes the Selenium user's old WebDAV files and folders on a node.

    Deletes old items in the home folder, and old items inside the
    mounts in g_excludeList. Recently modified items are skipped. The
    node passes if all listings and deletions succeed.
    """

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        node = self.name
        g_testPassed[node] = False
        logger.info(f"DAV cleaning thread started: {node}")

        try:
            drv = sunetnextcloud.TestTarget(g_testtarget)
            nodeuser = drv.get_seleniumuser(node)
            nodepwd = drv.get_seleniumuserapppassword(node)
            url = drv.get_webdav_url(node, nodeuser)
            logger.info(f"URL: {url}")
            client = Client({
                "webdav_hostname": url,
                "webdav_login": nodeuser,
                "webdav_password": nodepwd,
                "webdav_timeout": g_webdav_timeout,
            })
            client.verify = drv.verify
            basepath = unquote(urlsplit(url).path)
            if not basepath.endswith("/"):
                basepath += "/"
        except Exception as error:
            logger.error(f"Error setting up the WebDAV client for {node}: {error}")
            return

        try:
            rootItems = list_folder(client, basepath)
        except Exception as error:
            logger.error(f"Unable to list the home folder on {node}: {error}")
            return
        logger.info(f"DAV elements on {node}: {[path for path, _ in rootItems]}")

        # Mounts are kept; their contents are cleaned like the home folder
        candidates = []
        failed = 0
        for path, modified in rootItems:
            if path in g_excludeList:
                try:
                    candidates.extend(list_folder(client, basepath, path))
                except Exception as error:
                    logger.error(f"Unable to list {path} on {node}: {error}")
                    failed += 1
            else:
                candidates.append((path, modified))

        now = datetime.now(timezone.utc)
        deleted = skipped = 0
        startTime = datetime.now()
        for path, modified in candidates:
            if modified is None:
                logger.warning(f"Skipping {path} on {node}: no modification time")
                skipped += 1
                continue
            if now - modified < g_minAge:
                logger.info(f"Skipping {path} on {node}: modified {modified:%Y-%m-%d %H:%M:%S} UTC")
                skipped += 1
                continue
            logger.info(f"Removing {node} - {drv.target} - {path}")
            try:
                client.clean(path)
                deleted += 1
            except Exception as error:
                logger.error(f"Could not delete {node} - {drv.target} - {path}: {error}")
                failed += 1

        totalTime = (datetime.now() - startTime).total_seconds()
        message = f"{node} - {deleted} deleted, {failed} failed, {skipped} skipped"
        if deleted > 0:
            message += f" - {totalTime:.1f}s at {totalTime / deleted:.2f} s/element"
        g_cleaningResults.append(message)
        logger.info(f"DAV cleaning thread done: {message}")
        g_testPassed[node] = failed == 0


class TestCleanAllWebDAV(unittest.TestCase):
    """Deletes the Selenium user's old WebDAV files on all nodes under test."""

    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        logger.info(f"TestID: {self._testMethodName}")

    def test_cleanallwebdav(self):
        """Delete the Selenium user's old WebDAV files on all nodes; fail nodes where this does not fully work."""
        logger.info(f"Target: {g_testtarget}")
        drv = sunetnextcloud.TestTarget(g_testtarget)
        threads = []
        for node in drv.nodestotest:
            thread = CleanWebDAV(node)
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
