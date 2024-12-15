import argparse
import sunetnextcloud
import os

g_firefoxCmd = 'firefox '
g_chromeCmd = 'google-chrome-stable '
g_exec = ''
g_execPrefix = ''
g_urlPrefix = ''

parser = argparse.ArgumentParser(description="Open Sunet Drive direct login pages in Firefox or Chrome",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('browser', choices = ['firefox', 'chrome'], help="Browser - firefox or chrome")
parser.add_argument('customer', help="Customer - <node>, all")
parser.add_argument('environment', choices = ['test', 'prod'], help="Environment")
args = parser.parse_args()
config = vars(args)

drv = sunetnextcloud.TestTarget(args.environment)

if args.browser == 'firefox':
    g_exec += g_firefoxCmd
    g_execPrefix += '-new-tab -url '
elif args.browser == 'chrome':
    g_exec += g_chromeCmd

if args.customer == 'all':
    for node in drv.allnodes:
        print(f'{node}')
        g_exec += g_execPrefix + "'" + drv.get_node_login_url(node) + "' "
elif args.customer == 'full':
    for node in drv.fullnodes:
        print(f'{node}')
        g_exec += g_execPrefix + "'" + drv.get_node_login_url(node) + "' "

else:
    g_exec += g_execPrefix + "'" + drv.get_node_login_url(args.customer) + "'"

os.system(g_exec)