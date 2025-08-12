import time
import requests
import os
import sys
from datetime import datetime
from oauthenticator.generic import GenericOAuthenticator

# import pprint
# import getpass
# env_var = os.environ
# print(f"User's Environment variable in nextcloud-oauth.py for user {getpass.getuser()} in {__file__}") 
# pprint.pprint(dict(env_var), width = 1) 

token_url = 'http://' + os.environ['NEXTCLOUD_HOST'] + '/index.php/apps/oauth2/api/v1/token'
debug = os.environ.get('NEXTCLOUD_DEBUG_OAUTH', 'false').lower() in ['true', '1', 'yes']
def get_nextcloud_access_token(refresh_token):
  client_id = os.environ['NEXTCLOUD_CLIENT_ID']
  client_secret = os.environ['NEXTCLOUD_CLIENT_SECRET']
  code = refresh_token
  data = {
    'grant_type': 'refresh_token',
    'code': code,
    'refresh_token': refresh_token,
    'client_id': client_id,
    'client_secret': client_secret
  }
  response = requests.post(token_url, data=data)
  if debug:
    print(response.text)
  return response.json()
def post_auth_hook(authenticator, handler, authentication):
  user = authentication['auth_state']['oauth_user']['ocs']['data']['id']
  auth_state = authentication['auth_state']
  auth_state['token_expires'] =  time.time() + auth_state['token_response']['expires_in']
  authentication['auth_state'] = auth_state
  return authentication
class NextcloudOAuthenticator(GenericOAuthenticator):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.user_dict = {}
  async def pre_spawn_start(self, user, spawner):
    super().pre_spawn_start(user, spawner)
    auth_state = await user.get_auth_state()
    if not auth_state:
      return
    access_token = auth_state['access_token']
    spawner.environment['NEXTCLOUD_ACCESS_TOKEN'] = access_token
  async def refresh_user(self, user, handler=None):
    auth_state = await user.get_auth_state()
    if not auth_state:
      if debug:
        print(f'auth_state missing for {user}')
      return False
    access_token = auth_state['access_token']
    refresh_token = auth_state['refresh_token']
    token_response = auth_state['token_response']
    now = time.time()
    now_hr = datetime.fromtimestamp(now)
    expires = auth_state['token_expires']
    expires_hr = datetime.fromtimestamp(expires)
    expires = 0
    if debug:
      print(f'auth_state for {user}: {auth_state}')
    if now >= expires:
      if debug:
        print(f'Time is: {now_hr}, token expired: {expires_hr}')
        print(f'Refreshing token for {user}')
      try:
        token_response = get_nextcloud_access_token(refresh_token)
        auth_state['access_token'] = token_response['access_token']
        auth_state['refresh_token'] = token_response['refresh_token']
        auth_state['token_expires'] = now + token_response['expires_in']
        auth_state['token_response'] = token_response
        if debug:
          print(f'Successfully refreshed token for {user.name}')
          print(f'auth_state for {user.name}: {auth_state}')
        return {'name': user.name, 'auth_state': auth_state}
      except Exception:
        if debug:
          print(f'Failed to refresh token for {user}')
        return False
      return False
    if debug:
      print(f'Time is: {now_hr}, token expires: {expires_hr}')
    return True
c.JupyterHub.authenticator_class = NextcloudOAuthenticator
c.NextcloudOAuthenticator.client_id = os.environ['NEXTCLOUD_CLIENT_ID']
c.NextcloudOAuthenticator.client_secret = os.environ['NEXTCLOUD_CLIENT_SECRET']
c.NextcloudOAuthenticator.login_service = 'Sunet Drive'
c.NextcloudOAuthenticator.username_claim = lambda r: r.get('ocs', {}).get('data', {}).get('id')
c.NextcloudOAuthenticator.userdata_url = 'http://' + os.environ['NEXTCLOUD_HOST'] + '/ocs/v2.php/cloud/user?format=json'
c.NextcloudOAuthenticator.authorize_url = 'http://' + os.environ['NEXTCLOUD_HOST'] + '/index.php/apps/oauth2/authorize'
c.NextcloudOAuthenticator.token_url = token_url
c.NextcloudOAuthenticator.oauth_callback_url = 'http://' + os.environ['JUPYTER_HOST'] + '/hub/oauth_callback'
c.NextcloudOAuthenticator.allow_all = True
c.NextcloudOAuthenticator.refresh_pre_spawn = True
c.NextcloudOAuthenticator.enable_auth_state = True
c.NextcloudOAuthenticator.auth_refresh_age = 3600
c.NextcloudOAuthenticator.post_auth_hook = post_auth_hook

