import argparse
import sunetnextcloud
import os
import pyotp

parser = argparse.ArgumentParser(description="Print TOTP code for selenium mfa user",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('customer', help="Customer node")
parser.add_argument('environment', choices = ['test', 'prod'], help="Environment")
args = parser.parse_args()
config = vars(args)

drv = sunetnextcloud.TestTarget(args.environment)
nodetotpsecret = drv.get_seleniummfausertotpsecret(args.customer)

totp = pyotp.TOTP(nodetotpsecret)
print(totp.now())