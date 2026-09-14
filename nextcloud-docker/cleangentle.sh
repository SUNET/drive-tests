#!/bin/bash
# Stop and remove this project's containers, networks, and volumes.
# Scoped to docker-compose.yml, so it stays correct as services are
# added/renamed/removed. Images are left in place so the next `make docker`
# doesn't have to re-pull/rebuild them.

docker compose down --volumes --remove-orphans
