import json
import logging
import os
import time
from datetime import datetime

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

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger.info("Start eduid.se login")
delay = 30

loginurl = "https://eduid.se"
logger.info(f"Login url: {loginurl}")

username = os.environ.get("EDUID_USER")
pwd = os.environ.get("EDUID_PASSWORD")

logger.info(f"Logging in with {username}")

options = ChromeOptions()
driver = webdriver.Chrome(options=options)

logger.info(f"Eduid.se register virtual authenticator test")
driver.get(loginurl)
wait = WebDriverWait(driver, delay)

try:
    wait.until(EC.presence_of_element_located((By.ID, "login-button"))).click()
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    time.sleep(1)
    wait.until(EC.presence_of_element_located((By.ID, "currentPassword"))).send_keys(
        pwd
    )
    time.sleep(1)
    wait.until(EC.presence_of_element_located((By.ID, "login-form-button"))).click()

    wait.until(EC.presence_of_element_located((By.ID, "mfa-security-key"))).click()
    logger.info(f"Use your existing security key to log on!")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "user-name")))
    driver.get(f"https://eduid.se/profile/security/")

    wait.until(
        EC.presence_of_element_located((By.ID, "security-webauthn-button"))
    ).click()
    wait.until(
        EC.element_to_be_clickable((By.ID, "describe-webauthn-token-modal"))
    ).send_keys(f"Automatic VAuth {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Adding virtual authenticator and credentials to driver")

    driver.execute_cdp_cmd("WebAuthn.enable", {})

    # Now add virtual authenticator
    options = {
        "protocol": "ctap2",
        "transport": "usb",
        "hasResidentKey": True,
        "hasUserVerification": True,
        "isUserVerified": True,
    }

    result = driver.execute_cdp_cmd(
        "WebAuthn.addVirtualAuthenticator", {"options": options}
    )
    authenticator_id = result["authenticatorId"]

    logger.info(f"Authenticator ID: {authenticator_id}")

    # add the credential created to virtual authenticator
    wait.until(
        EC.element_to_be_clickable((By.ID, "describe-webauthn-token-modal"))
    ).send_keys(Keys.RETURN)

    wait.until(
        EC.element_to_be_clickable((By.ID, "verify-webauthn-token-modal-close-link"))
    ).click()
    time.sleep(1)

    # Get credentials
    credentials_result = driver.execute_cdp_cmd(
        "WebAuthn.getCredentials", {"authenticatorId": authenticator_id}
    )

    # Serialize data
    auth_data = {
        "authenticator_id": authenticator_id,
        "options": options,
        "credentials": credentials_result["credentials"],
    }

    with open("eduid_data.json", "w") as f:
        json.dump(auth_data, f, indent=2)

    logger.info("Registration successful and credentials saved!")
    logger.info(f"Saved {len(credentials_result['credentials'])} credential(s)")
    time.sleep(5)


except Exception as error:
    logger.error(f"Something wrong: {error}")
    time.sleep(600)

logger.info("DONE!")
