#!/bin/bash
cd /usr/local/jenkins-service
curl -sO https://testautomation.drive.sunet.dev/jnlpJars/agent.jar
java -jar agent.jar -url https://testautomation.drive.sunet.dev/ -secret @secret-file -name $(hostname) -workDir "/var/lib/jenkins"
exit 0