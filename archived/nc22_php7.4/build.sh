#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc22_php7.4 .
docker push binsky/passman-dev:nc22_php7.4
rm entrypoint.sh
