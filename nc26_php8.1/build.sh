#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc26_php8.1 .
#docker push binsky/passman-dev:nc26_php8.1
#docker push binsky/passman-dev:latest
rm entrypoint.sh
