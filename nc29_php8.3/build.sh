#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc29_php8.3 .
#docker push binsky/passman-dev:nc29_php8.3
#docker push binsky/passman-dev:latest
rm entrypoint.sh
