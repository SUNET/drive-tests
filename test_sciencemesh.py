""" Unit testing for sciencemesh
Author: Richard Freitag <freitag@sunet.se>

"""

import unittest
import requests
import json
import yaml

g_cs3url        = 'https://iop.sciencemesh.uni-muenster.de/iop/mentix/cs3'
g_sitesurl      = 'https://iop.sciencemesh.uni-muenster.de/iop/mentix/sites'
expectedResultsFile = 'expected.yaml'

class TestScienceMesh(unittest.TestCase):
    def test_cs3(self):
        statusCount = 0
        instanceCount = 0
        offlineCount = 0
        print("Testing CS3 URL")
        r=requests.get(g_cs3url)
        j = json.loads(r.text)
        for instance in j:
            instanceCount += 1
            print(instance["name"])
            
            hosturl = instance["services"][0]["host"]
            fullhosturl = "https://" + hosturl

            try:
                hr = requests.get(fullhosturl)
                # print("\tLIVE: " + hosturl)
                isLive = True
                # print(r.text)
            except:
                print("\t\t\t\tOffline: " + fullhosturl)
                offlineCount += 1
                isLive = False

            if (isLive):
                try:
                    statusUrl = fullhosturl + "/status.php"
                    sr = requests.get(statusUrl)
                    if ('installed' in sr.text):
                        statusCount += 1
                        hasStatus = True
                        print("\tStatus: ", statusUrl)
                except:
                    print("Status url not available: " + statusUrl)

            for service in instance["services"]:
                servicename = service["endpoint"]["type"]["name"]
                # print("\t", servicename)
                # if (servicename == "OCM"):
                #     print("\t\t\t\t OCM ENDPOINT FOUND")


                if not (service.get('additional_endpoints') is None):
                    for additionalEndpoint in service["additional_endpoints"]:
                        # print("\t\t", additionalEndpoint["type"]["name"])
                        if (additionalEndpoint["type"]["name"] == "METRICS"):
                            # print("\t\t\t", additionalEndpoint["path"])
                            metricsPath = additionalEndpoint["path"]
                            # try:
                            #     r=requests.get(metricsPath)
                            #     # print(r.text)
                            # except:
                            #     print("\t\t\t\t", "Metrics access failed")
                            # print(r.text)
                    # print("value is present for given JSON key")
                    # # print(service["additional_endpoints"]["type"]["name"])
                    # print(service["additional_endpoints"]["type"])
        print("Instances: ", instanceCount)
        print("Live sites: ", statusCount)
        print("Offline: ", offlineCount)

if __name__ == '__main__':
    import xmlrunner
    # unittest.main()
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
