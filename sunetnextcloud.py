""" Sunet Drive Support Module for unit and general testing
Author: Richard Freitag <freitag@sunet.se>
TestTarget is a helper class containing node-information, as well as for saving and retrieving node-local usernames/passwords.
expected.yaml contains expected results when retrieving status.php from a Sunet Drive node 
"""
import os
import sys
import random
import string
import yaml
import logging
import time
import pyotp

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from enum import Enum

# Change to local directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

envtarget = os.environ.get('NextcloudTestTarget')
if envtarget == 'localhost':
    g_expectedFile = 'expected_localhost.yaml'
else:
    g_expectedFile = 'expected.yaml'

logger.info(f'Using test results file: {g_expectedFile}')

opsbase='sunet-drive-ops/'
opsCommonFile = opsbase + "/global/overlay/etc/hiera/data/common.yaml"
# opsCosmosDbFile = opsbase + "/global/overlay/etc/puppet/cosmos-db.yaml"

def get_value(env, raiseException = True):
    value = os.environ.get(env)
    if value == None:
        msg = f'Environment variable {env} is not set!'
        if raiseException == True:
            raise Exception(msg)
        else:
            logger.error(msg)
            pass
    return value

class TestTarget(object):
    with open(g_expectedFile, 'r') as stream:
        expectedResults=yaml.safe_load(stream)

    with open(opsCommonFile, 'r') as stream:
        opsCommonConfig=yaml.safe_load(stream)

    baseurl = expectedResults['global']['baseUrl']
    testprefix = expectedResults['global']['testPrefix']
    nodeprefix = expectedResults['global']['nodePrefix']
    docprefix = expectedResults['global']['docPrefix']
    indexsuffix = expectedResults['global']['indexSuffix']

    # default target is test, unless overwritten by initializing with 'prod'
    targetprefix = '.' + testprefix

    allnodes = expectedResults['global']['allnodes']
    fullnodes = expectedResults['global']['fullnodes']
    multinodes = expectedResults['global']['multinodes']
    browsers = expectedResults['global']['testBrowsers']
    singlenodetesting = False

    target = 'test'
    platform = sys.platform

    def __init__(self, target=None):
        global envtarget
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        logger.info(f'Working directory is {dname}')
        testcustomers = os.environ.get('NextcloudTestCustomers')
        testbrowsers = os.environ.get('NextcloudTestBrowsers')
        testrunner = os.environ.get('NextcloudTestRunner')
        testfilesize = os.environ.get('NextcloudTestFileSize')

        if testfilesize is None:
            logger.info(f'Using default file size M')
            self.testfilesize = 'M'
        elif (testfilesize == 'M') or (testfilesize == 'G'):
            logger.info(f'Using {testfilesize}B file size')
            self.testfilesize = testfilesize
        else:
            logger.warning(f'Unknown file size {testfilesize}B, using MB as default')
            self.testrunner = 'M'

        if testrunner is None:
            logger.info(f'Using default xml test runner')
            self.testrunner = 'xml'
        elif (testrunner == 'xml') or (testrunner == 'html'):
            logger.info(f'Using {testrunner} test runner')
            self.testrunner = testrunner
        else:
            logger.warning(f'Unknown testrunner {testrunner}, using html as default')
            self.testrunner = 'html'
        
        if target is not None:
            logger.info(f'Test target initialized by caller: {target}')
            testtarget = target
        elif envtarget is not None:
            logger.info(f'Test target initialized by environment variable: {envtarget}')
            testtarget = envtarget
        else:
            logger.warning(f'Test target initialized by default value: test')
            testtarget = 'test'

        if testtarget not in ['prod','test','localhost']:
            logger.error(f'Unsupported test target: {target}, exiting...')
            sys.exit()

        sys.stdout.flush()
        if testtarget == "prod":
            self.target = "prod"
            self.targetprefix = ""
        elif testtarget == "localhost":
            self.target = "localhost"
        else:
            self.target = "test"
            self.targetprefix = "." + self.testprefix

        if testcustomers in self.allnodes:
            self.singlenodetesting = True
            self.allnodes = [testcustomers]
            self.fullnodes = self.allnodes
            self.multinodes = self.allnodes

        # Override browsers to test from expected.yaml with value(s) in environment variable
        if testbrowsers is not None:
            self.browsers = testbrowsers.split(",")

        if testtarget == "localhost":
            self.targetprefix = ''
            self.nodeprefix = ''
            self.delimiter = ''
            self.verify = False     # Do not verify SSL when testing locally
        else:
            self.delimiter = '.'    # URL delimiter
            self.verify = True

    def getnodeprefix(self, node):
        if (node == 'none') or (node == 'localhost'):
            prefix = self.nodeprefix
        elif len(self.nodeprefix) == 0:
            prefix = node
        else:
            prefix = node + '.' + self.nodeprefix
        return prefix

    def is_multinode(self, node):
        try:
            self.opsCommonConfig['multinode_mapping'][node]['server']
            return True
        except:
            return False
        
    def get_multinode(self, node):
        return self.opsCommonConfig['multinode_mapping'][node]['server']
    
    def get_multinode_port(self, node):
        return self.opsCommonConfig['multinode_mapping'][node]['port']

    def get_node_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl

    def get_node_base_url(self, node):
        return self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl
    
    def get_base_url(self):
        return self.nodeprefix + self.targetprefix + self.delimiter + self.baseurl 

    def get_node_login_url(self, node, direct = True):
        if direct == True:
            return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/login?direct=1'
        else:
            return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix

    def get_login_url(self):
        return 'https://' + self.nodeprefix + self.targetprefix + self.delimiter + self.baseurl 

    def get_node_post_logout_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/login?clear=1'

    def get_node_post_logout_simple_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/login'

    def get_node_post_logout_saml_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/selectUserBackEnd?redirectUrl='

    def get_post_logout_url(self):
        if self.target == 'test':
            return 'https://service.seamlessaccess.org/ds/?entityID=https%3A%2F%2Fidp-proxy.drive.test.sunet.se%2Fsp&return=https%3A%2F%2Fdrive.test.sunet.se'
        elif self.target == 'prod':
            return 'https://service.seamlessaccess.org/ds/?entityID=https%3A%2F%2Fdrive-idp-proxy.sunet.se%2Fsp&return=https%3A%2F%2Fdrive.sunet.se'
        else:
            return 'TBD'

    def get_ocs_capabilities_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v2.php/cloud/capabilities?format=json'

    def get_all_apps_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v2.php/cloud/apps?format=json'

    def get_app_url(self, node, app):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v2.php/cloud/apps/' + app + '?format=json'

    def get_add_user_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v1.php/cloud/users?format=json'

    def get_add_group_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v1.php/cloud/groups?format=json'

    def get_add_user_fe_url(self, node, id):
        return 'https://$USERNAME$:$PASSWORD$@node' + str(id) + '.' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v1.php/cloud/users?format=json'

    def get_add_user_multinode_url(self, node):
        server = self.opsCommonConfig['multinode_mapping'][node]['server']
        port = self.opsCommonConfig['multinode_mapping'][node]['port']
        return 'https://$USERNAME$:$PASSWORD$@' + server + '.' + self.nodeprefix + self.targetprefix + self.delimiter + self.baseurl + ':' + str(port) + '/ocs/v1.php/cloud/users?format=json'

    def get_userinfo_url(self, node, userid):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v1.php/cloud/users/' + userid + '?format=json'

    def get_user_url(self, node, username):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v1.php/cloud/users/' + username + '?format=json'

    def get_disable_user_url(self, node, username):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v1.php/cloud/users/' + username + '/disable?format=json'

    def get_dashboard_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/apps/dashboard/'

    def get_folder_url(self, node, foldername):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/apps/files/?dir=/' + foldername

    def get_webdav_url(self, node, username):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/remote.php/dav/files/' + username + '/'
 
    def get_file_lock_url(self, node, filename):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v2.php/apps/files_lock/lock/' + filename

    def get_file_lock_curl(self, node, username, filename):
        return 'curl -X LOCK --url https://' + username + ':$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/remote.php/dav/files/' + username + '/' + filename + ' --header \'X-User-Lock: 1\''

    def get_file_unlock_curl(self, node, username, filename):
        return 'curl -X UNLOCK --url https://' + username + ':$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/remote.php/dav/files/' + username + '/' + filename + ' --header \'X-User-Lock: 1\''

    def get_shares_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json'

    def get_delete_share_url(self, node, id):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v2.php/apps/files_sharing/api/v1/shares/' + id

    def get_serverinfo_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + '/ocs/v2.php/apps/serverinfo/api/v1/info?format=json'

    def get_metadata_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/metadata?idp=1'

    def get_node_entity_id(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + self.delimiter + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/metadata'

    def get_collabora_node_url(self, node):
        if len(self.nodeprefix) == 0:
            return 'https://' + self.docprefix + str(node) + self.targetprefix + self.delimiter + self.baseurl + '' 
        return 'https://' + self.docprefix + str(node) + '.' + self.getnodeprefix('none') + self.targetprefix + self.delimiter + self.baseurl + ''

    def get_collabora_capabilities_url(self, node):
        if len(self.nodeprefix) == 0:
            return 'https://' + self.docprefix + str(node) + self.targetprefix + self.delimiter + self.baseurl + '/hosting/capabilities'
        return 'https://' + self.docprefix + str(node) + '.' + self.getnodeprefix('none') + self.targetprefix + self.delimiter + self.baseurl + '/hosting/capabilities'

    def get_fullnode_status_urls(self):
        nodeurls = []
        for node in self.fullnodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + self.delimiter + self.baseurl + "/status.php" )
        return nodeurls

    def get_multinode_status_urls(self):
        nodeurls = []
        for node in self.multinodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + self.delimiter + self.baseurl + "/status.php" )
        return nodeurls

    def get_allnode_status_urls(self):
        nodeurls = []
        for node in self.allnodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + self.delimiter + self.baseurl + "/status.php" )
        return nodeurls

    def get_status_url(self, node):
        return 'https://' + self.getnodeprefix(node) +  self.targetprefix + self.delimiter + self.baseurl + "/status.php"

    def get_node_status_url(self, node, id):
        return 'https://node' + str(id) + '.' + self.getnodeprefix(node) +  self.targetprefix + self.delimiter + self.baseurl + "/status.php"

    def get_webdav_root(self, username):
        return '/remote.php/dav/files/' + username + '/'

    def get_ocsuser(self, node, raiseException = True):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsUser ' + node + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_OCS_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniumuser(self, node, raiseException = True):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUser ' + node + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfauser(self, node, raiseException = True):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUser ' + node + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_jupyteruser(self, node):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUser ' + node + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_JUPYTER_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_ocsuserpassword(self, node, raiseException = True):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_OCS_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniumuserpassword(self, node, raiseException = True):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfauserpassword(self, node, raiseException = True):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_jupyteruserpassword(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_JUPYTER_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_ocsuserapppassword(self, node, raiseException = True):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsAppPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_OCS_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniumuserapppassword(self, node, raiseException = True):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserAppPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfauserapppassword(self, node, raiseException = True):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserAppPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def get_seleniummfausertotpsecret(self, node, raiseException = True):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserTotpSecret ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_SECRET_" + node.upper() + "_" + self.target.upper()
            return get_value(env, raiseException)
        else:
            raise NotImplementedError

    def save_ocsusercredentials(self, node):
        if self.platform == 'win32':
            cmd = 'powershell -command "& { . ./NodeCredentials.ps1; Save-OcsCredentials ' + node + ' ' + self.target + ' }"'
            os.system(cmd)
        elif self.platform == 'linux':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_seleniumusercredentials(self, node):
        if self.platform == 'win32':
            cmd = 'powershell -command "& { . ./NodeCredentials.ps1; Save-SeleniumCredentials ' + node + ' ' + self.target + ' }"'
            os.system(cmd)
        elif self.platform == 'linux':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_ocsuserappcredentials(self, node):
        if self.platform == 'win32':
            cmd = 'powershell -command "& { . ./NodeCredentials.ps1; Save-OcsAppCredentials ' + node + ' ' + self.target + ' }"'
            os.system(cmd)
        elif self.platform == 'linux':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_seleniumuserappcredentials(self, node):
        if self.platform == 'win32':
            cmd = 'powershell -command "& { . ./NodeCredentials.ps1; Save-SeleniumAppCredentials ' + node + ' ' + self.target + ' }"'
            os.system(cmd)
        elif self.platform == 'linux':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def get_samlusername(self, userid):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserName ' + userid + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SAML_USER_" + userid.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_samluseralias(self, userid):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserName ' + userid + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SAML_USER_" + userid.upper() + "_ALIAS_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_samluserpassword(self, userid):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserPassword ' + userid + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SAML_PASSWORD_" + userid.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_samlusertotpsecret(self, userid):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SamlUserTotpSecret ' + userid + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_SAML_MFA_SECRET_" + userid.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError        

    def save_samlusercredentials(self, userid):
        if self.platform == 'win32':
            cmd = 'powershell -command "& { . ./NodeCredentials.ps1; Save-SamlUserCredentials ' + userid + ' ' + self.target + ' }"'
            os.system(cmd)
        elif self.platform == 'linux':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def save_userappcredentials(self, userid, node):
        if self.platform == 'win32':
            cmd = 'powershell -command "& { . ./NodeCredentials.ps1; Save-UserAppCredentials ' + userid + ' ' + node + ' ' + self.target + ' }"'
            os.system(cmd)
        elif self.platform == 'linux':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def get_userapppassword(self, userid, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-UserAppPassword ' + userid + ' ' +  node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SAML_PASSWORD_" + userid.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

class Helper():
    def get_random_string(self, length):
        # With combination of lower and upper case
        result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
        # print random string
        return result_str

class SeleniumHelper():
    class UserType(Enum):
        SELENIUM = 1
        SELENIUM_MFA = 2
        OCS = 3
        BASIC = 4
        UNKNOWN = -1

    def __init__(self, driver, nextcloudnode) -> None:
        self.driver = driver
        self.nextcloudnode = nextcloudnode
        self.drv = TestTarget()
        delay = 30
        self.wait = WebDriverWait(self.driver, delay)
        pass

    def delete_cookies(self):
        cookies = self.driver.get_cookies()
        logger.info(f'Deleting all cookies')
        self.driver.delete_all_cookies()
        logger.info(f'All cookies deleted')
        return
    def nodelogin(self, usertype : UserType, username='', password='', apppwd='', totpsecret='', mfaUser=False):
        loginurl = self.drv.get_node_login_url(self.nextcloudnode)
        if usertype == usertype.SELENIUM:
            nodeuser = self.drv.get_seleniumuser(self.nextcloudnode)
            nodepwd = self.drv.get_seleniumuserpassword(self.nextcloudnode)
            nodeapppwd = self.drv.get_seleniumuserapppassword(self.nextcloudnode)
            nodetotpsecret = ''
            isMfaUser = False
        elif usertype == usertype.SELENIUM_MFA:
            nodeuser = self.drv.get_seleniummfauser(self.nextcloudnode)
            nodepwd = self.drv.get_seleniummfauserpassword(self.nextcloudnode)
            nodeapppwd = self.drv.get_seleniummfauserapppassword(self.nextcloudnode)
            nodetotpsecret = self.drv.get_seleniummfausertotpsecret(self.nextcloudnode)
            isMfaUser = True
        elif usertype == usertype.OCS:
            nodeuser = self.drv.get_ocsuser(self.nextcloudnode)
            nodepwd = self.drv.get_ocsuserpassword(self.nextcloudnode)
            nodeapppwd = self.drv.get_ocsuserapppassword(self.nextcloudnode)
            nodetotpsecret = ''
            isMfaUser = True
        elif usertype == usertype.BASIC:
            nodeuser = username
            nodepwd = password
            nodeapppwd = apppwd
            nodetotpsecret = totpsecret
            isMfaUser = mfaUser
        else:
            logger.error(f'Unknown usertype {usertype}')
            return False

        loggedIn = False
        loginurl = self.drv.get_node_login_url(self.nextcloudnode)
        self.driver.get(loginurl)
        if self.driver.current_url != loginurl:
            logger.warning(f'Retry opening login url: {loginurl}')
            self.driver.get(loginurl)

        try:
            logger.info(f'Enter username and password')
            self.wait.until(EC.element_to_be_clickable((By.ID, 'user'))).send_keys(nodeuser)
            self.wait.until(EC.element_to_be_clickable((By.ID, 'password'))).send_keys(nodepwd + Keys.ENTER)
            currentUrl = self.driver.current_url
        except:
            logger.error(f'Error logging in to {loginurl}')

        if isMfaUser:
            logger.info(f'MFA login {currentUrl}')
            if 'selectchallenge' in currentUrl:
                logger.info(f'Select TOTP provider')
                totpselect = self.driver.find_element(By.XPATH, '//a[@href="'+ self.drv.indexsuffix + '/login/challenge/totp' +'"]')
                totpselect.click()
            elif 'challenge/totp' in currentUrl:
                logger.info(f'No need to select TOTP provider')

            currentOtp = 0
            totpRetry = 0
            while totpRetry <= 3:
                totpRetry += 1
                totp = pyotp.TOTP(nodetotpsecret)
                currentOtp = totp.now()
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*//input[@placeholder="Authentication code"]'))).send_keys(currentOtp + Keys.ENTER)

                if 'challenge/totp' in self.driver.current_url:
                    logger.info(f'Try again')
                    while currentOtp == totp.now():
                        logger.info(f'Wait for new OTP to be issued')
                        time.sleep(3)
                else:
                    logger.info(f'Logging in to {self.nextcloudnode}')
                    break
        else:
            logger.info(f'No MFA login')

        # if 'apps/dashboard/' not in self.driver.current_url:
        #     logger.warning(f'Unknown post login URL: {self.driver.current_url}')

        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'app-menu')))
            logger.info(f'App menu is ready!')
        except TimeoutException:
            logger.info(f'Loading of app menu took too much time!')
        return True