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
    # Load saved data
    with open("webauthn_data.json", "r") as f:
        auth_data = json.load(f)

    # Increase sign count by one and save the json for the next login
    print(f"Virtual authenticator has been used {auth_data["credentials"][0]["signCount"]} times")
    auth_data["credentials"][0]["signCount"] += 1
    with open("webauthn_data.json", "w") as f:
        json.dump(auth_data, f, indent=2)

    driver.get("https://webauthn.io")

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

    print(f"Restored {len(auth_data['credentials'])} credential(s)")

    # Perform login
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "input-email"))
    )
    username_field.send_keys(auth_data["credentials"][0]["userName"])

    login_button = driver.find_element(By.ID, "login-button")
    login_button.click()

    # Wait for success
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "btn-primary"))
    )

    print("Login successful with restored credentials!")
    time.sleep(5)

finally:
    driver.quit()
