FROM quay.io/jupyter/scipy-notebook:lab-4.0.10  
USER root
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
  curl \
  r-cran-irkernel \
  jq \
  nextcloud-desktop-cmd \
  python3-pip
COPY ./nc-sync /usr/local/bin/
USER jovyan
