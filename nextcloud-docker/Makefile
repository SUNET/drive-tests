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

cert_dir=$(HOME)/.nextcloud/certificates

all: docker
release: docker
.PHONY: selfsignedcert
selfsignedcert:
	test -f /tmp/localhost.crt || openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=localhost"  -keyout /tmp/localhost.key  -out /tmp/localhost.crt; \
	cat /tmp/localhost.key /tmp/localhost.crt > /tmp/localhost.pem

.PHONY: docker_kill
docker_kill:
	docker kill nextcloud-local 2&> /dev/null || true
	docker kill nextcloud-local-db 2&> /dev/null || true
	pushd $(CURDIR)/minio && docker-compose down
.PHONY: docker
docker: selfsignedcert docker_kill
	$(shell printf 'LoadModule socache_shmcb_module /usr/lib/apache2/modules/mod_socache_shmcb.so \nLoadModule ssl_module /usr/lib/apache2/modules/mod_ssl.so \nSSLRandomSeed startup builtin \nSSLRandomSeed startup file:/dev/urandom 512 \nSSLRandomSeed connect builtin \nSSLRandomSeed connect file:/dev/urandom 512 \nAddType application/x-x509-ca-cert .crt \nAddType application/x-pkcs7-crl .crl \nSSLPassPhraseDialog  exec:/usr/share/apache2/ask-for-passphrase \nSSLSessionCache     shmcb:$${APACHE_RUN_DIR}/ssl_scache(512000) \nSSLSessionCacheTimeout  300 \nSSLCipherSuite HIGH:!aNULL \nSSLProtocol all -SSLv3 \nSSLSessionTickets off' > /tmp/nextcloud-ssl.conf )
	$(shell printf 'Listen 8443 \n<VirtualHost *:8443> \nServerAdmin webmaster@localhost \nDocumentRoot /var/www/html \nSSLEngine on \nSSLCertificateFile /etc/ssl/private/localhost.pem \nSSLCertificateKeyFile /etc/ssl/private/localhost.pem \nHeader always set Strict-Transport-Security "max-age=0" \nErrorLog $${APACHE_LOG_DIR}/sslerror.log \nCustomLog $${APACHE_LOG_DIR}/sslaccess.log combined \n</VirtualHost>' > /tmp/nextcloud-8443.conf)
	docker-compose up -d
	sleep 10
	# docker cp $(build_dir)/$(app_name)-$(version).tar.gz nextcloud:/var/www/html/custom_apps
	# docker exec -u www-data nextcloud /bin/bash -c "cd /var/www/html/custom_apps && tar -xzf $(app_name)-$(version).tar.gz && rm $(app_name)-$(version).tar.gz"
	# docker exec nextcloud /bin/bash -c "chown -R www-data:www-data /var/www/html/custom_apps/$(app_name)"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ maintenance:install --admin-user='admin' --admin-pass='adminpassword'"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ app:install files_accesscontrol"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ app:install files_automatedtagging"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ app:install twofactor_webauthn"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ app:enable twofactor_totp"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ app:enable files_external"
	# docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ app:enable mfazones"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ group:add mfa"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ twofactorauth:enforce --on --group mfa"
	docker exec -u www-data nextcloud-local /bin/bash -c "/var/www/html/occ group:adduser mfa admin"
	docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=mfauserpassword /var/www/html/occ user:add --password-from-env --display-name='MFA User' --group='mfa' mfauser"
	docker exec -u www-data nextcloud-local /bin/bash -c "env OC_PASS=nomfauserpassword /var/www/html/occ user:add --password-from-env --display-name='Ordinary User' nomfauser"
	firefox -new-tab https://localhost:8443/

clean: docker_kill

# .PHONY: test
# test: composer
# 	$(project_dir)/vendor/phpunit/phpunit/phpunit -c $(project_dir)/phpunit.xml
# 	$(project_dir)/vendor/phpunit/phpunit/phpunit -c $(project_dir)/phpunit.integration.xml
