# SPDX-FileCopyrightText: Bernhard Posselt <dev@bernhard-posselt.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generic Makefile for building and packaging a Nextcloud app which uses npm and
# Composer.
#
# Dependencies:
# * make
# * which
# * curl: used if phpunit and composer are not installed to fetch them from the web
# * tar: for building the archive
# * npm: for building and testing everything JS
#
# If no composer.json is in the app root directory, the Composer step
# will be skipped. The same goes for the package.json which can be located in
# the app root or the js/ directory.
#
# The npm command by launches the npm build script:
#
#    npm run build
#
# The npm test command launches the npm test script:
#
#    npm run test
#
# The idea behind this is to be completely testing and build tool agnostic. All
# build tools and additional package managers should be installed locally in
# your project, since this won't pollute people's global namespace.
#
# The following npm scripts in your package.json install and update the bower
# and npm dependencies and use gulp as build system (notice how everything is
# run from the node_modules folder):
#
#    "scripts": {
#        "test": "node node_modules/gulp-cli/bin/gulp.js karma",
#        "prebuild": "npm install && node_modules/bower/bin/bower install && node_modules/bower/bin/bower update",
#        "build": "node node_modules/gulp-cli/bin/gulp.js"
#    },

# Global for all targets
# export NextcloudTestTarget=localhost
export NextcloudTestTarget=localhost
export NextcloudTestCustomers=localhost
export NextcloudTestRunner=html
export MFA_WAIT=3
export NEXTCLOUD_OCS_USER_LOCALHOST_LOCALHOST=_ocs_localhost
export NEXTCLOUD_OCS_PASSWORD_LOCALHOST_LOCALHOST=_ocs_localhost_password
export NEXTCLOUD_OCS_APP_PASSWORD_LOCALHOST_LOCALHOST=_ocs_localhost_app_password
export NEXTCLOUD_SELENIUM_USER_LOCALHOST_LOCALHOST=_selenium_localhost
export NEXTCLOUD_SELENIUM_PASSWORD_LOCALHOST_LOCALHOST=_selenium_localhost_password
export NEXTCLOUD_SELENIUM_APP_PASSWORD_LOCALHOST_LOCALHOST=
export NEXTCLOUD_SELENIUM_MFA_USER_LOCALHOST_LOCALHOST=_selenium_localhost_mfa
export NEXTCLOUD_SELENIUM_MFA_PASSWORD_LOCALHOST_LOCALHOST=_selenium_localhost_mfa_password
export NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_LOCALHOST_LOCALHOST=
export NEXTCLOUD_SELENIUM_MFA_SECRET_LOCALHOST_LOCALHOST=
LOCALIP = $(shell hostname -i | awk '{print $$1; exit}')
NEXTCLOUD_VERSION = $(shell yq '.localhost.status.version' ../expected_localhost.yaml -r)

all: docker
release: docker

.PHONY: docker_kill
docker_kill:
	docker kill nextcloud-local 2&> /dev/null || true
	docker kill nextcloud-local-db 2&> /dev/null || true
	docker kill nextcloud-local-whiteboard 2&> /dev/null || true
	docker kill nextcloud-local-nginx 2&> /dev/null || true
	docker kill nextcloud-local-minio1 2&> /dev/null || true
	docker kill nextcloud-local-minio2 2&> /dev/null || true
	docker kill nextcloud-local-minio3 2&> /dev/null || true
	docker kill nextcloud-local-minio4 2&> /dev/null || true

