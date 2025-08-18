#!/usr/bin/env python3

import argparse
import sunetnextcloud
import pyotp
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
parser = argparse.ArgumentParser(description="Print TOTP code for selenium mfa user",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('customer', help="Customer node")
parser.add_argument('environment', choices = ['test', 'prod','custom'], help="Environment")
args = parser.parse_args()
config = vars(args)

drv = sunetnextcloud.TestTarget(args.environment)
nodetotpsecret = drv.get_seleniummfausertotpsecret(args.customer)

totp = pyotp.TOTP(nodetotpsecret)
print(f'OTP for user {drv.get_seleniummfauser(args.customer)} in {args.environment}')
print(totp.now())