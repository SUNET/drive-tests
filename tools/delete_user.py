#!/usr/bin/env python3
"""Delete (or disable) users on a Sunet Drive node through the OCS provisioning API.

Usage:
    delete_user.py <node> <environment> <userid> [<userid> ...] [options]

Shows each user before doing anything and asks for confirmation. Deleting a
user also deletes their files, shares and app data; it cannot be undone.
Use --disable to block the login and keep the data.

Authenticates as the node's OCS admin user, like create_user.py:
    NEXTCLOUD_OCS_USER_<NODE>_<TARGET>
    NEXTCLOUD_OCS_APP_PASSWORD_<NODE>_<TARGET>   (default)
    NEXTCLOUD_OCS_PASSWORD_<NODE>_<TARGET>       (with --password, and to confirm
                                                  the password when using the app password)

Examples:
    delete_user.py sunet test __test_test
    delete_user.py kth test user1 user2 --dry-run
    delete_user.py su prod alice@su.se --disable
"""

import argparse
import sys
from urllib.parse import quote

import requests

from drivecommon import ENVIRONMENTS, DriveTarget, ocs_data, setup_logging

# Never delete these, whatever is passed on the command line
PROTECTED = {"admin"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Delete or disable users on a Sunet Drive node via the OCS API.",
        epilog="Credentials: NEXTCLOUD_OCS_USER_<NODE>_<TARGET>, NEXTCLOUD_OCS_APP_PASSWORD_<NODE>_<TARGET> "
        "and NEXTCLOUD_OCS_PASSWORD_<NODE>_<TARGET>.",
    )
    parser.add_argument("node", help="node name, e.g. sunet, kth, su")
    parser.add_argument("environment", choices=ENVIRONMENTS, help="target environment")
    parser.add_argument("userids", nargs="+", metavar="userid", help="user ID(s) to delete")
    parser.add_argument("--disable", action="store_true", help="disable the users instead of deleting them")
    parser.add_argument("--dry-run", action="store_true", help="show the users, change nothing")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="don't ask for confirmation (in prod you still type the node name)")
    parser.add_argument("--password", action="store_true",
                        help="authenticate with the OCS login password instead of the app password")
    parser.add_argument("--timeout", type=int, default=30, help="request timeout in seconds (default 30)")
    parser.add_argument("-v", "--verbose", action="store_true", help="log the requests made")
    return parser.parse_args()


def ocs_status(response):
    """OCS status code of a reply, or None if it isn't an OCS reply."""
    try:
        return response.json()["ocs"]["meta"]["statuscode"]
    except (ValueError, KeyError, TypeError):
        return None


def describe(info):
    groups = ", ".join(info.get("groups") or []) or "-"
    enabled = "enabled" if info.get("enabled") else "disabled"
    return (f"{info.get('id')}  ({info.get('displayname') or '-'}, {info.get('email') or '-'}, "
            f"{enabled}, backend {info.get('backend')}, groups: {groups})")


def main():
    args = parse_args()
    setup_logging(args.verbose)

    drive = DriveTarget(args.environment)
    node = args.node.lower()
    drive.check_node(node)
    base = drive.ocs_url(node) + "/cloud"
    action = "disable" if args.disable else "delete"

    # Read-only lookups first; confirm the password only when we change something.
    session = drive.ocs_session(node, use_password=args.password, timeout=args.timeout)
    ocs_user = session.auth[0]
    found = []
    try:
        for userid in dict.fromkeys(args.userids):  # unique, order kept
            if userid in PROTECTED or userid == ocs_user:
                print(f"Skipping {userid}: protected account", file=sys.stderr)
                continue
            r = session.get(f"{base}/users/{quote(userid, safe='')}")
            if ocs_status(r) == 404 or r.status_code == 404:
                print(f"Skipping {userid}: no such user on {node}", file=sys.stderr)
                continue
            info = ocs_data(r)
            if args.disable and not info.get("enabled"):
                print(f"Skipping {userid}: already disabled", file=sys.stderr)
                continue
            found.append(info)
    except requests.RequestException as error:
        sys.exit(f"Request to {base} failed: {error}")

    if not found:
        sys.exit(f"Nothing to {action}.")

    print(f"Node: {drive.node_url(node)} ({args.environment})")
    print(f"Users to {action}:")
    for info in found:
        print(f"  {describe(info)}")
    if args.dry_run:
        print("Dry run, nothing changed.")
        return

    if args.environment == "prod":
        if input(f"{action.capitalize()} {len(found)} user(s) in PROD. Type the node name to confirm: ").strip() != node:
            sys.exit("Aborted")
    elif not args.yes:
        if input(f"{action.capitalize()} {len(found)} user(s)? [y/N] ").strip().lower() != "y":
            sys.exit("Aborted")

    session = drive.ocs_session(node, use_password=args.password, timeout=args.timeout, confirm=True)
    failed = 0
    for info in found:
        url = f"{base}/users/{quote(info['id'], safe='')}"
        try:
            r = session.put(f"{url}/disable") if args.disable else session.delete(url)
        except requests.RequestException as error:
            print(f"Failed to {action} {info['id']}: {error}", file=sys.stderr)
            failed += 1
            continue
        if r.status_code == 200 and ocs_status(r) in (100, 200):
            print(f"{'Disabled' if args.disable else 'Deleted'} {info['id']}")
        else:
            failed += 1
            try:
                message = r.json()["ocs"]["meta"].get("message")
            except (ValueError, KeyError, TypeError):
                message = r.text[:200]
            print(f"Failed to {action} {info['id']} (HTTP {r.status_code}, OCS {ocs_status(r)}): {message}",
                  file=sys.stderr)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
