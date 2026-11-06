#!/usr/bin/env python3
"""List the users of a Sunet Drive node through the OCS provisioning API.

Usage:
    get_users.py <node> <environment> [options]

Authenticates as the node's OCS admin user. Credentials come from the
environment (load them with driveenv first):

    NEXTCLOUD_OCS_USER_<NODE>_<TARGET>
    NEXTCLOUD_OCS_APP_PASSWORD_<NODE>_<TARGET>   (default)
    NEXTCLOUD_OCS_PASSWORD_<NODE>_<TARGET>       (with --password)

Examples:
    get_users.py sunet test
    get_users.py sunet prod --search doe --details
    get_users.py kth test --group admin --format table
    get_users.py su prod --disabled --format csv > disabled.csv
    get_users.py uu prod --count
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from drivecommon import ENVIRONMENTS, DriveTarget, ocs_data, setup_logging

PAGE_SIZE = 500
DETAIL_COLUMNS = ["id", "displayname", "email", "enabled", "backend", "lastLogin", "used", "quota", "groups"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="List the users of a Sunet Drive node via the OCS API.",
        epilog="Credentials: NEXTCLOUD_OCS_USER_<NODE>_<TARGET> and "
        "NEXTCLOUD_OCS_APP_PASSWORD_<NODE>_<TARGET> (or ..._PASSWORD_... with --password).",
    )
    parser.add_argument("node", help="node name, e.g. sunet, kth, su")
    parser.add_argument("environment", choices=ENVIRONMENTS, help="target environment")
    parser.add_argument("-s", "--search", help="only users matching this text (id, display name, email)")
    parser.add_argument("-g", "--group", help="only members of this group")
    parser.add_argument("-l", "--limit", type=int, help="return at most this many users")
    parser.add_argument("-o", "--offset", type=int, default=0, help="skip this many users (default 0)")
    parser.add_argument("-d", "--details", action="store_true",
                        help="fetch display name, email, enabled, backend, last login, quota and groups")
    state = parser.add_mutually_exclusive_group()
    state.add_argument("--enabled", action="store_true", help="only enabled users (implies --details)")
    state.add_argument("--disabled", action="store_true", help="only disabled users (implies --details)")
    parser.add_argument("-f", "--format", choices=["plain", "table", "csv", "json"],
                        help="output format (default: plain without details, table with details)")
    parser.add_argument("-c", "--count", action="store_true", help="print only the number of users")
    parser.add_argument("--password", action="store_true",
                        help="authenticate with the login password instead of the app password")
    parser.add_argument("--timeout", type=int, default=30, help="request timeout in seconds (default 30)")
    parser.add_argument("-v", "--verbose", action="store_true", help="log the requests made")
    args = parser.parse_args()
    if args.enabled or args.disabled:
        args.details = True
    if args.format is None:
        args.format = "table" if args.details else "plain"
    return args


def fetch_paged(session, url, params, limit, offset):
    """Fetch an OCS list in pages. Returns a list of ids or a list of detail dicts."""
    results = []
    while limit is None or len(results) < limit:
        page = PAGE_SIZE if limit is None else min(PAGE_SIZE, limit - len(results))
        r = session.get(url, params={**params, "limit": page, "offset": offset})
        items = ocs_data(r).get("users") or []
        if isinstance(items, dict):  # the details endpoints return {id: {...}}
            items = list(items.values())
        results.extend(items)
        if len(items) < page:
            break
        offset += len(items)
    return results


def matches(user, search):
    """Client-side search, used where the API has no search parameter."""
    if not search:
        return True
    if isinstance(user, str):
        return search.lower() in user.lower()
    fields = (user.get("id"), user.get("displayname"), user.get("email"))
    return any(search.lower() in (f or "").lower() for f in fields)


def format_time(ms):
    if not ms:
        return "never"
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def format_bytes(value):
    if not isinstance(value, (int, float)) or value < 0:
        return "none" if value in (None, -3) else str(value)  # -3 = unlimited
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def flatten(user):
    quota = user.get("quota") or {}
    total = quota.get("quota")
    return {
        "id": user.get("id", ""),
        "displayname": user.get("displayname") or "",
        "email": user.get("email") or "",
        "enabled": "yes" if user.get("enabled") else "no",
        "backend": user.get("backend") or "",
        "lastLogin": format_time(user.get("lastLogin")),
        "used": format_bytes(quota.get("used")),
        "quota": "unlimited" if total == -3 else format_bytes(total),
        "groups": ",".join(user.get("groups") or []),
    }


def print_users(users, args):
    if args.format == "json":
        print(json.dumps(users, indent=2, ensure_ascii=False))
        return
    if not args.details:
        if args.format == "csv":
            print("id")
        for user in users:
            print(user)
        return
    rows = [flatten(u) for u in users]
    if args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=DETAIL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    elif args.format == "plain":
        for row in rows:
            print("\t".join(row[c] for c in DETAIL_COLUMNS))
    else:
        widths = {c: max([len(c)] + [len(r[c]) for r in rows]) for c in DETAIL_COLUMNS}
        print("  ".join(c.ljust(widths[c]) for c in DETAIL_COLUMNS).rstrip())
        print("  ".join("-" * widths[c] for c in DETAIL_COLUMNS))
        for row in rows:
            print("  ".join(row[c].ljust(widths[c]) for c in DETAIL_COLUMNS).rstrip())


def main():
    args = parse_args()
    setup_logging(args.verbose)

    drive = DriveTarget(args.environment)
    node = args.node.lower()
    drive.check_node(node)
    session = drive.ocs_session(node, use_password=args.password, timeout=args.timeout)
    base = drive.ocs_url(node) + "/cloud"
    logging.info("Querying %s as %s", base, session.auth[0])

    try:
        if args.group:
            group = quote(args.group, safe="")
            if args.details:
                users = fetch_paged(session, f"{base}/groups/{group}/users/details",
                                    {"search": args.search or ""}, args.limit, args.offset)
            else:
                # This endpoint has no search or paging parameters.
                users = ocs_data(session.get(f"{base}/groups/{group}/users")).get("users") or []
                users = [u for u in users if matches(u, args.search)][args.offset:]
                if args.limit is not None:
                    users = users[:args.limit]
        else:
            endpoint = f"{base}/users/details" if args.details else f"{base}/users"
            users = fetch_paged(session, endpoint, {"search": args.search or ""},
                                args.limit, args.offset)
    except requests.RequestException as error:
        sys.exit(f"Request to {base} failed: {error}")

    if args.enabled:
        users = [u for u in users if u.get("enabled")]
    elif args.disabled:
        users = [u for u in users if not u.get("enabled")]

    if args.count:
        print(len(users))
    else:
        print_users(users, args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:  # e.g. piped into head
        sys.exit(0)
