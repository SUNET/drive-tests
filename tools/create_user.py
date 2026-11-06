#!/usr/bin/env python3
"""Create a user on a Sunet Drive node through the OCS provisioning API.

Usage:
    create_user.py <node> <environment> <userid> [options]

The OCS API has no backend parameter: the user is created in the first
backend that can create users, normally Database. For SSO users, the user ID
must be exactly the ID the login flow will map to.

By default the user gets a long random password that is not shown, and no
welcome email is sent: the email address, if given, is set after creation.

Authenticates as the node's OCS admin user, like get_users.py:
    NEXTCLOUD_OCS_USER_<NODE>_<TARGET>
    NEXTCLOUD_OCS_APP_PASSWORD_<NODE>_<TARGET>   (default)
    NEXTCLOUD_OCS_PASSWORD_<NODE>_<TARGET>       (with --password, and to confirm
                                                  the password when using the app password)

Examples:
    create_user.py sunet test jdoe@sunet.se --displayname "Jane Doe" --email jane@sunet.se
    create_user.py kth test test_user1 -g testgroup -g other --quota "10 GB" --dry-run
    create_user.py su prod alice@su.se --email alice@su.se --welcome-email
"""

import argparse
import getpass
import re
import secrets
import string
import sys
from urllib.parse import quote

import requests

from drivecommon import ENVIRONMENTS, DriveTarget, ocs_data, setup_logging

# Characters Nextcloud accepts in a user ID (OC\User\Manager::validateUserId)
USERID_PATTERN = re.compile(r"^[a-zA-Z0-9 _.@\-']+$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a user on a Sunet Drive node via the OCS API.",
        epilog="Credentials: NEXTCLOUD_OCS_USER_<NODE>_<TARGET> and "
        "NEXTCLOUD_OCS_APP_PASSWORD_<NODE>_<TARGET> (or ..._PASSWORD_... with --password).",
    )
    parser.add_argument("node", help="node name, e.g. sunet, kth, su")
    parser.add_argument("environment", choices=ENVIRONMENTS, help="target environment")
    parser.add_argument("userid", help="user ID; for SSO users the ID the login flow maps to")
    parser.add_argument("-n", "--displayname", help="display name")
    parser.add_argument("-e", "--email", help="email address")
    parser.add_argument("--welcome-email", action="store_true",
                        help="pass the email at creation, so Nextcloud sends its welcome email")
    parser.add_argument("-g", "--group", action="append", default=[], dest="groups",
                        help="add to this existing group (repeatable)")
    parser.add_argument("--subadmin", action="append", default=[],
                        help="make group admin of this group (repeatable)")
    parser.add_argument("-q", "--quota", help='quota, e.g. "10 GB" or "none"')
    parser.add_argument("--language", help="language code, e.g. sv or en")
    pw = parser.add_mutually_exclusive_group()
    pw.add_argument("--ask-user-password", action="store_true",
                    help="prompt for the new user's password instead of generating one")
    pw.add_argument("--show-password", action="store_true",
                    help="print the generated password")
    parser.add_argument("--dry-run", action="store_true", help="show what would be sent, change nothing")
    parser.add_argument("-y", "--yes", action="store_true", help="don't ask for confirmation in prod")
    parser.add_argument("--password", action="store_true",
                    help="authenticate with the OCS login password instead of the app password")
    parser.add_argument("--timeout", type=int, default=30, help="request timeout in seconds (default 30)")
    parser.add_argument("-v", "--verbose", action="store_true", help="log the requests made")
    args = parser.parse_args()
    if args.welcome_email and not args.email:
        parser.error("--welcome-email needs --email")
    return args


def random_password(length=40):
    alphabet = string.ascii_letters + string.digits + "-_.:+="
    return "".join(secrets.choice(alphabet) for _ in range(length))


def check(response):
    """Exit with the OCS message if the call failed."""
    ocs_data(response)


def main():
    args = parse_args()
    setup_logging(args.verbose)

    if not USERID_PATTERN.match(args.userid):
        sys.exit(f"Invalid user ID '{args.userid}': allowed are letters, digits, space and _.@-'")

    drive = DriveTarget(args.environment)
    node = args.node.lower()
    drive.check_node(node)
    base = drive.ocs_url(node) + "/cloud"

    if args.ask_user_password:
        user_password = getpass.getpass(f"Password for {args.userid}: ")
        if user_password != getpass.getpass("Repeat: "):
            sys.exit("Passwords don't match")
    else:
        user_password = random_password()

    create = {"userid": args.userid, "password": user_password}
    if args.displayname:
        create["displayName"] = args.displayname
    if args.email and args.welcome_email:
        create["email"] = args.email
    if args.groups:
        create["groups[]"] = args.groups
    if args.subadmin:
        create["subadmin[]"] = args.subadmin
    if args.quota:
        create["quota"] = args.quota
    if args.language:
        create["language"] = args.language
    # Set after creation, so Nextcloud doesn't send the welcome email
    later = {"email": args.email} if args.email and not args.welcome_email else {}

    shown = {k: ("***" if k == "password" else v) for k, v in create.items()}
    print(f"Node:   {drive.node_url(node)}")
    print(f"Create: {shown}")
    if later:
        print(f"Then:   {later}")
    if args.dry_run:
        print("Dry run, nothing sent.")
        return

    if args.environment == "prod" and not args.yes:
        if input(f"Create '{args.userid}' on {node} in PROD? [y/N] ").strip().lower() != "y":
            sys.exit("Aborted")

    session = drive.ocs_session(node, use_password=args.password, timeout=args.timeout, confirm=True)
    user_url = f"{base}/users/{quote(args.userid, safe='')}"
    try:
        check(session.post(f"{base}/users", data=create))
        for key, value in later.items():
            r = session.put(user_url, data={"key": key, "value": value})
            if r.status_code != 200 or r.json().get("ocs", {}).get("meta", {}).get("statuscode") not in (100, 200):
                print(f"Warning: user created, but setting {key} failed (HTTP {r.status_code}): {r.text[:200]}",
                      file=sys.stderr)
        info = ocs_data(session.get(user_url))
    except requests.RequestException as error:
        sys.exit(f"Request to {base} failed: {error}")

    print(f"Created '{info.get('id')}' (backend: {info.get('backend')}, "
          f"display name: {info.get('displayname')}, email: {info.get('email') or '-'}, "
          f"groups: {', '.join(info.get('groups') or []) or '-'})")
    if args.show_password:
        print(f"Password: {user_password}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
