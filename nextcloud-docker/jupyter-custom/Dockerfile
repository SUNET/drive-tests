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

# Create a non-root user
RUN adduser --disabled-password --gecos "Default Jupyter user" \
    --uid 1000 \
     jovyan

COPY ./jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
# COPY ./whoami-oauth.py /srv/jupyterhub/whoami-oauth.py
# COPY ./whoami.py /srv/jupyterhub/whoami.py
# COPY ./whoami.png /srv/jupyterhub/whoami.png

RUN chown -R jovyan:jovyan /srv/jupyterhub/
USER jovyan