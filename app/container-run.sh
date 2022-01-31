#!/bin/bash
set -ex

apt-get update && apt-get install -y --no-install-recommends python3 python3-pip zlib1g python3-setuptools zlibc gcc libgcc-*-dev libgmp-dev
pip3 install -r /app/requirements.txt
cd /app
python3 ./app.py -d /datastore

