#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc27_php8.1 .
#docker push binsky/passman-dev:nc27_php8.1
rm entrypoint.sh
