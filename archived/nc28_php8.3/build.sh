#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc28_php8.3 .
#docker push binsky/passman-dev:nc28_php8.3
rm entrypoint.sh
