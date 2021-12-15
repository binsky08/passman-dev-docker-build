#!/bin/bash

cp ../entrypoint.sh .
docker build --no-cache -t binsky/passman-dev:nc23_php7.4 .
docker push binsky/passman-dev:nc23_php7.4
rm entrypoint.sh
