""" Testing Storage functions for Sunet Drive including users and buckets
Author: Richard Freitag <freitag@sunet.se>
"""

import unittest
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import yaml

import sunetdrive

g_testtarget = os.environ.get('DriveTestTarget')
repobase='sunet-drive-ops/'
expectedResultsFile = 'expected.yaml'

class TestStorage(unittest.TestCase):
    with open(expectedResultsFile, "r") as stream:
        expectedResults=yaml.safe_load(stream)

    def test_existingbuckets(self):
        drv = sunetdrive.TestTarget(g_testtarget)
        premotes=os.popen('rclone listremotes')
        for remote in premotes.read().splitlines():
            print('Read: ',remote)
            pbuckets=os.popen('rclone lsjson ' + remote)
            buckets=pbuckets.read()
            print('Buckets: ', buckets)

    def test_fullnodestoragelocation(self):
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.fullnodes:
            with self.subTest(nodetotest=fullnode):
                configfile = repobase + fullnode + "-common/overlay/etc/hiera/data/group.yaml"
                with open(configfile, "r") as stream:
                    data=yaml.safe_load(stream)
                    self.assertEqual(data[drv.target]["s3_host"],self.expectedResults['storage']['mainStorageLocation'])

    def test_multinodestoragelocation(self):
        print('Test target: ', g_testtarget)
        drv = sunetdrive.TestTarget(g_testtarget)
        with open(repobase + "multinode-common/overlay/etc/hiera/data/group.yaml", "r") as stream:
            data=yaml.safe_load(stream)
            for multinode in drv.multinodes:
                with self.subTest(nodetotest=multinode):
                    print(multinode)
                    self.assertEqual(data[multinode][drv.target]["s3_host"],self.expectedResults['storage']['mainStorageLocation'])

    # Test if the primary and the mirror bucket exist at the right location
    def test_fullnode_primarybackupmirrorbuckets(self):
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.fullnodes:
            with self.subTest(nodetotest=fullnode):
                globalconfigfile = repobase + "/global/overlay/etc/hiera/data/common.yaml"
                with open(globalconfigfile, "r") as stream:
                    data=yaml.safe_load(stream)

                    prj=data["project_mapping"][fullnode][drv.target]

                    primary_project=prj['primary_project']
                    primary_bucket=prj['primary_bucket']
                    mirror_project=prj['mirror_project']
                    mirror_bucket=primary_bucket+'-mirror'

                    primarycmd='rclone lsjson ' + primary_project + ':'
                    mirrorcmd='rclone lsjson ' + mirror_project + ':'

                    pprimary_buckets=os.popen(primarycmd)
                    primary_buckets=json.loads(pprimary_buckets.read())
                    pprimary_buckets.close()
                    primary_bucket_found=False
                    for entry in primary_buckets:
                        if entry['Name'] == primary_bucket:
                            primary_bucket_found=True

                    if primary_bucket_found == False:
                        print('Primary project: ', primary_project, '\t Primary bucket found: ', primary_bucket, ' - ', primary_bucket_found)

                    pmirror_buckets=os.popen(mirrorcmd)
                    mirror_buckets=json.loads(pmirror_buckets.read())
                    pmirror_buckets.close()
                    mirror_bucket_found=False
                    for entry in mirror_buckets:
                        if entry['Name'] == mirror_bucket:
                            mirror_bucket_found=True

                    if mirror_bucket_found == False:
                        print('Mirror project: ', mirror_project, '\t Mirror bucket found: ', mirror_bucket, ' - ', mirror_bucket_found)

                    print('Mirror bucket found: ', mirror_bucket, ' - ', mirror_bucket_found)
                    self.assertTrue(primary_bucket_found)
                    self.assertTrue(mirror_bucket_found)

    # Test if the primary and the mirror bucket exist at the right location
    def test_multinode_primarybackupmirrorbuckets(self):
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.multinodes:
            with self.subTest(nodetotest=fullnode):
                globalconfigfile = repobase + "/global/overlay/etc/hiera/data/common.yaml"
                with open(globalconfigfile, "r") as stream:
                    data=yaml.safe_load(stream)

                    prj=data["project_mapping"][fullnode][drv.target]

                    primary_project=prj['primary_project']
                    primary_bucket=prj['primary_bucket']
                    mirror_project=prj['mirror_project']
                    mirror_bucket=primary_bucket+'-mirror'

                    primarycmd='rclone lsjson ' + primary_project + ':'
                    mirrorcmd='rclone lsjson ' + mirror_project + ':'

                    pprimary_buckets=os.popen(primarycmd)
                    primary_buckets=json.loads(pprimary_buckets.read())
                    pprimary_buckets.close()
                    primary_bucket_found=False
                    for entry in primary_buckets:
                        if entry['Name'] == primary_bucket:
                            primary_bucket_found=True

                    if primary_bucket_found == False:
                        print('Primary project: ', primary_project, '\t Primary bucket found: ', primary_bucket, ' - ', primary_bucket_found)

                    pmirror_buckets=os.popen(mirrorcmd)
                    mirror_buckets=json.loads(pmirror_buckets.read())
                    pmirror_buckets.close()
                    mirror_bucket_found=False
                    for entry in mirror_buckets:
                        if entry['Name'] == mirror_bucket:
                            mirror_bucket_found=True

                    if mirror_bucket_found == False:
                        print('Mirror project: ', mirror_project, '\t Mirror bucket found: ', mirror_bucket, ' - ', mirror_bucket_found)

                    print('Mirror bucket found: ', mirror_bucket, ' - ', mirror_bucket_found)
                    self.assertTrue(primary_bucket_found)
                    self.assertTrue(mirror_bucket_found)

    # Test if the number of buckets in the mirror project is the same in Sto4 and Sto3
    def test_project_mapping_primary_bucket_number(self):
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.fullnodes:
            with self.subTest(nodetotest=fullnode):
                globalconfigfile = repobase + "/global/overlay/etc/hiera/data/common.yaml"
                with open(globalconfigfile, "r") as stream:
                    data=yaml.safe_load(stream)
                    prj=data["project_mapping"][fullnode][drv.target]

                    primary_project=prj['primary_project']
                    primary_bucket=prj['primary_bucket']
                    mirror_project=prj['mirror_project']
                    mirror_bucket=primary_bucket+'-mirror'

                    primarycmd='rclone lsjson ' + primary_project + ':'
                    mirrorcmd='rclone lsjson ' + mirror_project + ':'

                    pprimary_buckets=os.popen(primarycmd)
                    primary_buckets=json.loads(pprimary_buckets.read())
                    pprimary_buckets.close()

                    pmirror_buckets=os.popen(mirrorcmd)
                    mirror_buckets=json.loads(pmirror_buckets.read())
                    pmirror_buckets.close()

                    # -1 because of db-backup-bucket
                    self.assertEqual(len(primary_buckets),(len(mirror_buckets)-1))

    # Test project buckets for consistency: Name, number of buckets, mirror bucket
    def test_fullnode_projectbucketconsistency(self):
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.fullnodes:
            with self.subTest(nodetotest=fullnode):
                globalconfigfile = repobase + "/global/overlay/etc/hiera/data/common.yaml"
                with open(globalconfigfile, "r") as stream:
                    data=yaml.safe_load(stream)

                    assigned=data["project_mapping"][fullnode][drv.target]["assigned"]
                    print(fullnode + " " + str(len(assigned)))

                    if len(assigned) > 0:
                        print(fullnode + " " + str(len(assigned)))
                        for buckets in assigned:
                            # print(buckets)
                            # print(buckets["buckets"])
                            primary_project_bucket=buckets["buckets"][0]
                            primary_project=buckets["project"]
                            mirror_project=buckets["mirror_project"]
                            mirror_project_bucket=primary_project_bucket+'-mirror'

                            primarycmd='rclone lsjson ' + primary_project + ':'
                            mirrorcmd='rclone lsjson ' + mirror_project + ':'

                            pprimary_buckets=os.popen(primarycmd)
                            primary_buckets=json.loads(pprimary_buckets.read())
                            pprimary_buckets.close()
                            primary_project_bucket_found=False
                            for entry in primary_buckets:
                                if entry['Name'] == primary_project_bucket:
                                    primary_project_bucket_found=True

                            pmirror_buckets=os.popen(mirrorcmd)
                            mirror_buckets=json.loads(pmirror_buckets.read())
                            pmirror_buckets.close()
                            mirror_project_bucket_found=False
                            for entry in mirror_buckets:
                                if entry['Name'] == mirror_project_bucket:
                                    mirror_project_bucket_found=True

                            print('Project bucket found: ', primary_project_bucket, ' - ', primary_project_bucket_found)
                            print('Mirror bucket found: ', mirror_project_bucket, ' - ', mirror_project_bucket_found)
                            self.assertTrue(primary_project_bucket_found)
                            self.assertTrue(mirror_project_bucket_found)

    # Test project buckets for consistency: Name, number of buckets, mirror bucket
    def test_multinode_projectbucketconsistency(self):
        drv = sunetdrive.TestTarget(g_testtarget)
        for fullnode in drv.multinodes:
            with self.subTest(nodetotest=fullnode):
                globalconfigfile = repobase + "/global/overlay/etc/hiera/data/common.yaml"
                with open(globalconfigfile, "r") as stream:
                    data=yaml.safe_load(stream)

                    assigned=data["project_mapping"][fullnode][drv.target]["assigned"]
                    print(fullnode + " " + str(len(assigned)))

                    if len(assigned) > 0:
                        print(fullnode + " " + str(len(assigned)))
                        for buckets in assigned:
                            # print(buckets)
                            # print(buckets["buckets"])
                            primary_project_bucket=buckets["buckets"][0]
                            primary_project=buckets["project"]
                            mirror_project=buckets["mirror_project"]
                            mirror_project_bucket=primary_project_bucket+'-mirror'

                            primarycmd='rclone lsjson ' + primary_project + ':'
                            mirrorcmd='rclone lsjson ' + mirror_project + ':'

                            pprimary_buckets=os.popen(primarycmd)
                            primary_buckets=json.loads(pprimary_buckets.read())
                            pprimary_buckets.close()
                            primary_project_bucket_found=False
                            for entry in primary_buckets:
                                if entry['Name'] == primary_project_bucket:
                                    primary_project_bucket_found=True

                            pmirror_buckets=os.popen(mirrorcmd)
                            mirror_buckets=json.loads(pmirror_buckets.read())
                            pmirror_buckets.close()
                            mirror_project_bucket_found=False
                            for entry in mirror_buckets:
                                if entry['Name'] == mirror_project_bucket:
                                    mirror_project_bucket_found=True

                            print('Project bucket found: ', primary_project_bucket, ' - ', primary_project_bucket_found)
                            print('Mirror bucket found: ', mirror_project_bucket, ' - ', mirror_project_bucket_found)
                            self.assertTrue(primary_project_bucket_found)
                            self.assertTrue(mirror_project_bucket_found)

    # Test if access to storage report folder works
    def test_storagereport(self):
        rclonecmd='rclone lsjson sunet-nextcloud:'

        prclonecmd=os.popen(rclonecmd)
        folderlist=json.loads(prclonecmd.read())
        prclonecmd.close()
        customerShareFound=False
        for folder in folderlist:
            # print(folder['Path'])
            if folder['Path'] == "DriveCustomerShare":
                customerShareFound=True
        self.assertTrue(customerShareFound)

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
