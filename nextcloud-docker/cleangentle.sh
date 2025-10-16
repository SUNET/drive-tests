#!/bin/bash

# echo Prune system and voumes and remove containers, images and volumes in 5s. Press Ctrl-C to cancel.
# for i in {5..1}; do echo $i & sleep 1; done

# docker rm -vf $(docker ps -aq)
# docker rmi -f $(docker images -aq)
# docker system prune -f
# docker volume prune -f

docker compose down

docker kill nextcloud-local 2&> /dev/null || true
docker kill nextcloud-local-db 2&> /dev/null || true
docker kill nextcloud-local-whiteboard 2&> /dev/null || true
docker kill nextcloud-local-minio 2&> /dev/null || true
docker kill nextcloud-local-minio1-1 2&> /dev/null || true
docker kill nextcloud-local-minio2-1 2&> /dev/null || true
docker kill nextcloud-local-minio3-1 2&> /dev/null || true
docker kill nextcloud-local-minio4-1 2&> /dev/null || true

docker rm -vf nextcloud-local
docker rm -vf nextcloud-local-db
docker rm -vf nextcloud-whiteboard
docker rm -vf nextcloud-local-nginx
docker rm -vf nextcloud-local-minio1-1
docker rm -vf nextcloud-local-minio2-1
docker rm -vf nextcloud-local-minio3-1
docker rm -vf nextcloud-local-minio4-1

docker rmi -f quay.io/minio/minio
docker rmi -f nextcloud
docker rmi -f mariadb
docker rmi -f ghcr.io/nextcloud-releases/whiteboard:release
docker rmi -f nginx

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

rmdir /tmp/localhost.pem