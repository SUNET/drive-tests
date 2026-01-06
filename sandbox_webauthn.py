import logging
import time
from base64 import urlsafe_b64decode

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
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
logger.info("Start webauthn.io registration")
delay = 30

# Generate a new RSA private key (2048 bits)
gen_pk = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Export the private key in PEM format (PKCS8, unencrypted)
pem = (
    gen_pk.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode()
    .strip(f"-----BEGIN PRIVATE KEY-----")
    .rstrip()
    .rstrip(f"-----END PRIVATE KEY-----")
    .lstrip()
    .rstrip()
)

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
privatekey = urlsafe_b64decode(pem)
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

logger.info(f"Private key registered:")
logger.info(f"\r\n{pem}")

logger.info("DONE!")
