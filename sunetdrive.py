""" Sunet Drive Support Module for unit and general testing
Author: Richard Freitag <freitag@sunet.se>
TestTarget is a helper class containing node-information, as well as for saving and retrieving node-local usernames/passwords.
expected.yaml contains expected results when retrieving status.php from a Sunet Drive node 
"""
import os
import sys
import random
import string

g_testtarget = os.environ.get('DriveTestTarget')
g_testcustomers = os.environ.get('DriveTestCustomers')

class TestTarget(object):
    allnodes=["extern","sunet","su","kau","suni","scilifelab","hh","gih","ki","lu","uu","gu","kth","liu","umu","chalmers","slu","lnu",
    "mau","ltu","oru","miun","du","hj","hb","hig","hv","his","hkr","mdu","bth","rkh","hhs","fhs","uniarts","konstfack","esh","kmh",
    "shh","kkh","ths","nordunet","kb","kva","sics","sp","irf","vr","nrm","smhi","uhr","antagning","swamid","vinnova"]

    fullnodes=["extern","sunet","su","kau","suni","scilifelab","hh","gih","hkr","mdu","mau","hv","shh","bth","kmh","ltu","hb","his","lnu","uu"]

    multinodes=["ki","lu","uu","gu","kth","liu","umu","chalmers","slu","lnu",
    "mau","ltu","oru","miun","du","hj","hb","hig","hv","his","bth","rkh","hhs","fhs","uniarts","konstfack","esh","kmh",
    "shh","kkh","ths","nordunet","kb","kva","sics","sp","irf","vr","nrm","smhi","uhr","antagning","swamid","vinnova"]

    # default target is test, unless overwritten by initializing with 'prod'
    targetprefix = '.test'

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
            self.targetprefix = ".test"

        if g_testcustomers in self.allnodes:
            self.allnodes = [g_testcustomers]
            self.fullnodes = self.allnodes
            self.multinodes = self.allnodes

    def getnodeprefix(self, node):
        if node == 'gss':
            prefix = 'drive'
        else:
            prefix = node + '.drive'
        return prefix

    def get_gss_url(self):
        if self.target == "prod":
            return "https://drive.sunet.se"
        else:
            return "https://drive.test.sunet.se"

    def get_node_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se'

    def get_gss_post_logout_url(self):
        if self.target == "prod":
            return 'https://drive.sunet.se/index.php/apps/user_saml/saml/selectUserBackEnd?redirectUrl='
        else:
            return 'https://drive.test.sunet.se/index.php/apps/user_saml/saml/selectUserBackEnd?redirectUrl='

    def get_node_login_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/index.php/login?redirect_url=&direct=1'

    def get_node_post_logout_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/index.php/login?clear=1'

    def get_node_post_logout_saml_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/index.php/apps/user_saml/saml/selectUserBackEnd?redirectUrl='

    def get_ocs_capabilities_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v1.php/cloud/capabilities?format=json'

    def get_all_apps_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v2.php/cloud/apps?format=json'

    def get_app_url(self, node, app):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v2.php/cloud/apps/' + app + '?format=json'

    def get_add_user_url(self, node):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v1.php/cloud/users?format=json'

    def get_user_url(self, node, username):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v1.php/cloud/users/' + username + '?format=json'

    def get_disable_user_url(self, node, username):
        return 'https://$USERNAME$:$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v1.php/cloud/users/' + username + '/disable?format=json'

    def get_dashboard_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/index.php/apps/dashboard/'

    def get_folder_url(self, node, foldername):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/index.php/apps/files/?dir=/' + foldername

    def get_webdav_url(self, node, username):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/remote.php/dav/files/' + username + '/'
 
    def get_file_lock_url(self, node, filename):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v2.php/apps/files_lock/lock/' + filename

    def get_file_lock_curl(self, node, username, filename):
        return 'curl -X LOCK --url https://' + username + ':$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/remote.php/dav/files/' + username + '/' + filename + ' --header \'X-User-Lock: 1\''

    def get_file_unlock_curl(self, node, username, filename):
        return 'curl -X UNLOCK --url https://' + username + ':$PASSWORD$@' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/remote.php/dav/files/' + username + '/' + filename + ' --header \'X-User-Lock: 1\''

    def get_serverinfo_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/ocs/v2.php/apps/serverinfo/api/v1/info?format=json'

    def get_gss_metadata_url(self):
        return 'https://drive' + self.targetprefix + '.sunet.se/index.php/apps/user_saml/saml/metadata?idp=1'

    def get_metadata_url(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/index.php/apps/user_saml/saml/metadata?idp=1'

    def get_gss_entity_id(self):
        return 'https://drive' + self.targetprefix + '.sunet.se/index.php/apps/user_saml/saml/metadata'

    def get_node_entity_id(self, node):
        return 'https://' + self.getnodeprefix(node) + self.targetprefix + '.sunet.se/index.php/apps/user_saml/saml/metadata'

    def get_fullnode_status_urls(self):
        nodeurls = []
        for node in self.fullnodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + ".sunet.se/status.php" )
        return nodeurls

    def get_multinode_status_urls(self):
        nodeurls = []
        for node in self.multinodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + ".sunet.se/status.php" )
        return nodeurls

    def get_allnode_status_urls(self):
        nodeurls = []
        for node in self.allnodes:
            nodeurls.append("https://" + self.getnodeprefix(node) +  self.targetprefix + ".sunet.se/status.php" )
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
            env = "DRIVE_OCS_USER_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SELENIUM_USER_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SELENIUM_MFA_USER_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_OCS_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SELENIUM_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SELENIUM_MFA_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_OCS_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SELENIUM_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SELENIUM_MFA_APP_PASSWORD_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SELENIUM_MFA_SECRET_" + node.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SAML_USER_" + userid.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SAML_PASSWORD_" + userid.upper() + "_" + self.target.upper()
            return os.environ.get(env)
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
            env = "DRIVE_SAML_PASSWORD_" + userid.upper() + "_" + self.target.upper()
            return os.environ.get(env)
        else:
            raise NotImplementedError

class Helper():
    def get_random_string(self, length):
        # With combination of lower and upper case
        result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
        # print random string
        return result_str
        