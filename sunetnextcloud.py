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

g_testtarget = os.environ.get('NextcloudTestTarget')
g_testcustomers = os.environ.get('NextcloudTestCustomers')
g_testbrowsers = os.environ.get('NextcloudTestBrowsers')
g_expectedFile = 'expected.yaml'

def get_value(env):
    value = os.environ.get(env)
    if value == None:
        msg = f'Environment variable {env} is not set!'
        raise Exception(msg)
    return value

class TestTarget(object):
    with open(g_expectedFile, 'r') as stream:
        expectedResults=yaml.safe_load(stream)

    baseurl = expectedResults['global']['baseUrl']
    testprefix = expectedResults['global']['testPrefix']
    nodeprefix = expectedResults['global']['nodePrefix']
    docprefix = expectedResults['global']['docPrefix']
    testgss = expectedResults['global']['testGss']
    indexsuffix = expectedResults['global']['indexSuffix']

    # default target is test, unless overwritten by initializing with 'prod'
    targetprefix = '.' + testprefix

    allnodes = expectedResults['global']['allnodes']
    fullnodes = expectedResults['global']['fullnodes']
    multinodes = expectedResults['global']['multinodes']
    browsers = expectedResults['global']['testBrowsers']

    target = 'test'
    platform = sys.platform

    def __init__(self, target='test'):
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        os.chdir(dname)
        print('Change working directory to :',dname)
        if g_testtarget == "prod":
            self.target = "prod"
            self.targetprefix = ""
        else:
            self.target = "test"
            self.targetprefix = "." + self.testprefix

        if g_testcustomers in self.allnodes:
            self.allnodes = [g_testcustomers]
            self.fullnodes = self.allnodes
            self.multinodes = self.allnodes

        # Override browsers to test from expected.yaml with value(s) in environment variable
        if g_testbrowsers is not None:
            self.browsers = g_testbrowsers.split(",")

    def getnodeprefix(self, node):
        if (node == 'gss' or node == 'none'):
            prefix = self.nodeprefix
        elif len(self.nodeprefix) == 0:
            prefix = node
        else:
            prefix = node + '.' + self.nodeprefix
        return prefix

    def get_gss_url(self):
        if self.target == "prod":
            return 'https://drive.' + self.baseurl
        else:
            return 'https://drive.test.' + self.baseurl

    def get_node_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl

    def get_gss_post_logout_url(self):
        if self.target == "prod":
            return 'https://drive.' + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/selectUserBackEnd?redirectUrl='
        else:
            return 'https://drive.test.' + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/selectUserBackEnd?redirectUrl='

    def get_node_login_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/login?redirect_url=&direct=1'

    def get_node_post_logout_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/login?clear=1'

    def get_node_post_logout_simple_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/login'

    def get_node_post_logout_saml_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/selectUserBackEnd?redirectUrl='

    def get_ocs_capabilities_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v1.php/cloud/capabilities?format=json'

    def get_all_apps_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v2.php/cloud/apps?format=json'

    def get_app_url(self, node, app):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v2.php/cloud/apps/' + app + '?format=json'

    def get_add_user_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v1.php/cloud/users?format=json'

    def get_user_url(self, node, username):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v1.php/cloud/users/' + username + '?format=json'

    def get_disable_user_url(self, node, username):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v1.php/cloud/users/' + username + '/disable?format=json'

    def get_dashboard_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/apps/dashboard/'

    def get_folder_url(self, node, foldername):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/apps/files/?dir=/' + foldername

    def get_webdav_url(self, node, username):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/remote.php/dav/files/' + username + '/'
 
    def get_file_lock_url(self, node, filename):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v2.php/apps/files_lock/lock/' + filename

    def get_file_lock_curl(self, node, username, filename):
        return 'curl -X LOCK --url https://' + username + ':$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/remote.php/dav/files/' + username + '/' + filename + ' --header \'X-User-Lock: 1\''

    def get_file_unlock_curl(self, node, username, filename):
        return 'curl -X UNLOCK --url https://' + username + ':$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/remote.php/dav/files/' + username + '/' + filename + ' --header \'X-User-Lock: 1\''

    def get_serverinfo_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + '/ocs/v2.php/apps/serverinfo/api/v1/info?format=json'

    def get_gss_metadata_url(self):
        return 'https://drive' + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/metadata?idp=1'

    def get_metadata_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/metadata?idp=1'

    def get_gss_entity_id(self):
        return 'https://drive' + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/metadata'

    def get_node_entity_id(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.' + self.baseurl + self.indexsuffix + '/apps/user_saml/saml/metadata'

    def get_collabora_node_url(self, node):
        if len(self.nodeprefix) == 0:
            return 'https://' + self.docprefix + str(node) + self.targetprefix + '.' + self.baseurl + '' 
        return 'https://' + self.docprefix + str(node) + '.' + self.getnodeprefix('none') + self.targetprefix + '.' + self.baseurl + ''

    def get_collabora_capabilities_url(self, node):
        if len(self.nodeprefix) == 0:
            return 'https://' + self.docprefix + str(node) + self.targetprefix + '.' + self.baseurl + '/hosting/capabilities'
        return 'https://' + self.docprefix + str(node) + '.' + self.getnodeprefix('none') + self.targetprefix + '.' + self.baseurl + '/hosting/capabilities'

    def get_fullnode_status_urls(self):
        nodeurls = []
        for node in self.fullnodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + '.' + self.baseurl + "./status.php" )
        return nodeurls

    def get_multinode_status_urls(self):
        nodeurls = []
        for node in self.multinodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + '.' + self.baseurl + "./status.php" )
        return nodeurls

    def get_allnode_status_urls(self):
        nodeurls = []
        for node in self.allnodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + '.' + self.baseurl + "./status.php" )
        return nodeurls

    def get_webdav_root(self, username):
        return '/remote.php/dav/files/' + username + '/'

    def get_ocsuser(self, node):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsUser ' + node + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_OCS_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_seleniumuser(self, node):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUser ' + node + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_seleniummfauser(self, node):
        if self.platform == 'win32':
            usercmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUser ' + node + ' ' + self.target + ' }"'
            process = os.popen(usercmd)
            user = process.read()
            process.close()
            return user
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_USER_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
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

    def get_ocsuserpassword(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_OCS_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_seleniumuserpassword(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_seleniummfauserpassword(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
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

    def get_ocsuserapppassword(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-OcsAppPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_OCS_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_seleniumuserapppassword(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumUserAppPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_seleniummfauserapppassword(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserAppPassword ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
        else:
            raise NotImplementedError

    def get_seleniummfausertotpsecret(self, node):
        if self.platform == 'win32':
            pwdcmd = 'powershell -command "& { . ./NodeCredentials.ps1; Get-SeleniumMfaUserTotpSecret ' + node + ' ' + self.target + ' }"'
            process = os.popen(pwdcmd)
            pwd = process.read()
            process.close()
            return pwd
        elif self.platform == 'linux':
            env = "NEXTCLOUD_SELENIUM_MFA_SECRET_" + node.upper() + "_" + self.target.upper()
            return get_value(env)
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
        