#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc22_php8 .
docker push binsky/passman-dev:nc22_php8
rm entrypoint.sh