.PHONY: docker
docker: docker_kill
	docker compose -p nextcloudlocal -f docker-compose.yml build
	docker compose -p nextcloudlocal up -d
	sleep 15
	-./occ_docker maintenance:install --admin-user='admin' --admin-pass='adminpassword' --database='mysql' --database-name='nextcloud' --database-host='nextcloud-local-db' --database-user='nextcloud' --database-pass='userpass'

	./occ_docker config:system:set overwrite.cli.url --value="http://localhost:8080"
	./occ_docker config:system:set overwritehost --value="localhost:8080"
	./occ_docker config:system:set overwriteprotocol --value="http"

	./occ_docker config:system:set trusted_proxies --value="127.0.0.1,172.18.0.1,$(LOCALIP)"
	./occ_docker config:system:set trusted_domains 10 --value=localhost
	./occ_docker config:system:set trusted_domains 11 --value=127.0.0.1

	-./occ_docker app:install files_accesscontrol
	-./occ_docker app:install files_automatedtagging
	-./occ_docker app:install twofactor_webauthn
	-./occ_docker app:install richdocumentscode
	-./occ_docker app:install richdocuments
	./occ_docker config:app:set richdocuments wopi_allowlist --value="127.0.0.1,172.18.0.0/12"
	./occ_docker config:app:set richdocuments disable_certificate_verification --value="yes"
	./occ_docker config:app:set richdocuments wopi_url --value="http://collabora-server:9980"
	./occ_docker richdocuments:setup

	-./occ_docker app:install whiteboard
	-./occ_docker config:app:set whiteboard collabBackendUrl --value="http://localhost:3002"
	-./occ_docker config:app:set whiteboard jwt_secret_key --value="some-random-key"

	-./occ_docker config:app:set bruteForce whitelist_1 --value='$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.Gateway}}{{end}}' nextcloud-local)'

	./occ_docker  app:enable twofactor_totp
	./occ_docker  app:enable files_external
	./occ_docker  app:enable tasks
	./occ_docker  app:enable calendar
	./occ_docker  app:enable polls
	./occ_docker  app:enable forms
	./occ_docker  app:enable deck
	./occ_docker  app:disable firstrunwizard

	wget https://github.com/SUNET/nextcloud-jupyter/releases/download/v0.1.2/integration_jupyterhub-0.1.2.tar.gz
	docker cp integration_jupyterhub-0.1.2.tar.gz nextcloud-local:/var/www/html/custom_apps
	docker exec -u www-data nextcloud-local /bin/bash -c "cd /var/www/html/custom_apps && tar -xzf integration_jupyterhub-0.1.2.tar.gz && rm integration_jupyterhub-0.1.2.tar.gz"
	docker exec -u www-data nextcloud-local /bin/bash -c "sed -i -e 's/max-version=\"29\"/max-version=\"31\"/g' /var/www/html/custom_apps/integration_jupyterhub/appinfo/info.xml"

	docker exec nextcloud-local /bin/bash -c "chown -R www-data:www-data /var/www/html/custom_apps/integration_jupyterhub"
	rm integration_jupyterhub-0.1.2.tar.gz
	./occ_docker app:enable integration_jupyterhub
	./occ_docker config:app:set integration_jupyterhub jupyter_url --value="http://localhost:8100"

	-./occ_docker  group:add forcemfa
	-./occ_docker  twofactorauth:enforce --on --group forcemfa
	./occ_docker  group:adduser forcemfa admin
	-docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=mfauserpassword /var/www/html/occ user:add --password-from-env --display-name='MFA User' --group='mfa' mfauser"
	-docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=nomfauserpassword /var/www/html/occ user:add --password-from-env --display-name='Ordinary User' nomfauser"
	-docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=_ocs_localhost_password /var/www/html/occ user:add --password-from-env --display-name='MFA User' --group='admin' _ocs_localhost"
	-docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=_selenium_localhost_mfa_password /var/www/html/occ user:add --password-from-env --display-name='Selenium MFA User' --group='mfa' _selenium_localhost_mfa"
	-docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=_selenium_localhost_password /var/www/html/occ user:add --password-from-env --display-name='Selenium User' _selenium_localhost"
	-docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=mfauserpassword /var/www/html/occ user:add --password-from-env --display-name='MFA User' --group='mfa' mfauser"
	-docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=nomfauserpassword /var/www/html/occ user:add --password-from-env --display-name='Ordinary User' nomfauser"

	# -docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=$(NEXTCLOUD_OCS_APP_PASSWORD_LOCALHOST_LOCALHOST) /var/www/html/occ user:auth-tokens:add --password-from-env _ocs_localhost"
	# -docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=$(NEXTCLOUD_SELENIUM_APP_PASSWORD_LOCALHOST_LOCALHOST) /var/www/html/occ user:auth-tokens:add --password-from-env _selenium_localhost"
	# -docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=$(NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_LOCALHOST_LOCALHOST) /var/www/html/occ user:auth-tokens:add --password-from-env _selenium_localhost_mfa"

	# -docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=notimportant /var/www/html/occ user:auth-tokens:add --password-from-env _ocs_localhost"
	# -docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=notimportant /var/www/html/occ user:auth-tokens:add --password-from-env _selenium_localhost"
	# -docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=notimportant /var/www/html/occ user:auth-tokens:add --password-from-env _selenium_localhost_mfa"

	# docker exec nextcloud-local-minio1 mc config host add myminio http://nextcloud-local-minio:9000 minioadmin minioadmin
	docker exec nextcloud-local-minio1 mc alias set myminio http://nextcloud-local-minio:9000 minioadmin minioadmin
	-docker exec nextcloud-local-minio1 mc mb myminio/project-bucket
	-docker exec nextcloud-local-minio1 mc mb myminio/selenium-system
	-docker exec nextcloud-local-minio1 mc mb myminio/selenium-personal

	# Copy bucket configuration file to container and import mounts
	docker cp files_external.json nextcloud-local:/var/www/html
	-./occ_docker files_external:import files_external.json

	-firefox -new-tab https://localhost:8443/ -new-tab http://localhost:9001 -new-tab https://localhost:9443

