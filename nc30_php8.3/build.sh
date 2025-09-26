#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc30_php8.3 .
#docker push binsky/passman-dev:nc30_php8.3
rm entrypoint.sh
