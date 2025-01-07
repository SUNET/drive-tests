#!/bin/bash
docker rm -vf $(docker ps -aq)
docker rmi -f $(docker images -aq)
docker system prune
docker volume prune
docker volume rm nextcloud-docker_db
docker volume rm nextcloud-docker_nextcloud
docker volume rm nextcloud-docker_data1-1
docker volume rm nextcloud-docker_data1-2
docker volume rm nextcloud-docker_data2-1
docker volume rm nextcloud-docker_data2-2
docker volume rm nextcloud-docker_data3-1
docker volume rm nextcloud-docker_data3-2
docker volume rm nextcloud-docker_data4-1
docker volume rm nextcloud-docker_data4-2
