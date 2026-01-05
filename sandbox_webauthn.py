import logging
import time
from base64 import urlsafe_b64decode

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.virtual_authenticator import (
    Credential,
    VirtualAuthenticatorOptions,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE64__ENCODED_PK = """
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDbBOu5Lhs4vpowbCnmCyLUpIE7JM9sm9QXzye2G+jr+Kr
MsinWohEce47BFPJlTaDzHSvOW2eeunBO89ZcvvVc8RLz4qyQ8rO98xS1jtgqi1NcBPETDrtzthODu/gd0sjB2Tk3TLuBGV
oPXt54a+Oo4JbBJ6h3s0+5eAfGplCbSNq6hN3Jh9YOTw5ZA6GCEy5l8zBaOgjXytd2v2OdSVoEDNiNQRkjJd2rmS2oi9AyQ
FR3B7BrPSiDlCcITZFOWgLF5C31Wp/PSHwQhlnh7/6YhnE2y9tzsUvzx0wJXrBADW13+oMxrneDK3WGbxTNYgIi1PvSqXlq
GjHtCK+R2QkXAgMBAAECggEAVc6bu7VAnP6v0gDOeX4razv4FX/adCao9ZsHZ+WPX8PQxtmWYqykH5CY4TSfsuizAgyPuQ0
+j4Vjssr9VODLqFoanspT6YXsvaKanncUYbasNgUJnfnLnw3an2XpU2XdmXTNYckCPRX9nsAAURWT3/n9ljc/XYY22ecYxM
8sDWnHu2uKZ1B7M3X60bQYL5T/lVXkKdD6xgSNLeP4AkRx0H4egaop68hoW8FIwmDPVWYVAvo8etzWCtibRXz5FcNld9MgD
/Ai7ycKy4Q1KhX5GBFI79MVVaHkSQfxPHpr7/XcmpQOEAr+BMPon4s4vnKqAGdGB3j/E3d/+4F2swykoQKBgQD8hCsp6FIQ
5umJlk9/j/nGsMl85LgLaNVYpWlPRKPc54YNumtvj5vx1BG+zMbT7qIE3nmUPTCHP7qb5ERZG4CdMCS6S64/qzZEqijLCqe
pwj6j4fV5SyPWEcpxf6ehNdmcfgzVB3Wolfwh1ydhx/96L1jHJcTKchdJJzlfTvq8wwKBgQDeCnKws1t5GapfE1rmC/h4ol
L2qZTth9oQmbrXYohVnoqNFslDa43ePZwL9Jmd9kYb0axOTNMmyrP0NTj41uCfgDS0cJnNTc63ojKjegxHIyYDKRZNVUR/d
xAYB/vPfBYZUS7M89pO6LLsHhzS3qpu3/hppo/Uc/AM/r8PSflNHQKBgDnWgBh6OQncChPUlOLv9FMZPR1ZOfqLCYrjYEqi
uzGm6iKM13zXFO4AGAxu1P/IAd5BovFcTpg79Z8tWqZaUUwvscnl+cRlj+mMXAmdqCeO8VASOmqM1ml667axeZDIR867ZG8
K5V029Wg+4qtX5uFypNAAi6GfHkxIKrD04yOHAoGACdh4wXESi0oiDdkz3KOHPwIjn6BhZC7z8mx+pnJODU3cYukxv3WTct
lUhAsyjJiQ/0bK1yX87ulqFVgO0Knmh+wNajrb9wiONAJTMICG7tiWJOm7fW5cfTJwWkBwYADmkfTRmHDvqzQSSvoC2S7aa
9QulbC3C/qgGFNrcWgcT9kCgYAZTa1P9bFCDU7hJc2mHwJwAW7/FQKEJg8SL33KINpLwcR8fqaYOdAHWWz636osVEqosRrH
zJOGpf9x2RSWzQJ+dq8+6fACgfFZOVpN644+sAHfNPAI/gnNKU5OfUv+eav8fBnzlf1A3y3GIkyMyzFN3DE7e0n/lyqxE4H
BYGpI8g==
"""

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger.info("Start webauthn.io registration")
delay = 30

loginurl = "https://webauthn.io"
logger.info(f"Login url: {loginurl}")

auth_options = VirtualAuthenticatorOptions()
auth_options.is_user_verified = True
auth_options.has_user_verification = True
auth_options.is_user_consenting = True
auth_options.transport = VirtualAuthenticatorOptions.Transport.USB
auth_options.protocol = VirtualAuthenticatorOptions.Protocol.U2F
auth_options.has_resident_key = False

dummyuser = "webauthn_dummy"
logger.info(f"Logging in with {dummyuser}")

options = ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.add_virtual_authenticator(auth_options)

# parameters for Non Resident Credential
credential_id = bytearray({1, 2, 3, 4})
rp_id = "localhost"
privatekey = urlsafe_b64decode(BASE64__ENCODED_PK)
sign_count = 0

# create a non resident credential using above parameters
credential = Credential.create_non_resident_credential(
    credential_id, rp_id, privatekey, sign_count
)

# add the credential created to virtual authenticator
driver.add_credential(credential)

logger.info(f"Registration test")
driver.get(loginurl)
wait = WebDriverWait(driver, delay)

try:
    wait.until(EC.presence_of_element_located((By.ID, "input-email"))).send_keys(
        dummyuser
    )
    time.sleep(1)
    wait.until(EC.presence_of_element_located((By.ID, "register-button"))).click()
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-success")))
    wait.until(EC.presence_of_element_located((By.ID, "login-button"))).click()
    time.sleep(5)
except Exception as error:
    logger.error(f"Something wrong: {error}")

logger.info("DONE!")
