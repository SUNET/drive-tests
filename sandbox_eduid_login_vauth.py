import json
import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.virtual_authenticator import (
    Credential,
    VirtualAuthenticatorOptions,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import sunetnextcloud

drv = sunetnextcloud.TestTarget()
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger.info("Start eduid.se login test")
delay = 30

# Load saved data
with open("eduid_data.json", "r") as f:
    auth_data = json.load(f)

# Increase sign count by one and save the json for the next login
logger.info(
    f"Virtual authenticator has been used {auth_data['credentials'][0]['signCount']} times"
)
auth_data["credentials"][0]["signCount"] += 1

loginurl = "https://dashboard.eduid.se"
logger.info(f"Login url: {loginurl}")

samluser = os.environ.get("EDUID_USER")
samlpassword = os.environ.get("EDUID_PASSWORD")
logger.info(f"Logging in with {samluser}")

options = ChromeOptions()
# options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, delay)

try:
    # Enable WebAuthn domain
    driver.execute_cdp_cmd("WebAuthn.enable", {})

    # Add virtual authenticator
    result = driver.execute_cdp_cmd(
        "WebAuthn.addVirtualAuthenticator", {"options": auth_data["options"]}
    )
    authenticator_id = result["authenticatorId"]

    # Restore credentials
    for credential in auth_data["credentials"]:
        driver.execute_cdp_cmd(
            "WebAuthn.addCredential",
            {"authenticatorId": authenticator_id, "credential": credential},
        )

    logger.info(f"Restored {len(auth_data['credentials'])} credential(s)")

    driver.get(loginurl)
    time.sleep(3)

    logger.info(f"Log on with passkey")
    wait.until(EC.presence_of_element_located((By.ID, "pass-key"))).click()
    time.sleep(5)
    wait.until(EC.presence_of_element_located((By.ID, "logout"))).click()
    wait.until(EC.presence_of_element_located((By.ID, "login-button")))
    currentUrl = driver.current_url
    logger.info(f"Logut successful: {currentUrl}")

    with open("webauthn_data.json", "w") as f:
        json.dump(auth_data, f, indent=2)

except Exception as error:
    logger.error(f"Something wrong: {error}")
    time.sleep(600)

logger.info("DONE!")
