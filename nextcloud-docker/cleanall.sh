#!/bin/bash

echo Prune system and voumes and remove containers, images and volumes in 5s. Press Ctrl-C to cancel.
for i in {5..1}; do echo $i & sleep 1; done

docker rm -vf $(docker ps -aq)
docker rmi -f $(docker images -aq)
docker system prune -f
docker volume prune -f
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
docker volume rm nextcloud
docker volume rm rds_data1-1
docker volume rm rds_data1-2
docker volume rm rds_data2-1
docker volume rm rds_data2-2
docker volume rm rds_data3-1
docker volume rm rds_data3-2
docker volume rm rds_data4-1
docker volume rm rds_data4-2
docker volume rm rds_db
docker volume rm rds_nextcloud
docker volume rm $(docker volume ls -qf dangling=true)