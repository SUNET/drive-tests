FROM jenkins/jnlp-agent-jdk11

USER root

ARG python_major_version=3.11
ARG python_full_version=3.11.6

# Pre-requisites for the extensions
RUN set -ex; \
  apt-get -q update > /dev/null && apt-get -q install -y \
\
  build-essential \
  wget \
  libreadline-gplv2-dev \
  libncursesw5-dev \
  libssl-dev \
  libsqlite3-dev \
  tk-dev \
  libgdbm-dev \
  libc6-dev \
  libbz2-dev \
  libffi-dev \
  zlib1g-dev \
  liblzma-dev \
#
  xvfb \
  fluxbox \
  python3 \
  scrot \
  python3-pip \
  > /dev/null

# Install newer python version
RUN wget https://www.python.org/ftp/python/${python_full_version}/Python-${python_full_version}.tgz -O /tmp/python.tgz \
  && cd /tmp && tar xf /tmp/python.tgz

RUN cd /tmp/Python-${python_full_version} && ./configure --enable-optimizations && make altinstall
RUN update-alternatives --install /usr/bin/python python /usr/local/bin/python${python_major_version} 1

RUN /usr/local/bin/python${python_major_version} -m pip install --upgrade pip
RUN update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip${python_major_version} 1

RUN python -V && pip -V

# Install pip packages required for testing
RUN wget https://raw.githubusercontent.com/SUNET/drive-tests/main/requirements.txt -O /tmp/requirements.txt \
  && cd /tmp && pip install -r requirements.txt 

RUN mkdir /var/lib/jenkins
