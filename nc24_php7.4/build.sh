#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc24_php7.4 .
docker push binsky/passman-dev:nc24_php7.4
rm entrypoint.sh
