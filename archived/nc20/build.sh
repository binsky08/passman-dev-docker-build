#!/usr/bin/env bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc20 .
docker push binsky/passman-dev:nc20
rm entrypoint.sh
