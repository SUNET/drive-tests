#!/bin/bash
# Full teardown of this project: containers, networks, volumes, and every
# image docker-compose.yml pulled or built. Scoped to this compose project
# only (see docker-compose.yml) -- does not touch other containers or images
# on the host.

echo Removing this project\'s containers, volumes and images in 5s. Press Ctrl-C to cancel.
for i in {5..1}; do echo $i; sleep 1; done

docker compose down --volumes --rmi all --remove-orphans
