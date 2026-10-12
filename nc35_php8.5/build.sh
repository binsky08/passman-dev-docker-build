#!/usr/bin/env bash

SLUG="nc35_php8.5"

cp ../entrypoint.sh ../demo-config.sh .
docker build --target demo -t binsky/passman-demo:${SLUG} .
docker build --target dev -t binsky/passman-dev:${SLUG} .
#docker push binsky/passman-demo:${SLUG} binsky/passman-dev:${SLUG}
rm entrypoint.sh demo-config.sh
