""" Generate expected_localhost.yaml file
Author: Richard Freitag <freitag@sunet.se>
Read the expected_localhost_template.yaml file and replace the values with the values from the locally installed instance
"""
import yaml
import sunetnextcloud

expectedResultsFile = 'expected_localhost_template.yaml'
with open(expectedResultsFile, "r") as stream:
    expectedResults=yaml.safe_load(stream)

# TBD: Read values from localhost instance

with open('expected_localhost.yaml', 'w') as outfile:
    yaml.dump(expectedResults, outfile, default_flow_style=False)
