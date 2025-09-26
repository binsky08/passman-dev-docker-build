#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc31_php8.3 -t binsky/passman-dev:latest --no-cache .
#docker push binsky/passman-dev:nc31_php8.3
#docker push binsky/passman-dev:latest
rm entrypoint.sh
