#!/bin/bash

docker build --force-rm --no-cache -f ./Dockerfile -t ueransim .
docker image prune --force
