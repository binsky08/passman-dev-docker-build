#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc27_php8.1 -t binsky/passman-dev:latest .
#docker push binsky/passman-dev:nc27_php8.1
#docker push binsky/passman-dev:latest
rm entrypoint.sh
