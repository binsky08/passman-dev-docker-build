#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc30_php8.3 -t binsky/passman-dev:latest .
#docker push binsky/passman-dev:nc30_php8.3
#docker push binsky/passman-dev:latest
rm entrypoint.sh
