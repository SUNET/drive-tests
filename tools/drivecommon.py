"""Shared helpers for the command-line tools in tools/.

Deliberately light: needs only requests and PyYAML, not the Selenium and
test-runner stack that sunetnextcloud.py imports. Node URLs are built the same
way as in sunetnextcloud.TestTarget, from the same expected*.yaml files.
"""

import logging
import os
import sys

import requests
import yaml

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENVIRONMENTS = ["test", "prod", "localhost", "custom"]
OCS_HEADERS = {"Accept": "application/json", "OCS-APIRequest": "true"}

log = logging.getLogger("drivetools")


def setup_logging(verbose=False):
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if verbose else logging.WARNING,
    )


def expected_file(environment):
    name = {"localhost": "expected_localhost.yaml", "custom": "expected_custom.yaml"}
    return os.path.join(REPO_DIR, name.get(environment, "expected.yaml"))


class DriveTarget:
    """Node URLs and OCS credentials for one environment."""

    def __init__(self, environment):
        if environment not in ENVIRONMENTS:
            sys.exit(f"Unknown environment '{environment}', use one of {', '.join(ENVIRONMENTS)}")
        self.environment = environment
        path = expected_file(environment)
        try:
            with open(path) as stream:
                self.expected = yaml.safe_load(stream)
        except FileNotFoundError:
            sys.exit(f"{path} not found")
        g = self.expected["global"]
        self.allnodes = sorted(g.get("allnodes") or [])
        self.baseurl = g["baseUrl"]
        self.nodeprefix = g["nodePrefix"]
        testprefix = g["testPrefix"]

        # Same rules as sunetnextcloud.TestTarget.__init__
        if environment == "prod":
            self.targetprefix, self.delimiter, self.verify = "", ".", True
        elif environment == "test":
            self.targetprefix, self.delimiter, self.verify = "." + testprefix, ".", True
        elif environment == "localhost":
            self.targetprefix, self.nodeprefix, self.delimiter, self.verify = "", "", "", False
        else:  # custom
            self.targetprefix, self.delimiter, self.verify = "." + testprefix, "", True

    def check_node(self, node):
        if self.environment in ("test", "prod") and node not in self.allnodes:
            log.warning("Node '%s' is not in expected.yaml (known: %s)", node, ", ".join(self.allnodes))

    def node_url(self, node):
        if node in ("none", "localhost"):
            prefix = self.nodeprefix
        elif not self.nodeprefix:
            prefix = node
        else:
            prefix = f"{node}.{self.nodeprefix}"
        return f"https://{prefix}{self.targetprefix}{self.delimiter}{self.baseurl}"

    def ocs_url(self, node):
        return self.node_url(node) + "/ocs/v2.php"

    def _env(self, kind, node):
        return f"NEXTCLOUD_OCS_{kind}_{node.upper()}_{self.environment.upper()}"

    def ocs_credentials(self, node, use_password=False):
        """(user, secret) of the node's OCS admin; exits if either is missing."""
        kind = "PASSWORD" if use_password else "APP_PASSWORD"
        names = [self._env("USER", node), self._env(kind, node)]
        values = [os.environ.get(n) for n in names]
        missing = [n for n, v in zip(names, values) if not v]
        if missing:
            sys.exit(f"Missing environment variable(s): {', '.join(missing)} (did you run driveenv?)")
        return values[0], values[1]

    def ocs_session(self, node, use_password=False, timeout=30, confirm=False):
        """Session for the node's OCS admin.

        confirm=True also confirms the login password in the session, which
        Nextcloud requires for admin actions (creating users and similar) when
        logged in with an app password. Needs NEXTCLOUD_OCS_PASSWORD_*.
        """
        user, secret = self.ocs_credentials(node, use_password)
        session = OcsSession(user, secret, verify=self.verify, timeout=timeout)
        if confirm and not use_password:
            _, password = self.ocs_credentials(node, use_password=True)
            session.confirm_password(self.ocs_url(node), password)
        return session


class OcsSession(requests.Session):
    """requests.Session with OCS headers, basic auth and a default timeout."""

    def __init__(self, user, secret, verify=True, timeout=30):
        super().__init__()
        self.auth = (user, secret)
        self.headers.update(OCS_HEADERS)
        self.verify = verify
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        response = super().request(method, url, **kwargs)
        log.debug("%s %s -> %s", method, response.url, response.status_code)
        return response

    def confirm_password(self, ocs_url, password):
        """Confirm the login password for this session (cookies keep it).

        Exits if the confirmation fails; nothing has been changed then.
        """
        r = self.put(f"{ocs_url}/core/apppassword/confirm", data={"password": password})
        if r.status_code == 404:
            sys.exit(f"{ocs_url}/core/apppassword/confirm not found: this Nextcloud version "
                     "has no password confirmation endpoint, try --password")
        if r.status_code == 403:
            sys.exit("Password confirmation failed: NEXTCLOUD_OCS_PASSWORD_* is not the "
                     "login password of the OCS user")
        ocs_data(r)
        log.debug("Password confirmed, session cookies: %s", ", ".join(self.cookies.keys()))


def ocs_data(response):
    """Return the 'data' part of an OCS reply, or exit with the OCS error."""
    try:
        payload = response.json()["ocs"]
        meta, data = payload["meta"], payload["data"]
    except (ValueError, KeyError, TypeError):
        sys.exit(f"HTTP {response.status_code}: no valid OCS reply from {response.url}")
    if meta.get("statuscode") not in (100, 200):
        sys.exit(f"OCS error {meta.get('statuscode')} (HTTP {response.status_code}): {meta.get('message')}")
    return data
