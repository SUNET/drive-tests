"""Find nodes with orphaned memberships in the forcemfa group
Author: Richard Freitag <freitag@sunet.se>

When a user is deleted, auto_groups before 1.7.2 adds the user back to
its groups (nextcloud/server#62872, #62911), so the forcemfa group keeps
memberships of users that no longer exist. Listing the members of such a
group can take minutes, because Nextcloud looks up every member.

For every node, the test reads the number of users on the node, the
member count of the group (counted in the database, including deleted
users) and the list of members that still exist. A node fails if the
group has more members than the node has users, if listing the members
times out, or if the group has members that no longer exist (orphaned).
Nodes without the group pass.

Use sandbox_clean_forcemfa_users.py for the SQL to remove the orphaned
memberships.

Environment variables:
- NextcloudTestTarget: test target passed to sunetnextcloud.TestTarget
- NextcloudTestCustomers: nodes to check, e.g. su or all
"""

import json
import logging
import os
import sys
import threading
import unittest

import HtmlTestRunner
import requests
import xmlrunner

import sunetnextcloud

drv = sunetnextcloud.TestTarget()

g_group = "forcemfa"
g_requestTimeout = 30
# Listing the members of a broken group is slow; give up after this many seconds
g_memberTimeout = 60
g_results = {}
# Per node: users, group members, listed members (None if unknown) and status, for the overview table
g_table = {}
g_testPassed = {}

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


class CheckGroupMembers(threading.Thread):
    """Thread that checks the forcemfa group of one node.

    Stores a one-line result in g_results and sets g_testPassed for the
    node to True if the group is missing or looks consistent.
    """

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        node = self.name
        g_testPassed[node] = False

        try:
            nodeuser = drv.get_ocsuser(node)
            nodepwd = drv.get_ocsuserapppassword(node)
            session = requests.Session()
            session.headers.update(drv.ocsheaders)

            def get_data(url, timeout, **kwargs):
                url = url.replace("$USERNAME$", nodeuser).replace("$PASSWORD$", nodepwd)
                r = session.get(url, timeout=timeout, verify=drv.verify, **kwargs)
                return json.loads(r.text)["ocs"]["data"]

            users = len(get_data(drv.get_users_url(node), g_requestTimeout)["users"])
            groups = get_data(
                drv.get_groups_details_url(node), g_requestTimeout, params={"search": g_group}
            )["groups"]
        except Exception as error:
            g_results[node] = f"error reading users or groups: {error}"
            g_table[node] = (None, None, None, "error reading users or groups")
            logger.error(f"{node}: {g_results[node]}")
            return

        group = next((g for g in groups if g["id"] == g_group), None)
        if group is None:
            g_results[node] = f"no group {g_group}"
            g_table[node] = (users, None, None, f"no group {g_group}")
            logger.info(f"{node}: {g_results[node]}")
            g_testPassed[node] = True
            return
        # Counted in the database, so it includes members that no longer exist
        count = int(group["usercount"])

        try:
            url = drv.get_group_url(node, g_group)
            members = len(get_data(f"{url}/users", g_memberTimeout)["users"])
        except requests.exceptions.Timeout:
            members = None
        except Exception as error:
            g_results[node] = f"{users} users, {count} {g_group} members, error listing members: {error}"
            g_table[node] = (users, count, None, "error listing members")
            logger.error(f"{node}: {g_results[node]}")
            return

        result = f"{users} users, {count} {g_group} members"
        problems = []
        if count > users:
            problems.append("more members than users")
        if members is None:
            problems.append(f"listing members timed out after {g_memberTimeout}s")
        else:
            result += f", {members} listed, {count - members} orphaned"
            if count > members:
                problems.append("orphaned members")

        g_table[node] = (users, count, members, ", ".join(problems) if problems else "ok")
        if problems:
            g_results[node] = f"{result} - {', '.join(problems)}"
            logger.warning(f"{node}: {g_results[node]}")
        else:
            g_results[node] = result
            logger.info(f"{node}: {g_results[node]}")
            g_testPassed[node] = True


def print_overview():
    """Print a table of all checked nodes, sorted by node name."""
    def cell(value):
        return "-" if value is None else str(value)

    rows = []
    for node in sorted(drv.nodestotest):
        users, count, members, status = g_table.get(node, (None, None, None, "no result"))
        orphaned = count - members if count is not None and members is not None else None
        listed = "timeout" if count is not None and members is None and "timed out" in status else cell(members)
        rows.append((node, cell(users), cell(count), listed, cell(orphaned), status))

    header = ("Node", "Users", "Members", "Listed", "Orphaned", "Status")
    widths = [max(len(row[i]) for row in rows + [header]) for i in range(len(header))]
    # Text columns left-aligned, numbers right-aligned
    align = ["<", ">", ">", ">", ">", "<"]
    line = lambda row: "  ".join(f"{value:{a}{w}}" for value, a, w in zip(row, align, widths))
    # Printed to stderr like the test runner output, so it ends up below it
    print(file=sys.stderr)
    print(f"{g_group} overview for {drv.target}:", file=sys.stderr)
    for row in [header, ["-" * w for w in widths]] + rows:
        print(line(row).rstrip(), file=sys.stderr)


class TestForcemfaMembers(unittest.TestCase):
    """Checks the forcemfa group on all nodes under test."""

    def test_logger(self):
        """Log the test ID to check that the test runner and logging work."""
        logger.info(f"TestID: {self._testMethodName}")

    def test_forcemfa_members(self):
        """Fail nodes whose forcemfa group has orphaned members, more members than users or cannot be listed."""
        threads = []
        for node in drv.nodestotest:
            thread = CheckGroupMembers(node)
            thread.start()
            threads.append(thread)

        # Wait until every thread has finished, however it exited
        for thread in threads:
            thread.join()

        flagged = [node for node in drv.nodestotest if not g_testPassed.get(node, False)]
        logger.info(f"Nodes with {g_group} problems: {flagged if flagged else 'none'}")

        for node in drv.nodestotest:
            with self.subTest(mynode=node):
                self.assertTrue(g_testPassed.get(node, False), g_results.get(node, "no result"))


if __name__ == "__main__":
    if drv.testrunner == "xml":
        program = unittest.main(exit=False, testRunner=xmlrunner.XMLTestRunner(output="test-reports"))
    elif drv.testrunner == "txt":
        program = unittest.main(
            exit=False,
            testRunner=unittest.TextTestRunner(
                resultclass=sunetnextcloud.NumbersTestResult
            )
        )
    else:
        program = unittest.main(
            exit=False,
            testRunner=HtmlTestRunner.HTMLTestRunner(
                output="test-reports-html",
                combine_reports=True,
                report_name=f"nextcloud-{drv.target}-{drv.expectedResults[drv.target]['status']['version'][-1]}-{os.path.basename(__file__)}",
                add_timestamp=False,
            )
        )

    # After the runner's summary, so that the table is the last output
    if g_table:
        print_overview()
    sys.exit(not program.result.wasSuccessful())
