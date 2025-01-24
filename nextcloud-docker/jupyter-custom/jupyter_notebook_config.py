# Configuration file for jupyter-notebook.
import sys

c = get_config()
c.NotebookApp.allow_origin = '*'
c.NotebookApp.tornado_settings = {
    'headers': { 'Content-Security-Policy': "frame-ancestors *;" }
}

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


c.JupyterHub.admin_users = {"refresh-token"}
c.JupyterHub.api_tokens = {
    os.environ['JUPYTERHUB_API_KEY']: "refresh-token",
}