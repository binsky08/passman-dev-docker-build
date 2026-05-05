#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc33_php8.4 -t binsky/passman-dev:latest .
#docker push binsky/passman-dev:nc33_php8.4
#docker push binsky/passman-dev:latest
rm entrypoint.sh
