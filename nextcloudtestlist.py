import argparse
import sunetnextcloud
import os
import yaml

configFile = 'tests.yaml'
parser = argparse.ArgumentParser(description="List test files to be executed for given test type",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('type', choices = ['acceptance', 'selenium', 'seleniumtotp', 'collabora', 'node'], help="Type")
args = parser.parse_args()
config = vars(args)

with open(configFile, "r") as stream:
    tests=yaml.safe_load(stream)
    testfiles=tests[args.type]
    for testfile in testfiles:
        print(testfile)
