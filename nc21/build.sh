#!/bin/bash

cp ../entrypoint.sh .
docker build -t binsky/passman-dev:nc21 .
docker push binsky/passman-dev:nc21
rm entrypoint.sh
