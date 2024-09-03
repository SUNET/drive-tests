import pyotp
import argparse
import os
import yaml
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

envFile = '.env.yaml'

try:
    with open(envFile, "r") as stream:
        envVariables=yaml.safe_load(stream)
except:
    logger.error(f'Error opening {envFile}')
    sys.exit()

parser = argparse.ArgumentParser(description="TOTP Helper for MFA Zones docker testing",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('username', help="<username>")
# parser.add_argument('environment', choices = ['test', 'prod'], help="Environment")
args = parser.parse_args()
config = vars(args)

prefix = args.username.upper()
userMfaSecret = envVariables[f'MFA_NEXTCLOUD_{prefix}_SECRET']
print(pyotp.TOTP(userMfaSecret).now())