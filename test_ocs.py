""" Testing OCS functions for Sunet Drive
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import time

import sunetdrive

ocsheaders = { "OCS-APIRequest" : "true" } 

class TestOcsCalls(unittest.TestCase):
    def test_capabilities_nouser(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_ocs_capabilities_url(fullnode)
                print(self._testMethodName, url)
                r=requests.get(url, headers=ocsheaders)
                try:
                    j = json.loads(r.text)
                except:
                    print("No JSON reply received")
                    print(r.text)

                if drv.target == 'prod':
                    ocsresult = sunetdrive.OcsCapabilitiesResult
                else:
                    ocsresult = sunetdrive.OcsCapabilitiesResultTest

                self.assertEqual(j["ocs"]["meta"]["status"], ocsresult.ocs_meta_status)
                self.assertEqual(j["ocs"]["meta"]["statuscode"], ocsresult.ocs_meta_statuscode)
                self.assertEqual(j["ocs"]["meta"]["message"], ocsresult.ocs_meta_message)
                self.assertEqual(j["ocs"]["data"]["version"]["string"], ocsresult.ocs_data_version_string)

    def test_capabilities(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_ocs_capabilities_url(fullnode)
                print(self._testMethodName, url)
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserpassword(fullnode)

                r=requests.get(url, headers=ocsheaders, auth = HTTPBasicAuth(nodeuser, nodepwd))
                try:
                    j = json.loads(r.text)
                except:
                    print("No JSON reply received")
                    print(r.text)
                ocsresult = sunetdrive.OcsCapabilitiesResult
                # self.assertEqual(j["ocs"]["data"]["capabilities"]["globalscale"]["enabled"], ocsresult.ocs_data_capabilities_globalscale_enabled)

    def test_gssusers(self):
        drv = sunetdrive.TestTarget()
        fullnode = 'gss'
        url = drv.get_add_user_url(fullnode)
        print(self._testMethodName, url)
        nodeuser = drv.get_ocsuser(fullnode)
        nodepwd = drv.get_ocsuserapppassword(fullnode)
        url = url.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)

        r = requests.get(url, headers=ocsheaders)
        try:
            j = json.loads(r.text)
            print(json.dumps(j, indent=4, sort_keys=True))
            users = j["ocs"]["data"]["users"]
            print(users)
        except:
            print("No JSON reply received")
            print(r.text)

    def test_nodeusers(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                url = drv.get_add_user_url(fullnode)
                print(self._testMethodName, url)
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)

                r = requests.get(url, headers=ocsheaders)
                try:
                    j = json.loads(r.text)
                    print(json.dumps(j, indent=4, sort_keys=True))
                    users = j["ocs"]["data"]["users"]
                    print(users)
                except:
                    print("No JSON reply received")
                    print(r.text)

    def test_userlifecycle(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                session = requests.Session()
                url = drv.get_add_user_url(fullnode)
                # print(self._testMethodName, url)
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)

                cliuser = "__cli_user_" + fullnode
                clipwd = sunetdrive.Helper().get_random_string(12)

                data = { 'userid': cliuser, 'password': clipwd}

                print("Create cli user " + cliuser)
                r = session.post(url, headers=ocsheaders, data=data)
                try:
                    j = json.loads(r.text)
                    print(json.dumps(j, indent=4, sort_keys=True))
                    ocsresult = sunetdrive.OcsCapabilitiesResult

                    if (j["ocs"]["meta"]["statuscode"] == 996):
                        print("Create cli user after internal server error" + cliuser)
                        r = session.post(url, headers=ocsheaders, data=data)
                        j = json.loads(r.text)
                        print(json.dumps(j, indent=4, sort_keys=True))
                except:
                    print("No JSON reply received")
                    print(r.text)

                # self.assertEqual(j["ocs"]["meta"]["status"], ocsresult.ocs_meta_status)
                # self.assertEqual(j["ocs"]["meta"]["statuscode"], ocsresult.ocs_meta_statuscode)
                # self.assertEqual(j["ocs"]["meta"]["message"], ocsresult.ocs_meta_message)

                print("Disable cli user " + cliuser)
                disableuserurl = drv.get_disable_user_url(fullnode, cliuser)
                disableuserurl = disableuserurl.replace("$USERNAME$", nodeuser)
                disableuserurl = disableuserurl.replace("$PASSWORD$", nodepwd)
                r = session.put(disableuserurl, headers=ocsheaders)
                try:
                    j = json.loads(r.text)
                    print(json.dumps(j, indent=4, sort_keys=True))

                    if (j["ocs"]["meta"]["statuscode"] == 996):
                        print("Disable cli user after internal server error" + cliuser)
                        r = session.put(disableuserurl, headers=ocsheaders)
                        j = json.loads(r.text)
                        print(json.dumps(j, indent=4, sort_keys=True))

                    self.assertEqual(j["ocs"]["meta"]["status"], ocsresult.ocs_meta_status)
                    self.assertEqual(j["ocs"]["meta"]["statuscode"], ocsresult.ocs_meta_statuscode)
                    self.assertEqual(j["ocs"]["meta"]["message"], ocsresult.ocs_meta_message)

                    print("Delete cli user " + cliuser)
                    userurl = drv.get_user_url(fullnode, cliuser)
                    userurl = userurl.replace("$USERNAME$", nodeuser)
                    userurl = userurl.replace("$PASSWORD$", nodepwd)
                    r = session.delete(userurl, headers=ocsheaders)
                    j = json.loads(r.text)
                    print(json.dumps(j, indent=4, sort_keys=True))

                    if (j["ocs"]["meta"]["statuscode"] == 996):
                        print("Delete cli user after internal server error" + cliuser)
                        r = session.delete(userurl, headers=ocsheaders)
                        j = json.loads(r.text)
                        print(json.dumps(j, indent=4, sort_keys=True))

                    self.assertEqual(j["ocs"]["meta"]["status"], ocsresult.ocs_meta_status)
                    self.assertEqual(j["ocs"]["meta"]["statuscode"], ocsresult.ocs_meta_statuscode)
                    self.assertEqual(j["ocs"]["meta"]["message"], ocsresult.ocs_meta_message)
                except:
                    print("No JSON reply received")
                    print(r.text)

    def test_app_versions(self):
        drv = sunetdrive.TestTarget()
        for fullnode in drv.fullnodes:
            with self.subTest(mynode=fullnode):
                userSamlFound = False
                gssFound = False

                session = requests.Session()
                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserapppassword(fullnode)
                url = drv.get_all_apps_url(fullnode)

                print(url)
                url = url.replace("$USERNAME$", nodeuser)
                url = url.replace("$PASSWORD$", nodepwd)

                nodeuser = drv.get_ocsuser(fullnode)
                nodepwd = drv.get_ocsuserpassword(fullnode)

                r=session.get(url, headers=ocsheaders)
                nodeApps = []
                try:
                    j = json.loads(r.text)
                    # print(json.dumps(j, indent=4, sort_keys=True))
                    apps = j["ocs"]["data"]["apps"]
                except:
                    print(f'No JSON reply received')
                    print(r.text)

                if 'user_saml' in apps:
                    userSamlFound = True
                if 'globalsiteselector' in apps:
                    gssFound = True

                # # user_saml check
                if userSamlFound:
                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserapppassword(fullnode)
                    url = drv.get_app_url(fullnode, 'user_saml')

                    print(url)
                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)

                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserpassword(fullnode)

                    if drv.target == 'prod':
                        appsamlresult = sunetdrive.AppUserSamlResult
                    else:
                        appsamlresult = sunetdrive.AppUserSamlResultTest

                    r=session.get(url, headers=ocsheaders)
                    try:
                        j = json.loads(r.text)
                        # print(json.dumps(j, indent=4, sort_keys=True))
                        print(j["ocs"]["data"]["id"])
                        print(j["ocs"]["data"]["version"])
                        
                    except:
                        print(f'No JSON reply received')
                        print(r.text)

                    self.assertTrue(userSamlFound)
                    self.assertEqual(j["ocs"]["data"]["id"], appsamlresult.id)
                    self.assertEqual(j["ocs"]["data"]["version"], appsamlresult.version)

                # # global site selector check
                if gssFound:
                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserapppassword(fullnode)
                    url = drv.get_app_url(fullnode, 'globalsiteselector')

                    print(url)
                    url = url.replace("$USERNAME$", nodeuser)
                    url = url.replace("$PASSWORD$", nodepwd)

                    nodeuser = drv.get_ocsuser(fullnode)
                    nodepwd = drv.get_ocsuserpassword(fullnode)

                    if drv.target == 'prod':
                        appgssresult = sunetdrive.AppGssResult
                    else:
                        appgssresult = sunetdrive.AppGssResultTest

                    r=session.get(url, headers=ocsheaders)
                    try:
                        j = json.loads(r.text)
                        print(j["ocs"]["data"]["id"])
                        print(j["ocs"]["data"]["version"])
                        # print(json.dumps(j, indent=4, sort_keys=True))
                    except:
                        print(f'No JSON reply received')
                        print(r.text)

                    self.assertTrue(gssFound)
                    self.assertEqual(j["ocs"]["data"]["id"], appgssresult.id)
                    self.assertEqual(j["ocs"]["data"]["version"], appgssresult.version)

                # Summary and test
                print(f'Saml app found: {userSamlFound}')
                print(f'Gss app found: {gssFound}')


if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
