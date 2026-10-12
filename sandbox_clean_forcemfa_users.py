"""Find group memberships of deleted users in the forcemfa group
Author: Richard Freitag <freitag@sunet.se>

When a user is deleted, the auto_groups app adds the user back to its
groups (see nextcloud/server#62872 and #62911). The group then keeps
memberships of users that no longer exist: the group's user count
includes them, but they are not listed in the UI.

For every node under test, this script compares the user count of the
group (counted in the database, including deleted users) with the
members that still exist (as listed by the OCS API). The difference is
the number of orphaned memberships.

The OCS API cannot list or remove memberships of users that do not exist,
so for nodes with orphaned memberships, the SQL to remove them on the
database server is printed.

Environment variables:
- NextcloudTestTarget: test target passed to sunetnextcloud.TestTarget
- NextcloudTestCustomers: nodes to check, e.g. su or all
"""

import json
import logging

import requests

import sunetnextcloud

g_group = "forcemfa"
g_requestTimeout = 120

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

drv = sunetnextcloud.TestTarget()
affected = {}

for node in drv.nodestotest:
    nodeuser = drv.get_ocsuser(node)
    nodeapppwd = drv.get_ocsuserapppassword(node)
    session = requests.Session()
    session.headers.update(drv.ocsheaders)

    try:
        # The user count comes from the group backend and includes deleted users
        url = drv.get_groups_details_url(node).replace("$USERNAME$", nodeuser).replace("$PASSWORD$", nodeapppwd)
        r = session.get(url, params={"search": g_group}, timeout=g_requestTimeout, verify=drv.verify)
        groups = json.loads(r.text)["ocs"]["data"]["groups"]
        group = next((g for g in groups if g["id"] == g_group), None)
        if group is None:
            logger.info(f"{node}: no group {g_group}")
            continue
        usercount = int(group["usercount"])

        # The member list only contains users that still exist
        url = drv.get_group_url(node, g_group).replace("$USERNAME$", nodeuser).replace("$PASSWORD$", nodeapppwd)
        r = session.get(f"{url}/users", timeout=g_requestTimeout, verify=drv.verify)
        members = json.loads(r.text)["ocs"]["data"]["users"]
    except Exception as error:
        logger.error(f"{node}: unable to read group {g_group}: {error}")
        continue

    orphaned = usercount - len(members)
    if orphaned > 0:
        logger.warning(f"{node}: {g_group} counts {usercount} users, {len(members)} exist, {orphaned} orphaned")
        affected[node] = orphaned
    else:
        logger.info(f"{node}: {g_group} counts {usercount} users, all exist")

logger.info(f"Nodes with orphaned {g_group} memberships: {affected if affected else 'none'}")

if affected:
    # Users exist either in the database backend (oc_users) or in user_saml (oc_user_saml_users)
    orphanCondition = (
        f"gid = '{g_group}'"
        " AND uid NOT IN (SELECT uid FROM oc_users)"
        " AND uid NOT IN (SELECT uid FROM oc_user_saml_users)"
    )
    print("\nCheck and remove the orphaned memberships on the database of each affected node:\n")
    print(f"SELECT COUNT(*) FROM oc_group_user WHERE {orphanCondition};")
    print(f"DELETE FROM oc_group_user WHERE {orphanCondition};")
