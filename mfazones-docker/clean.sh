#!/bin/bash
rm .env.yaml
docker exec -u www-data nextcloud /bin/bash -c "/var/www/html/occ twofactorauth:disable admin totp"
docker exec -u www-data nextcloud /bin/bash -c "/var/www/html/occ twofactorauth:disable mfauser totp"