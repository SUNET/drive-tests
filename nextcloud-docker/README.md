# Sunet Drive local testing
## Quickstart
If you want to see something quick, you can create a python virtual environment, install all requirements and run all tests. We assume that you work in a clean environment and there are no port or name conflicts with other containers. Please have Firefox as a browser installed on the local system.

    $ mkvirtualenv nextcloud-local
    $ pip install -r ../requirements.txt
    $ make testall

During the process, a number of unittests will be executed: acceptance tests, login tests and Collabora tests. This includes tests based on Selenium which means a few automated browser windows will open and execute the tests. Once the tests are finished, the html unit test results will be opened in the browser. If you want to further explore the deployment, the following (local) pages are a good start:
* Nextcloud: https://localhost:8443
* Jupyterhub: https://localhost:9444
* RDS NG: https://localhost:9445/ or http://localhost:4200
* MinIO: http://localhost:9000
* Mock OAuth: https://localhost:9446 or http://localhost:8080


**Note:** If you want to make sure that you work in a clean environment, you can also run `make cleantestall`, which prunes your local docker deployment, including all volumes and images. You will get 5 seconds to cancel this operation.  **You have been warned!**

## Containers and local services


## Docker compose and Makefile
With this local Nextcloud environment, you can execute most, if not all, automated tests that Sunet uses to test their Sunet Drive environment. The local deployment uses a (single-node) architecture that is as close to the Sunet Drive deployment as possible. The majority of the configuration is done in a `docker-compose.yaml` and a `Makefile`. The compose file contains configurations for:
* Nextcloud - [nextcloud:latest](https://hub.docker.com/_/nextcloud/) with a self-signed certificate
* MariaDB - [mariadb:latest](https://hub.docker.com/_/mariadb)
* MinIO - [minio:latest](https://quay.io/repository/minio/minio) with a configuration inspired by their [docker-compose example](https://github.com/minio/minio/blob/master/docs/orchestration/docker-compose/docker-compose.yaml)
* Whiteboard - []
* JupyterHub (WIP) - A locally built JupyterHub
* Mock OAuth Server (WIP) [mock-oauth2-server:2.1.1](https://ghcr.io/navikt/mock-oauth2-server)


