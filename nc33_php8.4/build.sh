#!/usr/bin/env bash

SLUG="nc33_php8.4"

cp ../entrypoint.sh .
docker build --target demo -t binsky/passman-demo:${SLUG} .
docker build --target dev -t binsky/passman-dev:${SLUG} .
#docker push binsky/passman-demo:${SLUG} binsky/passman-dev:${SLUG}
rm entrypoint.sh
