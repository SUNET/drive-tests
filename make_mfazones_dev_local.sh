#!/bin/bash
export NextcloudTestTarget=localhost

mkdir -p screenshots
mkdir -p mfazones-docker/screenshots

if [ -d "mfazones" ] 
then
    echo "Directory mfazones exists."
    pushd mfazones
    git pull
    popd    
else
    echo "Error: Directory mfazones does not exists."
	git clone https://github.com/SUNET/nextcloud-mfazones.git mfazones
fi

pushd mfazones
make clean
make docker
popd

pushd mfazones-docker
export MFA_WAIT=1

./clean.sh
python init_selenium.py
python test_mfazones_dev.py