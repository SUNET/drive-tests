import sunetnextcloud
import requests
import json
import logging
import time
import sys

drv = sunetnextcloud.TestTarget()
ocsheaders = drv.ocsheaders
expectedResults = drv.expectedResults

exclude_mfa4all = ['lnu', 'su', 'scilifelab', 'kau']

logger = logging.getLogger("MFA4All-Logger")
logging.basicConfig(
    format="%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

all_autogroups = []

for fullnode in drv.allnodes:

    logger.info(f'Execute for {fullnode}')
    nodeuser = drv.get_ocsuser(fullnode)
    nodepwd = drv.get_ocsuserapppassword(fullnode)
    rawurl = drv.get_all_apps_url(fullnode)
    logger.info(rawurl)
    url = rawurl.replace("$USERNAME$", nodeuser)
    url = url.replace("$PASSWORD$", nodepwd)
    session = requests.Session()
    r = session.get(url, headers=ocsheaders)

    try:
        j = json.loads(r.text)
        apps = j["ocs"]["data"]["apps"]
    except Exception as error:
        logger.error(f"No or invalid JSON reply received from {fullnode}:{error}")

    if 'auto_groups' in apps:
        try:
            rawurl = drv.get_app_url(fullnode, 'auto_groups')
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
            r = session.get(url, headers=ocsheaders)
            j = json.loads(r.text)

            r = session.post(url, headers=ocsheaders)
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4))
        except Exception as error:
            logger.error(f"No or invalid JSON reply received from {fullnode}:{error}")
    else:
        logger.error(f'auto_groups NOT FOUND')

    if 'stepupauth' in apps:
        try:
            rawurl = drv.get_app_url(fullnode, 'stepupauth')
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)
            r = session.get(url, headers=ocsheaders)
            j = json.loads(r.text)

            r = session.post(url, headers=ocsheaders)
            j = json.loads(r.text)
            logger.info(json.dumps(j, indent=4))
        except Exception as error:
            logger.error(f"No or invalid JSON reply received from {fullnode}:{error}")
    else:
        logger.error(f'stepupauth NOT FOUND')

    logger.info(f'Get app config keys')
    try:
        app = 'auto_groups'
        # app = 'stepupauth'
        rawurl = drv.get_app_config_keys_url(fullnode, app)

        url = rawurl.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)
        r = session.get(url, headers=ocsheaders)
        j = json.loads(r.text)
        logger.info(json.dumps(j, indent=4))
    except Exception as error:
        logger.error(f"Error during configuration of  auto_groups on {fullnode}:{error}")


    logger.info(f'Get app config value')
    try:
        app = 'auto_groups'
        key = 'auto_groups'
        # app = 'stepupauth'
        rawurl = drv.get_app_config_value_url(fullnode, app, key)

        url = rawurl.replace("$USERNAME$", nodeuser)
        url = url.replace("$PASSWORD$", nodepwd)
        r = session.get(url, headers=ocsheaders)
        j = json.loads(r.text)
        logger.info(json.dumps(j, indent=4))
    except Exception as error:
        logger.error(f"Error getting configuration of  auto_groups on {fullnode}:{error}")

    if 'forcemfa' not in j['ocs']['data']['data'] and fullnode not in exclude_mfa4all:
        logger.info(f'Add forcemfa to {fullnode}')
        logger.info(f'Set app config value')
        # if drv.target == 'prod':
        #     logger.warning(f'Not setting forcemfa for prod!')
        #     sys.exit(0)

        try:
            app = 'auto_groups'
            key = 'auto_groups'
            # app = 'stepupauth'
            rawurl = drv.get_app_config_value_url(fullnode, app, key)
            url = rawurl.replace("$USERNAME$", nodeuser)
            url = url.replace("$PASSWORD$", nodepwd)

            headers = {
                "OCS-APIRequest": "true",
                "Content-Type": "application/json"
            }

            data = { "value": "[\"forcemfa\"]" }
            # data = { "value": "[\"forcemfa\", \"sunet-gemensamt\"]"}
            r = session.post(url, headers=headers, json=data)

            if r.status_code == 200:
                logger.info(f'Auto_groups updated')
            else:
                logger.error(f'Unable to update auto_groups: {r.status_code} - {r.text}')

            time.sleep(5)
            r = session.get(url, headers=ocsheaders)
            j = json.loads(r.text)
            all_autogroups.append({fullnode:j['ocs']['data']['data']})

        except Exception as error:
            logger.error(f"Error during configuration of  auto_groups on {fullnode}:{error}")
    else:
        logger.warning(f'Excluding {fullnode} from mfa4all')
        time.sleep(5)

logger.info(all_autogroups)
logger.info(f'Done!')
