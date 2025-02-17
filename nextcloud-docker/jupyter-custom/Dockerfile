FROM quay.io/jupyterhub/jupyterhub:latest 
USER root
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
  curl \
  r-cran-irkernel \
  jq \
  nextcloud-desktop-cmd \
  python3-pip

RUN python3 -m pip install --upgrade pip
RUN pip install oauthenticator
RUN pip install notebook
RUN pip install dockerspawner

# Create a non-root user
RUN adduser --disabled-password --gecos "Default Jupyter user" \
    --uid 1000 \
     jovyan

RUN adduser --disabled-password --gecos "Default Jupyter user" \
    --uid 1001 \
    admin

RUN adduser --disabled-password --gecos "Default Jupyter user" \
    --uid 1002 \
    jupytertest

COPY ./jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY ./NextcloudOAuthenticator.py /srv/jupyterhub/NextcloudOAuthenticator.py
COPY ./NextcloudServiceConfig.py /srv/jupyterhub/NextcloudServiceConfig.py
COPY ./nextcloud-oauth.py /usr/local/etc/jupyterhub/nextcloud-oauth.py
COPY ./refresh-token.py /usr/local/etc/jupyterhub/refresh-token.py
COPY ./nc-sync /usr/local/bin/

# RUN chown -R jovyan:jovyan /srv/jupyterhub/
RUN chown -R admin:admin /srv/jupyterhub/

## Might need this when we switch to DockerSpawner
# RUN groupadd docker
# RUN usermod -a -G docker jovyan

USER admin
# CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
CMD ["jupyterhub"]