.PHONY: commandtest
commandtest:
	docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=$(NEXTCLOUD_OCS_APP_PASSWORD_LOCALHOST_LOCALHOST) /var/www/html/occ user:auth-tokens:add --password-from-env _ocs_localhost"

.PHONY: expected
expected:
	cp -f ../expected_localhost_template.yaml ../expected_localhost.yaml
	python ../expected_localhost.py

.PHONY: jupyterhub
jupyterhub:
	cd jupyter-custom && docker build -t jupyterhub-local .

.PHONY: cleanall
cleanall: docker_kill
	-./cleanall.sh
	-rm .env
	-rm -rf /tmp/localhost*
	-rm -rf /tmp/nextcloud*
	-cd .. && rm expected_localhost.yaml

.PHONY: clean
clean:
	-./cleangentle.sh
	-rm .env
	-cd .. && rm expected_localhost.yaml

.PHONY: checkenv
checkenv:
	python ../environment_check.py ../requirements.txt -d

.PHONY: preparetest
preparetest: checkenv expected apppasswords

.PHONY: test
test: clean docker checkenv expected apppasswords acceptancetest

.PHONY: testall
testall: clean docker checkenv expected apppasswords acceptancetest logintest collaboratest

.PHONY: cleantest
cleantest: cleanall docker checkenv expected apppasswords acceptancetest

.PHONY: cleantestall
cleantestall: cleanall docker checkenv expected apppasswords acceptancetest logintest collaboratest

.PHONY: acceptancetest
acceptancetest:
	. ./.env; \
	cd ..; \
	python test_tests.py; \
	python test_status_cli.py; \
	python test_ocs.py; \
	python test_webdav.py
	-firefox ../test-reports-html/nextcloud-${NEXTCLOUD_VERSION}-acceptance.html

.PHONY: logintest
logintest:
	. ./.env; \
	cd ..; \
	python test_login_selenium.py
	-firefox ../test-reports-html/nextcloud-${NEXTCLOUD_VERSION}-selenium.html

.PHONY: collaboratest
collaboratest:
	. ./.env; \
	cd ..; \
	python test_collabora_selenium.py
	-firefox ../test-reports-html/nextcloud-${NEXTCLOUD_VERSION}-collabora.html

