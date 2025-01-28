# Sunet Drive local testing
## Quickstart
If you want to see something quick, you can create a python virtual environment, install all requirements and run all tests. We assume that you work in a clean environment and there are no port or name conflicts with other containers. 

    $ mkvirtualenv nextcloud-local
    $ pip install -r ../requirements.txt
    $ make testall

**Note:** If you want to make sure that you work in a clean environment, you can also run `make cleantestall`, which prunes your local docker deployment, including all volumes and images. You will get 5 seconds to cancel this operation.  **You have been warned!**

## Docker compose and Makefile
With this local Nextcloud environment, you can execute most, if not all, automated tests that Sunet uses to test their Sunet Drive environment. The local deployment uses a (single-node) architecture that is as close to the Sunet Drive deployment as possible. The majority of the configuration is done in a `docker-compose.yaml` and a `Makefile`. The compose file contains configurations for:
* Nextcloud - [nextcloud:latest](https://hub.docker.com/_/nextcloud/) with a self-signed certificate
* MariaDB - [mariadb:latest](https://hub.docker.com/_/mariadb)
* MinIO - [minio:latest](https://quay.io/repository/minio/minio) with a configuration inspired by their [docker-compose example](https://github.com/minio/minio/blob/master/docs/orchestration/docker-compose/docker-compose.yaml)
* Whiteboard - []
* JupyterHub (WIP) - A locally built JupyterHub
* Mock OAuth Server (WIP) [mock-oauth2-server:2.1.1](https://ghcr.io/navikt/mock-oauth2-server)