# Configuration file for jupyter-notebook.

c = get_config()
c.NotebookApp.allow_origin = '*'
c.NotebookApp.tornado_settings = {
    'headers': { 'Content-Security-Policy': "frame-ancestors *;" }
}

c.JupyterHub.allow_origin = '*'
c.JupyterHub.tornado_settings = { 'headers': { 'Content-Security-Policy': "frame-ancestors *;" } }
c.JupyterHub.services = [
    {
        'name': 'refresh-token',
        'url': 'http://' + os.environ.get('HUB_SERVICE_HOST', 'hub') + ':' + os.environ.get('HUB_SERVICE_PORT_REFRESH_TOKEN', '8082'),
        'display': False,
        'oauth_no_confirm': True,
        'api_token': os.environ['JUPYTERHUB_API_KEY'],
        'command': [sys.executable, '/usr/local/etc/jupyterhub/refresh-token.py']
    },
    {
        'name': 'nextcloud-oauth',
        'url': 'http://127.0.0.1:8081',
        'command': [sys.executable, '/usr/local/etc/jupyterhub/nextcloud-oauth.py'],
    }
]

c.JupyterHub.load_roles = [
    {
        "name": "refresh-token",
        "services": [
        "refresh-token"
        ],
        "scopes": [
        "read:users",
        "admin:auth_state"
        ]
    },
    {
        "name": "user",
        "scopes": [
        "access:services!service=refresh-token",
        "read:services!service=refresh-token",
        "self",
        ],
    },
    {
        "name": "server",
        "scopes": [
        "access:services!service=refresh-token",
        "read:services!service=refresh-token",
        "inherit",
        ],
    }
]

### Dockerspawner config start - Migh use that in the future, right now we stick with LocalProcessSpawner
### Source: https://github.com/jupyterhub/jupyterhub-deploy-docker/blob/main/basic-example/jupyterhub_config.py
# Spawn single-user servers as Docker containers
  # c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

  # # Spawn containers from this image
  # c.DockerSpawner.image = os.environ["DOCKER_NOTEBOOK_IMAGE"]

  # # Connect containers to this Docker network
  # network_name = os.environ["DOCKER_NETWORK_NAME"]
  # c.DockerSpawner.use_internal_ip = True
  # c.DockerSpawner.network_name = network_name

  # # Explicitly set notebook directory because we'll be mounting a volume to it.
  # # Most `jupyter/docker-stacks` *-notebook images run the Notebook server as
  # # user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
  # # We follow the same convention.
  # notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
  # c.DockerSpawner.notebook_dir = notebook_dir

  # # Mount the real user's Docker volume on the host to the notebook user's
  # # notebook directory in the container
  # c.DockerSpawner.volumes = {"jupyterhub-user-{username}": notebook_dir}

  # # Remove containers once they are stopped
  # c.DockerSpawner.remove = True

  # # For debugging arguments passed to spawned containers
  # c.DockerSpawner.debug = True

  # # User containers will access hub by container name on the Docker network
  # c.JupyterHub.hub_ip = "nextcloud-local-jupyterhub"
  # c.JupyterHub.hub_port = 8100

  # # Persist hub data on volume mounted inside container
  # # c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"
  # # c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"

  # # Allow all signed-up users to login
  # c.Authenticator.allow_all = True

  # # Authenticate users with Native Authenticator - We have our own!
  # # c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"

  # # Allow anyone to sign-up without approval
  # c.NativeAuthenticator.open_signup = True

  # # Allowed admins
  # admin = os.environ.get("JUPYTERHUB_ADMIN")
  # if admin:
  #     c.Authenticator.admin_users = [admin]

### Dockerspawner config end ###

### We always use jovyan as the local user ###
# def default_user(spawner):
#     username = 'jovyan'
#     spawner.user.name = username
#     username = spawner.user.name
#     spawner.environment["GREETING"] = f"Hello {username}"
# c.Spawner.pre_spawn_hook = default_user

c.NativeAuthenticator.open_signup = True
c.JupyterHub.admin_users = {"refresh-token"}
c.JupyterHub.api_tokens = {
    os.environ['JUPYTERHUB_API_KEY']: "refresh-token",
}

c.Spawner.env_keep = ['PATH', 'PYTHONPATH', 'CONDA_ROOT', 'CONDA_DEFAULT_ENV', 'VIRTUAL_ENV', 'LANG', 'LC_ALL', 'JUPYTERHUB_SINGLEUSER_APP', 'NEXTCLOUD_HOST']
# DONE