.PHONY: apppasswords
apppasswords:
	-rm .env
	export OCS_APP_PASSWORD=$(shell docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=whatever /var/www/html/occ user:auth-tokens:add --password-from-env _ocs_localhost" | sed -n '2 p'); \
	export SELENIUM_APP_PASSWORD=$(shell docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=whatever /var/www/html/occ user:auth-tokens:add --password-from-env _selenium_localhost" | sed -n '2 p'); \
	export SELENIUM_MFA_APP_PASSWORD=$(shell docker exec -u www-data nextcloud-local /bin/bash -c "env NC_PASS=whatever /var/www/html/occ user:auth-tokens:add --password-from-env _selenium_localhost_mfa" | sed -n '2 p'); \
	echo export NEXTCLOUD_OCS_APP_PASSWORD_LOCALHOST_LOCALHOST=$$OCS_APP_PASSWORD >> .env; \
	echo export NEXTCLOUD_SELENIUM_APP_PASSWORD_LOCALHOST_LOCALHOST=$$SELENIUM_APP_PASSWORD >> .env; \
	echo export NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_LOCALHOST_LOCALHOST=$$SELENIUM_MFA_APP_PASSWORD >> .env

.PHONY: nextcloud-http-ip
nextcloud-http-ip:
	./occ_docker config:system:set overwrite.cli.url --value="http://$(LOCALIP):8080"
	./occ_docker config:system:set overwritehost --value="$(LOCALIP):8080"
	./occ_docker config:system:set overwriteprotocol --value="http"

.PHONY: nextcloud-https-ip
nextcloud-https-ip:
	./occ_docker config:system:set overwrite.cli.url --value="https://$(LOCALIP):8443"
	./occ_docker config:system:set overwritehost --value="$(LOCALIP):8443"
	./occ_docker config:system:set overwriteprotocol --value="https"

.PHONY: nextcloud-http-localhost
nextcloud-http-localhost:
	./occ_docker config:system:set overwrite.cli.url --value="http://localhost:8080"
	./occ_docker config:system:set overwritehost --value="localhost:8080"
	./occ_docker config:system:set overwriteprotocol --value="http"

.PHONY: nextcloud-https-localhost
nextcloud-https-localhost:
	./occ_docker config:system:set overwrite.cli.url --value="https://localhost:8443"
	./occ_docker config:system:set overwritehost --value="localhost:8443"
	./occ_docker config:system:set overwriteprotocol --value="https"

.PHONY: nextcloud-http-localhost
nextcloud-http-nextcloud-local:
	./occ_docker config:system:set overwrite.cli.url --value="http://nextcloud-local"
	./occ_docker config:system:set overwritehost --value="nextcloud-local"
	./occ_docker config:system:set overwriteprotocol --value="http"

# To set environment variables in your local shell run:
# eval "$(make printenv)"
.PHONY: printenv
printenv:
	echo 'export NextcloudTestTarget="$(NextcloudTestTarget)"'
	echo 'export NextcloudTestCustomers="$(NextcloudTestCustomers)"'
	echo 'export NextcloudTestRunner="html"'
	echo 'export MFA_WAIT="$(MFA_WAIT)"'
	echo 'export NEXTCLOUD_OCS_USER_LOCALHOST_LOCALHOST="$(NEXTCLOUD_OCS_USER_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_OCS_PASSWORD_LOCALHOST_LOCALHOST="$(NEXTCLOUD_OCS_PASSWORD_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_OCS_APP_PASSWORD_LOCALHOST_LOCALHOST="$(NEXTCLOUD_OCS_APP_PASSWORD_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_SELENIUM_USER_LOCALHOST_LOCALHOST="$(NEXTCLOUD_SELENIUM_USER_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_SELENIUM_PASSWORD_LOCALHOST_LOCALHOST="$(NEXTCLOUD_SELENIUM_PASSWORD_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_SELENIUM_APP_PASSWORD_LOCALHOST_LOCALHOST="$(NEXTCLOUD_SELENIUM_APP_PASSWORD_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_SELENIUM_MFA_USER_LOCALHOST_LOCALHOST="$(NEXTCLOUD_SELENIUM_MFA_USER_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_SELENIUM_MFA_PASSWORD_LOCALHOST_LOCALHOST="$(NEXTCLOUD_SELENIUM_MFA_PASSWORD_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_LOCALHOST_LOCALHOST="$(NEXTCLOUD_SELENIUM_MFA_APP_PASSWORD_LOCALHOST_LOCALHOST)"'
	echo 'export NEXTCLOUD_SELENIUM_MFA_SECRET_LOCALHOST_LOCALHOST="$(NEXTCLOUD_SELENIUM_MFA_SECRET_LOCALHOST_LOCALHOST)"'
