#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc25_php8.0 .
#docker push binsky/passman-dev:nc25_php8.0
rm entrypoint.sh
