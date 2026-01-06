import base64
import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)

try:
    driver.get("https://webauthn.io")

    # IMPORTANT: Enable WebAuthn domain first
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

    print(f"Authenticator ID: {authenticator_id}")

    # Perform registration
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "input-email"))
    )
    username_field.send_keys("webauthn_dummy")

    register_button = driver.find_element(By.ID, "register-button")
    register_button.click()

    # Wait for success
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
    )

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

    with open("webauthn_data.json", "w") as f:
        json.dump(auth_data, f, indent=2)

    print("Registration successful and credentials saved!")
    print(f"Saved {len(credentials_result['credentials'])} credential(s)")
    time.sleep(5)

finally:
    driver.quit()
