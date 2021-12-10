#!/bin/bash

docker build -f Dockerfile -t open5gs .
docker image prune --force
