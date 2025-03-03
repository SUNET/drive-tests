# Sunet Drive local testing
## Quickstart
If you want to see something quick, you can create a python virtual environment, install all requirements and run all tests. We assume that you work in a clean environment and there are no port or name conflicts with other containers. Please have Firefox as a browser installed on the local system.

    $ mkvirtualenv nextcloud-local
    $ pip install -r ../requirements.txt
    $ make testall

During the process, a number of unittests will be executed: acceptance tests, login tests and Collabora tests. This includes tests based on Selenium which means a few automated browser windows will open and execute the tests. Once the tests are finished, the html unit test results will be opened in the browser. If you want to further explore the deployment, the following (local) pages are a good start:
* Nextcloud: https://localhost:8443 or http://localhost:8880 (admin/adminpassword or you change it in the [Makefile](https://github.com/SUNET/drive-tests/blob/82e696b7b191cac2880fe87841331248ec5889e6/nextcloud-docker/Makefile#L91))
* Jupyterhub: https://localhost:9444
* RDS NG: https://localhost:9445/ or http://localhost:8000
* MinIO: http://localhost:9000 (minioadmin/minioadmin or you change it in the [Makefile](https://github.com/SUNET/drive-tests/blob/82e696b7b191cac2880fe87841331248ec5889e6/nextcloud-docker/Makefile#L169))
* Mock OAuth: https://localhost:9446 or http://localhost:8080


**Note:** If you want to make sure that you work in a clean environment, you can also run `make cleantestall`, which prunes your local docker deployment, including all volumes and images. You will get 5 seconds to cancel this operation.  **You have been warned!**

## Switch between ip/localhost and http/https
For some configurations Nextcloud seems to prefer either http/https and/or local IP/localhost. The following make commands switch between the different modes

    $ make nextcloud-http-ip
    $ make nextcloud-https-ip
    $ make nextcloud-http-localhost
    $ make nextcloud-https-localhost

This is just a convenience wrapper for overwrite.cli.url, overwritehost, and overwriteprotocol:

	$ ./occ_docker config:system:set overwrite.cli.url --value="http://$(LOCALIP):8080"
	$ ./occ_docker config:system:set overwritehost --value="$(LOCALIP):8080"
	$ ./occ_docker config:system:set overwriteprotocol --value="http"

## Restarting docker deployment
The local docker deployment currently requires to run within a project called rds. To stop/start everything, you can run:

    $ docker compose -p rds down
    $ docker compose -p rds up -d

## Configure OAuth for RDS-NG and JupyterHub
Unfortunately, Nextcloud does not currently allow scripted/automated OAuth configuration. If you think, this is a good idea, please upvote the the issue [here](https://github.com/nextcloud/server/issues/40645). Until then:

1. Switch to http with localhost: `make nextcloud-http-localhost`
1. Go to localhost:8080, login with admin/admin or register new admin account
1. Go to Settings/Security, add new OAUTH Clients (don't lose the Client Secret!).
    * RDS redirect URL: http://localhost:8080/apps/rdsng/main
    * Jupyter redirect URL: http://localhost:8100/hub/oauth_callback
1. Go to Administration Settings -> RDS NG, set RDS NG URL to http://localhost:8000
1. Go to Administration Settings -> Additional Settings, set Jupyterhub to http://localhost:8100
1. Add RDS_AUTHORIZATION_OAUTH2_CLIENT_ID to nextcloud-docker/rds-ng/deployment/env/dev.frontend.env
1. Add RDS_AUTHORIZATION_OAUTH2_SECRETS_HOST to nextcloud-docker/rds-ng/deployment/env/dev.server.env
1. (Jupyterhub config is tbd)
1. Restart deployment: `docker compose -p rds down && docker compose -p rds up -d`

## Docker compose and Makefile
With this local Nextcloud environment, you can execute most, if not all, automated tests that Sunet uses to test their Sunet Drive environment. The local deployment uses a (single-node) architecture that is as close to the Sunet Drive deployment as possible. The majority of the configuration is done in a `docker-compose.yaml` and a `Makefile`. The compose file contains configurations for:
* Nextcloud - [nextcloud:latest](https://hub.docker.com/_/nextcloud/) with a self-signed certificate
* MariaDB - [mariadb:latest](https://hub.docker.com/_/mariadb)
* MinIO - [minio:latest](https://quay.io/repository/minio/minio) with a configuration inspired by their [docker-compose example](https://github.com/minio/minio/blob/master/docs/orchestration/docker-compose/docker-compose.yaml)
* Whiteboard - []
* JupyterHub (WIP) - A locally built JupyterHub
* Mock OAuth Server (WIP) [mock-oauth2-server:2.1.1](https://ghcr.io/navikt/mock-oauth2-server)


