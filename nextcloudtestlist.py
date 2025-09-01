#!/usr/bin/env python3

import argparse
import yaml
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

configFile = 'tests.yaml'
parser = argparse.ArgumentParser(description="List test files to be executed for given test type",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('type', choices = ['acceptance', 'selenium', 'seleniumtotp', 'collabora', 'node', 'performance', 'all'], help="Type")
args = parser.parse_args()
config = vars(args)

with open(configFile, "r") as stream:
    tests=yaml.safe_load(stream)

    allfiles=[]
    if args.type == 'all':
        for category, files in tests.items():
            if isinstance(files, list):
                for file in files:
                    allfiles.append(file)
        for file in set(allfiles):
            print(file)
        sys.exit()
        
    testfiles=tests[args.type]
    for testfile in testfiles:
        print(testfile)
