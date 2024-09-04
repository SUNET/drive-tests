import pyotp
import argparse
import os
import yaml
import logging
import sys

baseUrl='https://github.com/SUNET/nextcloud-mfazones/releases/download/v'

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S', level = logging.INFO)

envFile = '.env.yaml'

parser = argparse.ArgumentParser(description="Install specific release of MFA Zones app into local docker container",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('version', help="<version>")
args = parser.parse_args()
config = vars(args)

version = args.version
donwloadUrl=f'{baseUrl}{version}/mfazones-{version}.tar.gz'
tarBall=f'mfazones-{version}.tar.gz'
logger.info(f'Installing v{version} of MFA Zones app from {donwloadUrl}')

if os.path.exists(tarBall):
    logger.warning(f'Removing existing file {tarBall}')
    os.system(f'rm {tarBall}')

os.system(f'wget {donwloadUrl}')
os.system(f'docker exec -u www-data nextcloud /bin/bash -c "/var/www/html/occ app:disable mfazones"')
os.system(f'docker exec -u www-data nextcloud /bin/bash -c "/var/www/html/occ app:remove mfazones"')
os.system(f'docker cp {tarBall} nextcloud:/var/www/html/custom_apps')
os.system(f'docker exec -u www-data nextcloud /bin/bash -c "cd /var/www/html/custom_apps && tar -xzf {tarBall} && rm {tarBall}"')
os.system(f'docker exec nextcloud /bin/bash -c "chown -R www-data:www-data /var/www/html/custom_apps/mfazones"')
os.system(f'docker exec -u www-data nextcloud /bin/bash -c "/var/www/html/occ app:enable mfazones"')
os.system(f'rm {tarBall}')
